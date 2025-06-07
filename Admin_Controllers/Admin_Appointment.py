from PyQt5.QtWidgets import (
    QComboBox, QDialog, QMessageBox, QPushButton,
    QWidget, QDateEdit, QLineEdit, QTableWidget, QTextEdit,
    QHeaderView, QTableWidgetItem, QTimeEdit, QCheckBox
)
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from datetime import date

from Database import connect_db
from Database import log_audit
from Admin_Controllers.Admin_Appointment_View.Admin_Edit_App import ViewAppointmentDialog

class AdminAppointmentController:
    def __init__(self, tableWidApp: QTableWidget, searchApp: QLineEdit, sortAppCombo: QComboBox, user_id):
        self.conn = connect_db()
        self.tableWidApp = tableWidApp
        self.user_id = user_id
        
        self.update_appointment_statuses()
        self.appointment_list()
        
        try:
            self.tableWidApp.cellClicked.disconnect()
        except TypeError:
            pass
        
        self.tableWidApp.cellClicked.connect(self.view_appointment)
        
        self.searchApp = searchApp
        self.searchApp.textChanged.connect(self.search_appointment)
        
        self.sortAppCombo = sortAppCombo
        self.sortAppCombo.currentTextChanged.connect(self.sort_appointment_list)
    
    def update_appointment_statuses(self):
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                UPDATE APPOINTMENT
                SET APP_STATUS_ID = 2
                WHERE QUEUE_STATUS_ID = 3
                AND APP_STATUS_ID != 2
                AND APP_ISDELETED = FALSE
            """)

            today = date.today()
            cursor.execute("""
                UPDATE APPOINTMENT
                SET APP_STATUS_ID = 4
                WHERE APP_DATE < %s
                AND QUEUE_STATUS_ID = 1
                AND APP_STATUS_ID != 4
                AND APP_ISDELETED = FALSE
            """, (today,))
            
            self.conn.commit()
                        
        except Exception as e:
            self.conn.rollback()
            print(f"Error updating appointment statuses: {e}")
            
    def search_appointment(self, text):
        for row in range(self.tableWidApp.rowCount()):
            match = False
            for col in range(1, self.tableWidApp.columnCount()):
                item = self.tableWidApp.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.tableWidApp.setRowHidden(row, not match)
            
    def sort_appointment_list(self, sort_option):
        self.sortAppCombo.setCurrentIndex(0)
        
        if sort_option == "Date (Ascending)":
            sort_clause = "A.APP_DATE ASC, A.APP_TIME ASC"
        elif sort_option == "Date (Descending)":
            sort_clause = "A.APP_DATE DESC, A.APP_TIME DESC"
        elif sort_option == "Time (Ascending)":
            sort_clause = "A.APP_TIME ASC"
        elif sort_option == "Time (Descending)":
            sort_clause = "A.APP_TIME DESC"
        elif sort_option == "Patient Name (A-Z)":
            sort_clause = "P.PAT_LNAME ASC, P.PAT_FNAME ASC"
        elif sort_option == "Patient Name (Z-A)":
            sort_clause = "P.PAT_LNAME DESC, P.PAT_FNAME DESC"
        elif sort_option == "Service Availed (A-Z)":
            sort_clause = "S.SERV_NAME ASC"
        elif sort_option == "Appointment Type (A-Z)":
            sort_clause = "ST.SERV_TYPE_NAME ASC"
        elif sort_option == "Attendant (A-Z)":
            sort_clause = "U.STAFF_LNAME ASC, U.STAFF_FNAME ASC"
        elif sort_option == "Status":
            sort_clause = "AS1.APP_STATUS_NAME ASC"
        else:
            sort_clause = "A.APP_DATE ASC, A.APP_TIME ASC"

        try:
            self.tableWidApp.setRowCount(0)
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT 
                    A.APP_ID, A.APP_DATE, 
                    TO_CHAR(A.APP_TIME, 'HH12:MI AM') AS APP_TIME,
                    CONCAT(P.PAT_LNAME, ', ', P.PAT_FNAME) AS PATIENT_NAME,
                    S.SERV_NAME AS SERVICE_AVAILED,
                    ST.SERV_TYPE_NAME AS APPOINTMENT_TYPE,
                    CONCAT(U.STAFF_LNAME, ', ', U.STAFF_FNAME) AS ATTENDANT,
                    AS1.APP_STATUS_NAME AS STATUS
                FROM APPOINTMENT A
                JOIN PATIENT P ON A.PAT_ID = P.PAT_ID
                JOIN APPOINTMENT_SERVICE APS ON A.APP_ID = APS.APP_ID
                JOIN PATIENT_SERVICE PS ON APS.PS_ID = PS.PS_ID
                JOIN SERVICE S ON PS.SERV_ID = S.SERV_ID
                JOIN APPOINTMENT_SERVICE_TYPE AST ON APS.APS_ID = AST.APS_ID
                JOIN PATIENT_SERVICE_TYPE PST ON AST.PST_ID = PST.PST_ID
                JOIN SERVICE_TYPE ST ON PST.SERV_TYPE_ID = ST.SERV_TYPE_ID
                JOIN USER_STAFF U ON A.STAFF_ID = U.STAFF_ID
                JOIN APPOINTMENT_STATUS AS1 ON A.APP_STATUS_ID = AS1.APP_STATUS_ID
                WHERE A.APP_ISDELETED = FALSE
                AND P.PAT_ISDELETED = FALSE
                ORDER BY {sort_clause}
            """)
            rows = cursor.fetchall()

            for row in rows:
                row_position = self.tableWidApp.rowCount()
                self.tableWidApp.insertRow(row_position)
                for column, data in enumerate(row):
                    self.tableWidApp.setItem(row_position, column, QTableWidgetItem(str(data)))

        except Exception as e:
            QMessageBox.critical(self.tableWidApp, "Database Error", f"Error sorting data: {e}")

    def appointment_list(self):
        self.tableWidApp.setRowCount(0)
        
        header = self.tableWidApp.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [0, 100, 100, 250, 150, 150, 130, 88]
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)

        self.tableWidApp.setColumnHidden(0, True)
        self.tableWidApp.verticalHeader().setVisible(False)
                
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    A.APP_ID, A.APP_DATE, 
                    TO_CHAR(A.APP_TIME, 'HH12:MI AM') AS APP_TIME,
                    CONCAT(P.PAT_LNAME, ', ', P.PAT_FNAME) AS PATIENT_NAME,
                    S.SERV_NAME AS SERVICE_AVAILED,
                    ST.SERV_TYPE_NAME AS APPOINTMENT_TYPE,
                    CONCAT(U.STAFF_LNAME, ', ', U.STAFF_FNAME) AS ATTENDANT,
                    AS1.APP_STATUS_NAME AS STATUS
                FROM APPOINTMENT A
                JOIN PATIENT P ON A.PAT_ID = P.PAT_ID
                JOIN APPOINTMENT_SERVICE APS ON A.APP_ID = APS.APP_ID
                JOIN PATIENT_SERVICE PS ON APS.PS_ID = PS.PS_ID
                JOIN SERVICE S ON PS.SERV_ID = S.SERV_ID
                JOIN APPOINTMENT_SERVICE_TYPE AST ON APS.APS_ID = AST.APS_ID
                JOIN PATIENT_SERVICE_TYPE PST ON AST.PST_ID = PST.PST_ID
                JOIN SERVICE_TYPE ST ON PST.SERV_TYPE_ID = ST.SERV_TYPE_ID
                JOIN USER_STAFF U ON A.STAFF_ID = U.STAFF_ID
                JOIN APPOINTMENT_STATUS AS1 ON A.APP_STATUS_ID = AS1.APP_STATUS_ID
                WHERE A.APP_ISDELETED = FALSE
                AND P.PAT_ISDELETED = FALSE
                ORDER BY A.APP_DATE ASC, A.APP_TIME ASC
            """)
            rows = cursor.fetchall()

            existing_ids = [self.tableWidApp.item(row, 0).text() for row in range(self.tableWidApp.rowCount())]

            for row in rows:
                if row[0] not in existing_ids:
                    row_position = self.tableWidApp.rowCount()
                    self.tableWidApp.insertRow(row_position)
                    for column, data in enumerate(row):
                        self.tableWidApp.setItem(row_position, column, QTableWidgetItem(str(data)))

        except Exception as e:
            QMessageBox.critical(self.tableWidApp, "Database Error", f"Error fetching updated data: {e}")

    def add_appointment_dialog(self):
        if hasattr(self, 'dialog') and self.dialog is not None:
            if self.dialog.isVisible():
                self.dialog.raise_()
                self.dialog.activateWindow()
                return
        else:
            self.dialog = QDialog()
            self.dialog.setAttribute(Qt.WA_DeleteOnClose)
            self.dialog.destroyed.connect(lambda: setattr(self, 'dialog', None))
            
            uic.loadUi("wfui/add_appointment.ui", self.dialog)
            self.dialog.setWindowTitle("Add New Appointment")
            self.dialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))
            
            addAppWidget = self.dialog.findChild(QWidget, "widgetAddApp")
            if not addAppWidget:
                print("ERROR: widgetAddApp not found!")
            
            select_patient = self.dialog.findChild(QPushButton, "btnSearchPatient")
            if select_patient:
                select_patient.clicked.connect(lambda: self.open_select_patient_dialog(addAppWidget))
            
            comboAttendant = addAppWidget.findChild(QComboBox, "comboBoxAttendant")
            if comboAttendant:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("""
                        SELECT STAFF_ID, STAFF_LNAME || ', ' || STAFF_FNAME
                        FROM USER_STAFF us
                        JOIN USER_ROLE r ON us.ROLE_ID = r.ROLE_ID
                        WHERE r.ROLE_NAME IN ('Midwife', 'Nursing Aide') AND us.STAFF_ISDELETED = FALSE
                    """)
                    staff_list = cursor.fetchall()
                    comboAttendant.clear()
                    comboAttendant.addItem("-- Select Attendant --", -1)
                    for staff_id, name in staff_list:
                        comboAttendant.addItem(name, staff_id)
                except Exception as e:
                    QMessageBox.warning(self.dialog, "Warning", f"Failed to load staff: {e}")

            dateEdit = addAppWidget.findChild(QDateEdit, "dateEditAppDate")
            timeEdit = addAppWidget.findChild(QTimeEdit, "timeEditAppTime")
            queueNoEdit = addAppWidget.findChild(QLineEdit, "lineEditQueueNumber")
            if queueNoEdit:
                queueNoEdit.setReadOnly(True)

            def generate_queue_number():
                if not dateEdit or not timeEdit:
                    return

                selected_date = dateEdit.date().toPyDate()
                selected_time = timeEdit.time().toPyTime()

                try:
                    cursor = self.conn.cursor()

                    # Check if the selected time slot is already taken
                    cursor.execute("""
                        SELECT APP_ID
                        FROM APPOINTMENT
                        WHERE APP_DATE = %s AND APP_TIME = %s AND APP_ISDELETED = FALSE
                    """, (selected_date, selected_time))

                    if cursor.fetchone():
                        QMessageBox.warning(self.dialog, "Time Conflict", "There is already an appointment scheduled at this time.")
                        queueNoEdit.clear()
                        return

                    # Get all appointments for that day, ordered by time
                    cursor.execute("""
                        SELECT APP_TIME
                        FROM APPOINTMENT
                        WHERE APP_DATE = %s AND APP_ISDELETED = FALSE
                        ORDER BY APP_TIME ASC
                    """, (selected_date,))
                    appointments = cursor.fetchall()

                    # Determine queue number based on where the time fits
                    new_queue = 1
                    for i, (appt_time,) in enumerate(appointments):
                        if selected_time > appt_time:
                            new_queue = i + 2
                        else:
                            break

                    queueNoEdit.setText(str(new_queue).zfill(3))

                except Exception as e:
                    print(f"Error generating queue number: {e}")
                    queueNoEdit.setText("001")

            if dateEdit and timeEdit:
                dateEdit.dateChanged.connect(generate_queue_number)
                timeEdit.timeChanged.connect(generate_queue_number)
                    
            save_button = self.dialog.findChild(QPushButton, "pushBtnSaveApp")
            if save_button:
                save_button.clicked.connect(lambda: self.save_appointment(addAppWidget, self.dialog))
            
            cancel_button = self.dialog.findChild(QPushButton, "pushBtnCancelApp")
            if cancel_button:
                cancel_button.clicked.connect(self.dialog.reject)
            
        self.dialog.exec_()
    
    def open_select_patient_dialog(self, addAppWidget):
        patLDialog = QDialog()
        uic.loadUi("wfui/patientList_appointment.ui", patLDialog)
        patLDialog.setWindowTitle("Select Patient")
        patLDialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))

        selectPatAWidget = patLDialog.findChild(QWidget, "widgetPatListApp")
        tableWidPatA = selectPatAWidget.findChild(QTableWidget, "tableWidgetPatApp")
        searchPatApp = selectPatAWidget.findChild(QLineEdit, "lineEditSearchPatApp")

        header = tableWidPatA.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [0, 250, 250, 300]
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)

        tableWidPatA.setColumnHidden(0, True)
        tableWidPatA.verticalHeader().setVisible(False)

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT PAT_ID, PAT_LNAME, PAT_FNAME, (
                SELECT STRING_AGG(SERV_NAME, ', ')
                FROM PATIENT_SERVICE ps
                JOIN SERVICE s ON s.SERV_ID = ps.SERV_ID
                WHERE ps.PAT_ID = p.PAT_ID
            ) AS services
            FROM PATIENT p
            WHERE PAT_ISDELETED = FALSE
        """)
        patients = cursor.fetchall()
        tableWidPatA.setRowCount(len(patients))
        for row_idx, row_data in enumerate(patients):
            for col_idx, value in enumerate(row_data):
                tableWidPatA.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        def handle_patient_selection(row, _):
            try:
                if not tableWidPatA.item(row, 0):
                    return
                
                pat_id = tableWidPatA.item(row, 0).text()
                pat_fname = tableWidPatA.item(row, 2).text()
                pat_lname = tableWidPatA.item(row, 1).text()
                
                if not pat_id or not pat_fname or not pat_lname:
                    QMessageBox.warning(patLDialog, "Selection Error", "Incomplete patient info.")
                    return

                name_display = f"{pat_lname}, {pat_fname}"
                pat_name = addAppWidget.findChild(QLineEdit, "lineEditSelectedPatient")
                if pat_name:
                    pat_name.setText(name_display)
                    pat_name.setReadOnly(True)
                    addAppWidget.selected_patient_id = int(pat_id)
            
                service_cb = {
                    "Family Planning": "checkBoxFamPlan",
                    "Maternal Care Package": "checkBoxMatCare",
                    "Pap Smear": "checkBoxPS"
                }

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
                
                cb_names = list(service_cb.values()) + list(subservice_cb.values())
                for cb_name in cb_names:
                    cb = addAppWidget.findChild(QCheckBox, cb_name)
                    if cb:
                        cb.setChecked(False)
                        cb.setEnabled(False)

                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT s.SERV_NAME, st.SERV_TYPE_NAME
                    FROM PATIENT_SERVICE ps
                    JOIN SERVICE s ON s.SERV_ID = ps.SERV_ID
                    LEFT JOIN PATIENT_SERVICE_TYPE pst ON pst.PS_ID = ps.PS_ID
                    LEFT JOIN SERVICE_TYPE st ON st.SERV_TYPE_ID = pst.SERV_TYPE_ID
                    WHERE ps.PAT_ID = %s
                """, (pat_id,))
                services_availed = cursor.fetchall()

                for service, subservice in services_availed:
                    main_cb = service_cb.get(service)
                    if main_cb:
                        main_cb = addAppWidget.findChild(QCheckBox, main_cb)
                        if main_cb:
                            main_cb.setChecked(True)
                            main_cb.setEnabled(False)

                    if subservice:
                        sub_cb = subservice_cb.get(subservice)
                        if sub_cb:
                            sub_cb = addAppWidget.findChild(QCheckBox, sub_cb)
                            if sub_cb:
                                sub_cb.setChecked(True)
                                sub_cb.setEnabled(False)
                
                service_map = {
                    "checkBoxFamPlan": "groupBoxFamPlan",
                    "checkBoxMatCare": "groupBoxMatCare",
                    "checkBoxPS": "groupBoxPS"
                }
                for service_checkbox, groupbox_name in service_map.items():
                    checkbox = addAppWidget.findChild(QCheckBox, service_checkbox)
                    groupbox = addAppWidget.findChild(QWidget, groupbox_name)
                    if checkbox and groupbox:
                        if checkbox.isChecked():
                            groupbox.setVisible(True)
                        else:
                            groupbox.setVisible(False)
                            
                subservice_groupbox_map = {
                    "checkBoxCounseling": "checkBoxFPCounseling",
                    "checkBoxIUD": "checkBoxFPIUD",
                    "checkBoxCondom": "checkBoxFPCondom",
                    "checkBoxInjectible": "checkBoxFPInjectible",
                    "checkBoxPills": "checkBoxFPPills",
                    "checkBoxPrenatal": "checkBoxMCPrenatal",
                    "checkBoxLaborMonitoring": "checkBoxMCLaborMonitoring",
                    "checkBoxNSD": "checkBoxMCNSD",
                    "checkBoxPostpartumCare": "checkBoxMCPostpartum",
                    "checkBoxPapSmearService": "checkBoxPSPapSmearService"
                }
                
                for subservice_checkbox, subservice_groupbox in subservice_groupbox_map.items():
                    subservice_checkbox_elem = addAppWidget.findChild(QCheckBox, subservice_checkbox)
                    subservice_groupbox_elem = addAppWidget.findChild(QWidget, subservice_groupbox)
                    if subservice_checkbox_elem and subservice_groupbox_elem:
                        if subservice_checkbox_elem.isChecked():
                            subservice_groupbox_elem.setVisible(True)
                        else:
                            subservice_groupbox_elem.setVisible(False)
            
                patLDialog.accept()
            except Exception as e:
                QMessageBox.critical(patLDialog, "Error", f"An error occurred while selecting a patient:\n{e}")
        
        def search_patient_selection(text):
            for row in range(tableWidPatA.rowCount()):
                match = False
                for col in range(1, tableWidPatA.columnCount()):
                    item = tableWidPatA.item(row, col)
                    if item and text.lower() in item.text().lower():
                        match = True
                        break
                tableWidPatA.setRowHidden(row, not match)
        
        searchPatApp.textChanged.connect(search_patient_selection)
        tableWidPatA.cellClicked.connect(handle_patient_selection)
        patLDialog.exec_()
        
    def save_appointment(self, addAppWidget, dialog):
        try:
            patient_id = getattr(addAppWidget, "selected_patient_id", None)
            if not patient_id:
                QMessageBox.warning(dialog, "Warning", "Please select a patient.")
                return

            dateEdit = addAppWidget.findChild(QDateEdit, "dateEditAppDate")
            timeEdit = addAppWidget.findChild(QTimeEdit, "timeEditAppTime")
            attendantCombo = addAppWidget.findChild(QComboBox, "comboBoxAttendant")
            queueNoEdit = addAppWidget.findChild(QLineEdit, "lineEditQueueNumber")
            notesEdit = addAppWidget.findChild(QTextEdit, "textEditAppNotes")

            if not dateEdit or not timeEdit or not attendantCombo or not queueNoEdit:
                QMessageBox.warning(dialog, "Warning", "Some required fields are missing.")
                return

            app_date = dateEdit.date().toString("yyyy-MM-dd")
            app_time = timeEdit.time().toString("HH:mm:ss")
            queue_number = queueNoEdit.text()
            staff_index = attendantCombo.currentIndex()
            staff_id = attendantCombo.itemData(staff_index)
            
            if staff_id == -1:
                QMessageBox.warning(dialog, "Warning", "Please select an attendant.")
                return
            
            app_notes = notesEdit.toPlainText() if notesEdit else ""

            cursor = self.conn.cursor()

            # Default status (e.g., 1 = Scheduled)
            default_status_id = 1

            cursor.execute(""" 
                INSERT INTO APPOINTMENT (PAT_ID, STAFF_ID, APP_DATE, APP_TIME, APP_STATUS_ID, QUEUE_NUM, APP_NOTES)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING APP_ID
            """, (patient_id, staff_id, app_date, app_time, default_status_id, queue_number, app_notes))
            app_id = cursor.fetchone()[0]
            
            log_audit(self.user_id, 'ADD', 'APPOINTMENTS', app_id)

            service_map = {
                "groupBoxFamPlan": "Family Planning",
                "groupBoxMatCare": "Maternal Care Package",
                "groupBoxPS": "Pap Smear"
            }

            for service_name, groupbox_name in service_map.items():
                groupbox = addAppWidget.findChild(QWidget, groupbox_name)
                checkbox = addAppWidget.findChild(QCheckBox, service_name)
                
                if groupbox and checkbox and not checkbox.isChecked():
                    groupbox.setVisible(False)
                
                elif groupbox and checkbox and checkbox.isChecked():
                    groupbox.setVisible(True)

            subservice_map = {
                "checkBoxFPCounseling": "Counseling",
                "checkBoxFPIUD": "IUD",
                "checkBoxFPCondom": "Condom",
                "checkBoxFPInjectible": "Injectable",
                "checkBoxFPPills": "Pills",
                "checkBoxMCPrenatal": "Prenatal Care",
                "checkBoxMCLaborMonitoring": "Labor Monitoring",
                "checkBoxMCNSD": "NSD",
                "checkBoxMCPostpartum": "Postpartum Care",
                "checkBoxpPSPapSmearService": "Pap Smear"
            }
            
            app_service_map = {}

            for sub_cb_name, sub_name in subservice_map.items():
                cb = addAppWidget.findChild(QCheckBox, sub_cb_name)
                if cb and cb.isChecked():
                    cursor.execute("SELECT SERV_TYPE_ID, SERV_ID FROM SERVICE_TYPE WHERE SERV_TYPE_NAME = %s", (sub_name,))
                    sub_res = cursor.fetchone()
                    if not sub_res:
                        continue
                    serv_type_id, serv_id = sub_res

                    cursor.execute("""
                        SELECT PST.PST_ID, PS.PS_ID
                        FROM PATIENT_SERVICE_TYPE PST
                        JOIN PATIENT_SERVICE PS ON PST.PS_ID = PS.PS_ID
                        WHERE PS.PAT_ID = %s AND PST.SERV_TYPE_ID = %s
                    """, (patient_id, serv_type_id))
                    pserv_type_res = cursor.fetchone()
                    if not pserv_type_res:
                        continue
                    pserv_type_id, pserv_id = pserv_type_res

                    if pserv_id not in app_service_map:
                        cursor.execute("""
                            INSERT INTO APPOINTMENT_SERVICE (APP_ID, PS_ID)
                            VALUES (%s, %s)
                            RETURNING APS_ID
                        """, (app_id, pserv_id))
                        app_serv_id = cursor.fetchone()[0]
                        app_service_map[pserv_id] = app_serv_id
                    else:
                        app_serv_id = app_service_map[pserv_id]

                    cursor.execute("""
                        INSERT INTO APPOINTMENT_SERVICE_TYPE (APS_ID, PST_ID)
                        VALUES (%s, %s)
                    """, (app_serv_id, pserv_type_id))

            self.conn.commit()
            QMessageBox.information(dialog, "Success", "Appointment saved successfully.")
            dialog.accept()
            self.appointment_list()

        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(dialog, "Error", f"Failed to save appointment: {e}")

    def view_appointment(self, row, column):
            app_id_item = self.tableWidApp.item(row, 0)
            
            if app_id_item is None:
                return
            
            app_id = app_id_item.text()
            
            dialog = ViewAppointmentDialog(app_id)  #Passing PAT_ID to View Patient Details and Forms
            dialog.appointment_updated.connect(self.appointment_list)
            dialog.exec_()
      
    def trashAppointment_list(self):
        if hasattr(self, 'trashDialog') and self.trashDialog is not None:
            if self.trashDialog.isVisible():
                self.trashDialog.raise_()
                self.trashDialog.activateWindow()
                return
        else:
            self.trashDialog = QDialog()
            self.trashDialog.setAttribute(Qt.WA_DeleteOnClose)
            self.trashDialog.destroyed.connect(lambda: setattr(self, 'trashDialog', None))

            uic.loadUi("wfui/trash_appointment.ui", self.trashDialog)
            self.trashDialog.setWindowTitle("Trash")
            self.trashDialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))

            trashAppWidget = self.trashDialog.findChild(QWidget, "widgetAppTrash")
            if not trashAppWidget:
                print("ERROR: widgetAppTrash not found!")
                return

            self.searchTrash = trashAppWidget.findChild(QLineEdit, "lineEditSearchAppTrash")
            self.trashTable = trashAppWidget.findChild(QTableWidget, "tableWidgetAppTrash")

            header = self.trashTable.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Fixed)
            column_sizes = [0, 210, 210, 150, 50, 130, 120]
            for i, size in enumerate(column_sizes):
                header.resizeSection(i, size)

            self.trashTable.setColumnHidden(0, True)
            self.trashTable.verticalHeader().setVisible(False)

            if self.searchTrash:
                self.searchTrash.textChanged.connect(lambda: self.search_trash(text=self.searchTrash.text(), trashTable=self.trashTable))
            self.trashTable.cellClicked.connect(lambda row, col: self.restore_or_delete_appointment(row, col, self.trashTable))

        self.refresh_trash_table()
        self.trashDialog.show()

        
    def search_trash(self, text, trashTable):
        for row in range(trashTable.rowCount()):
            match = False
            for col in range(trashTable.columnCount()):
                item = trashTable.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            trashTable.setRowHidden(row, not match)

    def restore_or_delete_appointment(self, row, column, trashTable):
        app_id = trashTable.item(row, 0).text()

        msg_box = QMessageBox(self.trashDialog)
        msg_box.setWindowTitle("Restore or Delete")
        msg_box.setText("Do you want to restore or permanently delete this appointment?")
        msg_box.setIcon(QMessageBox.Question)

        restore_button = msg_box.addButton("Restore", QMessageBox.YesRole)
        delete_button = msg_box.addButton("Delete", QMessageBox.DestructiveRole)
        cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)

        msg_box.exec_()

        if msg_box.clickedButton() == restore_button:
            self.restore_app(app_id)
        elif msg_box.clickedButton() == delete_button:
            self.delete_app(app_id)

    def restore_app(self, app_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE APPOINTMENT SET APP_ISDELETED = FALSE WHERE APP_ID = %s", (app_id,))
            self.conn.commit()
            QMessageBox.information(self.trashDialog, "Restoration Success", "Appointment has been restored successfully.")
            self.appointment_list()  
            self.refresh_trash_table()  
        except Exception as e:
            QMessageBox.critical(self.trashDialog, "Restore Error", f"Error restoring appointment: {e}")
        finally:
            cursor.close()

    def delete_app(self, app_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM APPOINTMENT WHERE APP_ID = %s", (app_id,))
            self.conn.commit()
            log_audit(self.user_id, 'DELETE', 'APPOINTMENTS', app_id)

            QMessageBox.information(self.trashDialog, "Deletion Success", "Appointment has been permanently deleted.")
            self.appointment_list()  
            self.refresh_trash_table() 
        except Exception as e:
            QMessageBox.critical(self.trashDialog, "Deletion Error", f"Error deleting appointment: {e}")
        finally:
            cursor.close()

    def refresh_trash_table(self):
        trashTable = self.trashDialog.findChild(QTableWidget, "tableWidgetAppTrash")
        trashTable.setRowCount(0)
        
        header = self.trashTable.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [0, 100, 100, 250, 150, 150, 100, 80]
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    A.APP_ID, A.APP_DATE, 
                    TO_CHAR(A.APP_TIME, 'HH12:MI AM') AS APP_TIME,
                    CONCAT(P.PAT_LNAME, ', ', P.PAT_FNAME) AS PATIENT_NAME,
                    S.SERV_NAME AS SERVICE_AVAILED,
                    ST.SERV_TYPE_NAME AS APPOINTMENT_TYPE,
                    CONCAT(U.STAFF_LNAME, ', ', U.STAFF_FNAME) AS ATTENDANT,
                    AS1.APP_STATUS_NAME AS STATUS
                FROM APPOINTMENT A
                JOIN PATIENT P ON A.PAT_ID = P.PAT_ID
                JOIN APPOINTMENT_SERVICE APS ON A.APP_ID = APS.APP_ID
                JOIN PATIENT_SERVICE PS ON APS.PS_ID = PS.PS_ID
                JOIN SERVICE S ON PS.SERV_ID = S.SERV_ID
                JOIN APPOINTMENT_SERVICE_TYPE AST ON APS.APS_ID = AST.APS_ID
                JOIN PATIENT_SERVICE_TYPE PST ON AST.PST_ID = PST.PST_ID
                JOIN SERVICE_TYPE ST ON PST.SERV_TYPE_ID = ST.SERV_TYPE_ID
                JOIN USER_STAFF U ON A.STAFF_ID = U.STAFF_ID
                JOIN APPOINTMENT_STATUS AS1 ON A.APP_STATUS_ID = AS1.APP_STATUS_ID
                WHERE A.APP_ISDELETED = TRUE
                AND P.PAT_ISDELETED = FALSE;
            """)
            rows = cursor.fetchall()

            for row in rows:
                row_position = trashTable.rowCount()
                trashTable.insertRow(row_position)
                for column, data in enumerate(row):
                    trashTable.setItem(row_position, column, QTableWidgetItem(str(data)))

        except Exception as e:
            QMessageBox.critical(self.trashDialog, "Error", f"Failed to refresh trash:\n{e}")
        finally:
            cursor.close()