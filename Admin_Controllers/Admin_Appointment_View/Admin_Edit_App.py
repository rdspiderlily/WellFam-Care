from PyQt5.QtWidgets import (
    QDialog, QLineEdit, QPushButton, QDateEdit,
    QTimeEdit, QMessageBox, QTextEdit,
    QComboBox, QCheckBox, QGroupBox, QWidget
)
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDate, QTime, pyqtSignal
from datetime import datetime, time

from Database import connect_db

class ViewAppointmentDialog(QDialog):
    def __init__(self, app_id, parent=None):
        super().__init__(parent)
        uic.loadUi("wfui/view_edit_appointment.ui", self)
        self.setWindowTitle("Appointment Details")
        self.setWindowIcon(QIcon("wfpics/logo1.jpg"))

        self.app_id = app_id
        self.conn = connect_db()
        
        self.patient = self.findChild(QLineEdit, "lineEditSelectedPatient")
        self.queue_no = self.findChild(QLineEdit, "lineEditQueueNumber")
        self.date = self.findChild(QDateEdit, "dateEditAppDate")
        self.time = self.findChild(QTimeEdit, "timeEditAppTime")
        self.notes = self.findChild(QTextEdit, "textEditNote")
        self.appointment_status = self.findChild(QComboBox, "comboBoxAppStatus")
        self.attendant = self.findChild(QComboBox, "comboBoxAttendant")

        self.btn_edit = self.findChild(QPushButton, "btnEdit")
        if self.btn_edit:
            self.btn_edit.clicked.connect(self.enable_inputs)

        self.btn_save = self.findChild(QPushButton, "btnSave")
        if self.btn_save:
            self.btn_save.clicked.connect(self.save_appointment)
            self.btn_save.setDisabled(True)
            
        self.btn_cancel = self.findChild(QPushButton, "btnCancel")
        if self.btn_cancel:
            self.btn_cancel.clicked.connect(self.cancel_edit)
            self.btn_cancel.setDisabled(True)
        
        btn_trash = self.findChild(QPushButton, "btnTrash")
        if btn_trash:
            btn_trash.clicked.connect(self.appointment_trash)
        
        self.time.timeChanged.connect(self.on_time_changed)
        self.load_appointment_details()
        self.disable_inputs()

    def load_appointment_details(self):
        try:
            self.availed_checkboxes_patient = []
            self.availed_checkboxes_appointment = []
            cursor = self.conn.cursor()

            # Fetch appointment details
            cursor.execute("""
                SELECT a.PAT_ID, p.PAT_LNAME || ', ' || p.PAT_FNAME AS fullname,
                    a.STAFF_ID, s.STAFF_LNAME || ', ' || s.STAFF_FNAME AS staff_name, 
                    a.APP_DATE, a.APP_TIME, a.QUEUE_NUM, a.APP_NOTES,
                    a.APP_STATUS_ID, aps.APP_STATUS_NAME AS appoint_status
                FROM APPOINTMENT a
                JOIN PATIENT p ON a.PAT_ID = p.PAT_ID
                JOIN USER_STAFF s ON a.STAFF_ID = s.STAFF_ID
                JOIN APPOINTMENT_STATUS aps ON a.APP_STATUS_ID = aps.APP_STATUS_ID
                WHERE a.APP_ID = %s
            """, (self.app_id,))
            row = cursor.fetchone()
            if not row:
                QMessageBox.warning(self, "Warning", "Appointment not found.")
                self.reject()
                return

            self.pat_id = row[0]

            # Fill in patient details on the UI
            self.patient.setText(row[1])
            self.date.setDate(QDate.fromString(str(row[4]), "yyyy-MM-dd"))
            self.time.setTime(QTime.fromString(str(row[5]), "HH:mm:ss"))
            self.queue_no.setText(str(row[6]))
            self.notes.setPlainText(row[7])
            
            appStatus = self.appointment_status
            cursor.execute("""
                SELECT aps.APP_STATUS_ID, aps.APP_STATUS_NAME AS appoint_status
                FROM APPOINTMENT_STATUS aps
            """)
            status = cursor.fetchall()
            appStatus.clear()
            for appSid, appSname in status:
                appStatus.addItem(appSname, appSid)
            appStatus.setCurrentIndex(appStatus.findData(row[8])) # Set selected appointment status

            # Set the attendant (staff) options
            attendantCombo = self.attendant
            cursor.execute("""
                SELECT s.STAFF_ID, s.STAFF_LNAME || ', ' || s.STAFF_FNAME AS staff_name
                FROM USER_STAFF s
            """)
            attendants = cursor.fetchall()
            attendantCombo.clear()
            for id, name in attendants:
                attendantCombo.addItem(name, id)
            attendantCombo.setCurrentIndex(attendantCombo.findData(row[2]))  # Set selected attendant

            # Fetch services and subservices availed by the patient for the specific appointment
            cursor.execute("""
                SELECT s.SERV_NAME, st.SERV_TYPE_NAME
                FROM PATIENT_SERVICE ps
                JOIN SERVICE s ON s.SERV_ID = ps.SERV_ID
                LEFT JOIN PATIENT_SERVICE_TYPE pst ON pst.PS_ID = ps.PS_ID
                LEFT JOIN SERVICE_TYPE st ON st.SERV_TYPE_ID = pst.SERV_TYPE_ID
                WHERE ps.PAT_ID = %s AND ps.PS_ID IN (SELECT PS_ID FROM APPOINTMENT_SERVICE WHERE APP_ID = %s)
            """, (self.pat_id, self.app_id))
            services_availed = cursor.fetchall()

            # Define the mapping for checkboxes for services
            service_cb = {
                "Family Planning": "checkBoxFamPlan",
                "Maternal Care Package": "checkBoxMatCare",
                "Pap Smear": "checkBoxPS"
            }

            # Define the mapping for subservices checkboxes
            subservice_cb = {
                "Counseling": "checkBoxCounseling",
                "IUD": "checkBoxIUD",
                "Condom": "checkBoxCondom",
                "Injectable": "checkBoxInjectible",
                "Pills": "checkBoxPills",
                "Prenatal Care": "checkBoxPrenatal",
                "Labor Monitoring": "checkBoxLaborMonitoring",
                "NSD": "checkBoxNSD",
                "Postpartum Care": "checkBoxPostpartumCare",
                "Pap Smear": "checkBoxPapSmearService"
            }

            # Initialize all checkboxes as unchecked and disabled
            cb_names = list(service_cb.values()) + list(subservice_cb.values())
            for cb_name in cb_names:
                cb = self.findChild(QCheckBox, cb_name)
                if cb:
                    cb.setChecked(False)
                    cb.setEnabled(False)

            # Loop through services and mark the checkboxes accordingly
            for service, subservice in services_availed:
                # Check main service checkbox
                main_cb = service_cb.get(service)
                if main_cb:
                    main_cb_checkbox = self.findChild(QCheckBox, main_cb)
                    if main_cb_checkbox:
                        main_cb_checkbox.setChecked(True)
                        main_cb_checkbox.setEnabled(False)  # Disable checkbox to prevent editing
                        self.availed_checkboxes_patient.append(main_cb)

                # Check subservice checkbox if exists
                if subservice:
                    sub_cb = subservice_cb.get(subservice)
                    if sub_cb:
                        sub_cb_checkbox = self.findChild(QCheckBox, sub_cb)
                        if sub_cb_checkbox:
                            sub_cb_checkbox.setChecked(True)
                            sub_cb_checkbox.setEnabled(False)  # Disable checkbox to prevent editing
                            self.availed_checkboxes_patient.append(sub_cb)
                            
            appointment_service_cb = {
                "Family Planning": "groupBoxFamPlan",
                "Maternal Care Package": "groupBoxMatCare",
                "Pap Smear": "groupBoxPS"
            }

            appointment_subservice_cb = {
                "Counseling": "checkBoxFPCounseling",
                "IUD": "checkBoxFPIUD",
                "Condom": "checkBoxFPCondom",
                "Injectable": "checkBoxFPInjectible",
                "Pills": "checkBoxFPPills",
                "Prenatal Care": "checkBoxMCPrenatal",
                "Labor Monitoring": "checkBoxMCLaborMonitoring",
                "NSD": "checkBoxMCNSD",
                "Postpartum Care": "checkBoxMCPostpartum",
                "Pap Smear": "checkBoxPSPapSmearService"
            }

            # Reset all appointment checkboxes
            acb_names = list(appointment_service_cb.values()) + list(appointment_subservice_cb.values())
            for acb_name in acb_names:
                cb = self.findChild(QCheckBox, acb_name)
                if cb:
                    cb.setChecked(False)
                    cb.setEnabled(True)

            # Fetch scheduled services and subservices for the appointment
            cursor.execute("""
                SELECT s.SERV_NAME, st.SERV_TYPE_NAME
                FROM APPOINTMENT_SERVICE aps
                JOIN PATIENT_SERVICE ps ON ps.PS_ID = aps.PS_ID
                JOIN SERVICE s ON s.SERV_ID = ps.SERV_ID
                LEFT JOIN APPOINTMENT_SERVICE_TYPE ast ON aps.APS_ID = ast.APS_ID
                LEFT JOIN PATIENT_SERVICE_TYPE pst ON pst.PST_ID = ast.PST_ID
                LEFT JOIN SERVICE_TYPE st ON st.SERV_TYPE_ID = pst.SERV_TYPE_ID
                WHERE aps.APP_ID = %s
            """, (self.app_id,))
            appointment_services = cursor.fetchall()

            # Loop through appointment services and check appropriate checkboxes
            for service, subservice in appointment_services:
                main_cb = appointment_service_cb.get(service)
                if main_cb:
                    cb = self.findChild(QCheckBox, main_cb)
                    if cb:
                        cb.setChecked(True)
                        self.availed_checkboxes_appointment.append(main_cb)
                
                if subservice:
                    sub_cb = appointment_subservice_cb.get(subservice)
                    if sub_cb:
                        cb = self.findChild(QCheckBox, sub_cb)
                        if cb:
                            cb.setChecked(True)
                            self.availed_checkboxes_appointment.append(sub_cb)
            
            subservice_groupbox_map = {
                "checkBoxCounseling": "checkBoxFPCounseling",
                "checkBoxIUD": "checkBoxFPIUD",
                "checkBoxCondom": "checkBoxFPCondom",
                "checkBoxInjectible": "checkBoxFPInjectible",
                "checkBoxPills": "checkBoxFPPills",
                "checkBoxPrenatal": "checkBoxMCPrenatal",
                "checkBoxLaborMonitoring": "checkBoxMCLaborMonitoring",
                "checkBoxNSD": "checkBoxMCNSD",
                "checkBoxPostpartum": "checkBoxMCPostpartum",
                "checkBoxPapSmearService": "checkBoxPSPapSmearService"
            }

            for cb_name, gb_name in subservice_groupbox_map.items():
                cb = self.findChild(QCheckBox, cb_name)
                gb = self.findChild(QWidget, gb_name)
                if cb and gb:
                    gb.setVisible(cb.isChecked())
            
            if row[9] == "Completed":  # row[9] = appointment status name (appoint_status)
                self.disable_inputs()
                self.btn_edit = self.findChild(QPushButton, "btnEdit")
                if self.btn_edit:
                    self.btn_edit.setDisabled(True)
                if self.btn_save:
                    self.btn_save.setDisabled(True)
                if self.btn_cancel:
                    self.btn_cancel.setDisabled(True)
                self.notes.setReadOnly(True)
                self.date.setEnabled(False)
                self.time.setEnabled(False)
                self.appointment_status.setEnabled(False)
                self.attendant.setEnabled(False)
                self.completed_warning()

        except Exception as e:
            print(f"Error loading appointment details: {e}")
            QMessageBox.warning(self, "Error", f"An error occurred while loading appointment details: {e}")

    def completed_warning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Cannot Edit Appointment")
        msg.setText("This appointment is already completed and cannot be edited.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def disable_inputs(self):
        for widget in self.findChildren((QLineEdit, QDateEdit, QTimeEdit, QComboBox, QTextEdit, QCheckBox)):
            widget.setDisabled(True)

    def enable_inputs(self):  
        for widget in self.findChildren((QLineEdit, QDateEdit, QTimeEdit, QComboBox, QTextEdit)):
            widget.setDisabled(False)
        
        availed_patient = set(getattr(self, 'availed_checkboxes_patient', []))
        availed_appointment = set(getattr(self, 'availed_checkboxes_appointment', [])) 
        for cb in self.findChildren(QCheckBox):
            cb_name = cb.objectName()

            if cb_name in availed_patient:
                cb.setDisabled(True)

            if cb_name in availed_appointment:
                cb.setDisabled(True)
            
        # Queue and patient name remain read-only
        self.queue_no.setDisabled(True)
        self.patient.setDisabled(True)
        
        if self.btn_save:
            self.btn_save.setEnabled(True)
        if self.btn_cancel:
            self.btn_cancel.setEnabled(True)

    def save_appointment(self):
        try:
            cursor = self.conn.cursor()
            new_date = self.date.date().toString("yyyy-MM-dd")
            new_time = self.time.time().toString("HH:mm:ss")
            new_notes = self.notes.toPlainText()
            new_staff_id = self.attendant.currentData()
            new_status_id = self.appointment_status.currentData()
            
            queue_number = self.generate_queue_number(new_date, new_time)

            # Update appointment query
            cursor.execute("""
                UPDATE APPOINTMENT
                SET APP_DATE = %s, APP_TIME = %s, STAFF_ID = %s, APP_NOTES = %s, APP_STATUS_ID = %s, QUEUE_NUM = %s
                WHERE APP_ID = %s
            """, (new_date, new_time, new_staff_id, new_notes, new_status_id, queue_number, self.app_id))

            self.conn.commit()
            QMessageBox.information(self, "Success", "Appointment updated successfully.")
            self.accept()
            self.load_appointment_details()

        except Exception as e:
            self.conn.rollback()
            print(self, "Error", f"Failed to save appointment: {e}")
            
    def generate_queue_number(self, new_date, new_time):
        try:
            cursor = self.conn.cursor()

            if isinstance(new_time, str):
                new_time_obj = datetime.strptime(new_time, "%H:%M:%S").time()
            else:
                new_time_obj = new_time.toPyTime() if hasattr(new_time, 'toPyTime') else new_time

            cursor.execute("""
                SELECT APP_ID
                FROM APPOINTMENT
                WHERE APP_DATE = %s AND APP_TIME = %s AND APP_ISDELETED = FALSE AND APP_ID != %s
            """, (new_date, new_time_obj, self.app_id))
            
            if cursor.fetchone():
                QMessageBox.warning(self, "Time Conflict", "There is already an appointment scheduled at this time.")
                return None

            cursor.execute("""
                SELECT APP_ID, APP_TIME
                FROM APPOINTMENT
                WHERE APP_DATE = %s AND APP_ISDELETED = FALSE AND APP_ID != %s
                ORDER BY APP_TIME ASC
            """, (new_date, self.app_id))

            appointments = cursor.fetchall()

            new_queue = 1
            for i, (app_id, app_time) in enumerate(appointments):
                if new_time_obj > app_time:
                    new_queue = i + 2
                else:
                    break

            cursor.execute("""
                UPDATE APPOINTMENT
                SET queue_num = queue_num + 1
                WHERE APP_DATE = %s AND APP_ISDELETED = FALSE AND APP_ID != %s AND APP_TIME >= %s
            """, (new_date, self.app_id, new_time_obj))

            cursor.execute("""
                UPDATE APPOINTMENT
                SET queue_num = %s
                WHERE APP_ID = %s
            """, (new_queue, self.app_id))

            self.conn.commit()
            return new_queue

        except Exception as e:
            print(f"Error generating new queue number: {e}")
            return 1
    
    def on_time_changed(self):
        new_time = self.time.time().toString("HH:mm:ss")
        new_date = self.date.date().toString("yyyy-MM-dd")

        # Generate the new queue number based on the new time
        new_queue_number = self.generate_queue_number(new_date, new_time)
        if new_queue_number:
            self.queue_no.setText(str(new_queue_number))
        else:
            self.queue_no.clear()  # If there was an issue with generating the queue number, clear it

        
    def cancel_edit(self):
        reply = QMessageBox.question(
            self,
            "Cancel Editing",
            "Are you sure you want to discard any changes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.load_appointment_details()
            self.disable_inputs()
    
    def appointment_trash(self):
        reply = QMessageBox.question(
            self,
            "Move to Trash",
            "Are you sure you want to move this appointment to trash?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            conn = connect_db()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("UPDATE APPOINTMENT SET APP_ISDELETED = TRUE WHERE APP_ID = %s", (self.app_id,))
                    conn.commit()

                    QMessageBox.information(self, "Deleted", "Appointment has been moved to trash successfully.")
                    self.appointment_updated.emit()
                    self.accept()
                    self.window().close()

                except Exception as e:
                    conn.rollback()
                    QMessageBox.critical(self, "Error", f"Failed to move appointment to trash: {e}")
                finally:
                    conn.close()
                    
    appointment_updated = pyqtSignal()