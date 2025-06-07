from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtWidgets import (
    QLabel, QCalendarWidget, QTableWidget, 
    QTableWidgetItem, QMessageBox, QHeaderView,
    QDialog, QWidget, QLineEdit, QPushButton
)
from PyQt5 import uic
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QIcon
from datetime import datetime

from Database import connect_db

class AdminDashboardController:
    def __init__(self, tableWidQueue: QTableWidget, tableWidMonApp: QTableWidget, time_label: QLabel, calendar_widget: QCalendarWidget, total_pat: QLabel, total_app: QLabel, greeting_label: QLabel):
        self.conn = connect_db()
        self.tableWidQueue = tableWidQueue
        self.tableWidMonApp = tableWidMonApp
        
        self.timeLabel = time_label
        self.calendar = calendar_widget
        self.totalPatLabel = total_pat
        self.totalAppLabel = total_app
        self.greetingLabel = greeting_label
        
        try:
            self.tableWidQueue.cellClicked.disconnect()
        except TypeError:
            pass
        self.tableWidQueue.cellClicked.connect(self.view_queue)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        self.greetings()
        self.update_time()
        self.total_patients()
        self.total_appointments()
        self.queue_table()
        self.monApp_table()
        
    def greetings(self):
        current_time = QTime.currentTime()
        time_text = current_time.toString("hh:mm:ss AP")
        self.timeLabel.setText(time_text)

        hour = current_time.hour()
        if 0 <= hour < 12:
            greeting = "Good Morning"
        elif 12 <= hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"

        self.greetingLabel.setText(greeting + "!")

    def update_time(self):
        current_time = QTime.currentTime()
        time_text = current_time.toString("hh:mm:ss AP")
        self.timeLabel.setText(time_text)
        
    def total_patients(self):
        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM PATIENT")
                count = cur.fetchone()[0]
                self.totalPatLabel.setText(str(count))
            except Exception as e:
                self.totalPatLabel.setText("Error loading patients")
                print(f"Error fetching total patients: {e}")
            finally:
                conn.close()

    def total_appointments(self):
        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM APPOINTMENT")
                count = cur.fetchone()[0]
                self.totalAppLabel.setText(str(count))
            except Exception as e:
                self.totalAppLabel.setText("Error loading appointments")
                print(f"Error fetching total appointments: {e}")
            finally:
                conn.close()
                
    def monApp_table(self):
        self.tableWidMonApp.setRowCount(0)
        
        today = datetime.today()
        year = today.year
        month = today.month
            
        header = self.tableWidMonApp.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [50, 98, 220]
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)
        
        self.tableWidMonApp.verticalHeader().setVisible(False)
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    EXTRACT(DAY FROM a.APP_DATE) AS app_day,
                    TO_CHAR(a.APP_TIME, 'HH12:MI AM') AS formatted_time,
                    CONCAT(p.PAT_LNAME, ', ', p.PAT_FNAME) AS patient_name
                FROM 
                    APPOINTMENT a
                JOIN PATIENT p ON a.PAT_ID = p.PAT_ID
                JOIN QUEUE_STATUS qs ON a.QUEUE_STATUS_ID = qs.QUEUE_STATUS_ID
                WHERE 
                    EXTRACT(MONTH FROM a.APP_DATE) = %s
                    AND EXTRACT(YEAR FROM a.APP_DATE) = %s
                    AND qs.QUEUE_STATUS_NAME != 'Cancelled'
                    AND a.APP_ISDELETED = FALSE
                ORDER BY a.APP_DATE, a.APP_TIME
            """, (month, year))
            monthly_app = cursor.fetchall()

            self.tableWidMonApp.setRowCount(0)
            for row in monthly_app:
                row_position = self.tableWidMonApp.rowCount()
                self.tableWidMonApp.insertRow(row_position)
                for column, value in enumerate(row):
                    self.tableWidMonApp.setItem(row_position, column, QTableWidgetItem(str(value)))

        except Exception as e:
            QMessageBox.critical(self.tableWidMonApp, "Database Error", f"Error fetching monthly appointments data: {e}")
                
    def queue_table(self):
        self.tableWidQueue.setRowCount(0)
        
        header = self.tableWidQueue.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [80, 98, 250, 160, 180, 100, 160]
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)
        
        self.tableWidQueue.verticalHeader().setVisible(False)
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    a.QUEUE_NUM,
                    TO_CHAR(a.APP_TIME, 'HH12:MI AM') as app_time,
                    CONCAT(p.PAT_LNAME, ', ', p.PAT_FNAME) AS patient_name,
                    COALESCE(string_agg(DISTINCT s.SERV_NAME, ', '), '') AS services,
                    COALESCE(string_agg(DISTINCT st.SERV_TYPE_NAME, ', '), '') AS appointment_types,
                    qs.QUEUE_STATUS_NAME,
                    CONCAT(stf.STAFF_LNAME, ', ', stf.STAFF_FNAME) AS staff_name,
                    CASE qs.QUEUE_STATUS_NAME
                        WHEN 'Being Attended' THEN 1
                        WHEN 'Waiting' THEN 2
                        WHEN 'Skipped' THEN 3
                        WHEN 'Served' THEN 4
                        ELSE 5 -- for safety if other statuses exist
                    END AS status_order
                FROM 
                    APPOINTMENT a
                JOIN PATIENT p ON a.PAT_ID = p.PAT_ID
                JOIN USER_STAFF stf ON a.STAFF_ID = stf.STAFF_ID
                JOIN QUEUE_STATUS qs ON a.QUEUE_STATUS_ID = qs.QUEUE_STATUS_ID
                LEFT JOIN APPOINTMENT_SERVICE aps ON a.APP_ID = aps.APP_ID
                LEFT JOIN APPOINTMENT_SERVICE_TYPE ast ON aps.APS_ID = ast.APS_ID
                LEFT JOIN PATIENT_SERVICE ps ON aps.PS_ID = ps.PS_ID
                LEFT JOIN PATIENT_SERVICE_TYPE pst ON ast.PST_ID = pst.PST_ID
                LEFT JOIN SERVICE s ON ps.SERV_ID = s.SERV_ID
                LEFT JOIN SERVICE_TYPE st ON pst.SERV_TYPE_ID = st.SERV_TYPE_ID
                WHERE 
                    a.APP_DATE = CURRENT_DATE 
                    AND qs.QUEUE_STATUS_NAME != 'Cancelled'
                    AND a.APP_ISDELETED = FALSE
                GROUP BY 
                    a.QUEUE_NUM, p.PAT_LNAME, p.PAT_FNAME, a.APP_TIME, qs.QUEUE_STATUS_NAME, stf.STAFF_LNAME, stf.STAFF_FNAME
                ORDER BY 
                    status_order ASC, a.QUEUE_NUM ASC;
            """)
            rows = cursor.fetchall()

            self.tableWidQueue.setRowCount(0)
            for row in rows:
                row_position = self.tableWidQueue.rowCount()
                self.tableWidQueue.insertRow(row_position)
                for column, data in enumerate(row):
                    self.tableWidQueue.setItem(row_position, column, QTableWidgetItem(str(data)))

        except Exception as e:
            QMessageBox.critical(self.tableWidQueue, "Database Error", f"Error fetching queue table data: {e}")
            
    def view_queue(self, row, column):
        if hasattr(self, 'queueDialog') and self.queueDialog is not None:
            if self.queueDialog.isVisible():
                self.queueDialog.raise_()
                self.queueDialog.activateWindow()
                return
        else:
            self.queueDialog = QDialog()
            self.queueDialog.setAttribute(Qt.WA_DeleteOnClose)
            self.queueDialog.destroyed.connect(lambda: setattr(self, 'queueDialog', None))

            uic.loadUi("wfui/queue.ui", self.queueDialog)
            self.queueDialog.setWindowTitle("View Patient Queue Details")
            self.queueDialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))

            queueWidget = self.queueDialog.findChild(QWidget, "widgetQueue")
            if not queueWidget:
                print("ERROR: widgetQueue not found!")
                return
            
            self.queueNo = self.queueDialog.findChild(QLineEdit, "lineEditQueueNo")
            self.patientName = self.queueDialog.findChild(QLineEdit, "lineEditPatName")
            self.appointmentTime = self.queueDialog.findChild(QLineEdit, "lineEditAppTime")

            self.checkboxYes = self.queueDialog.findChild(QWidget, "checkBoxYes")
            self.checkboxNo = self.queueDialog.findChild(QWidget, "checkBoxNo")
            
            self.comboStatusNo = self.queueDialog.findChild(QWidget, "comboStatusNo")  # waiting/skipped
            self.timeEditStart = self.queueDialog.findChild(QWidget, "timeEditStartTime")
            
            self.comboMarkServed = self.queueDialog.findChild(QWidget, "comboMarkServed")  # yes/no
            self.timeEditEnd = self.queueDialog.findChild(QWidget, "timeEditEndTime")

            self.comboStatusNo.setEnabled(False)
            self.timeEditStart.setEnabled(False)
            self.comboMarkServed.setEnabled(False)
            self.timeEditEnd.setEnabled(False)

            self.checkboxYes.toggled.connect(self.yes_checked)
            self.checkboxNo.toggled.connect(self.no_checked)
            self.comboMarkServed.currentIndexChanged.connect(self.mark_served_changed)

            self.saveButton = self.queueDialog.findChild(QPushButton, "pushBtnSaveQueue")
            self.saveButton.clicked.connect(self.save_queue_update)
        
        queue_no = self.tableWidQueue.item(row, 0).text()
        app_time = self.tableWidQueue.item(row, 1).text()
        patient_name = self.tableWidQueue.item(row, 2).text()

        self.queueNo.setText(queue_no)
        self.queueNo.setEnabled(False)

        self.patientName.setText(patient_name)
        self.patientName.setEnabled(False)

        if isinstance(app_time, str):
            try:
                time_obj = datetime.strptime(app_time, "%I:%M %p")
                formatted_time = time_obj.strftime("%I:%M %p")  
            except ValueError:
                formatted_time = app_time
        else:
            formatted_time = app_time.strftime("%I:%M %p")
        self.appointmentTime.setText(formatted_time)
        self.appointmentTime.setEnabled(False)
        
        try:
            cursor = self.conn.cursor()
            query = """
                SELECT 
                    qs.QUEUE_STATUS_NAME, 
                    a.APP_ACTUAL_START, 
                    a.APP_ACTUAL_END
                FROM APPOINTMENT a
                JOIN QUEUE_STATUS qs ON a.QUEUE_STATUS_ID = qs.QUEUE_STATUS_ID
                WHERE a.QUEUE_NUM = %s
                AND a.APP_DATE = CURRENT_DATE
            """
            cursor.execute(query, (queue_no,))
            result = cursor.fetchone()

            if result:
                queue_status_name, app_actual_start, app_actual_end = result

                self.checkboxYes.setEnabled(False)
                self.checkboxNo.setEnabled(False)
                self.comboStatusNo.setEnabled(False)
                self.comboMarkServed.setEnabled(False)
                self.timeEditStart.setEnabled(False)
                self.timeEditEnd.setEnabled(False)

                if queue_status_name == "Being Attended":
                    self.checkboxYes.setChecked(True)
                    self.checkboxYes.setEnabled(False)
                    self.checkboxNo.setEnabled(False)
                    self.comboStatusNo.setEnabled(False)

                    self.timeEditStart.setEnabled(True)
                    self.timeEditStart.setReadOnly(True)

                    if app_actual_start:
                        time = QTime.fromString(str(app_actual_start), "HH:mm:ss")
                        self.timeEditStart.setTime(time)
                    else:
                        self.timeEditStart.setTime(QTime.currentTime())

                    self.comboMarkServed.setEnabled(True)
                    if app_actual_end:
                        self.comboMarkServed.setCurrentText("Yes")
                        self.timeEditEnd.setEnabled(True)
                        end_time = QTime.fromString(str(app_actual_end), "HH:mm:ss")
                        self.timeEditEnd.setTime(end_time)
                        self.timeEditEnd.setReadOnly(True)
                        self.comboMarkServed.setEnabled(False)
                    else:
                        self.comboMarkServed.setCurrentText("No")
                        self.timeEditEnd.setEnabled(False)

                elif queue_status_name == "Served":
                    # Served - all fields read-only
                    self.checkboxYes.setChecked(True)
                    self.checkboxYes.setEnabled(False)
                    self.checkboxNo.setEnabled(False)
                    self.comboStatusNo.setEnabled(False)
                    self.comboMarkServed.setEnabled(False)

                    if app_actual_start:
                        self.timeEditStart.setEnabled(True)
                        self.timeEditStart.setReadOnly(True)
                        time = QTime.fromString(str(app_actual_start), "HH:mm:ss")
                        self.timeEditStart.setTime(time)

                    if app_actual_end:
                        self.comboMarkServed.setCurrentText("Yes")
                        self.timeEditEnd.setEnabled(True)
                        self.timeEditEnd.setReadOnly(True)
                        end_time = QTime.fromString(str(app_actual_end), "HH:mm:ss")
                        self.timeEditEnd.setTime(end_time)

                elif queue_status_name == "Skipped":
                    self.checkboxNo.setChecked(True)
                    self.checkboxYes.setEnabled(False)
                    self.checkboxNo.setEnabled(False)
                    self.comboStatusNo.setEnabled(False)

                    if queue_status_name == "Skipped":
                        self.comboStatusNo.setCurrentText("Skipped")
                    else:
                        self.comboStatusNo.setCurrentText("Waiting")

                else:
                    # Default new entry
                    self.checkboxYes.setEnabled(True)
                    self.checkboxNo.setEnabled(True)
                    self.comboStatusNo.setEnabled(False)
                    self.comboMarkServed.setEnabled(False)
                    self.timeEditEnd.setEnabled(False)
        except Exception as e:
            print(f"Database error fetching queue status: {e}")

        self.queue_table()
        self.queueDialog.show()
    
    def yes_checked(self, checked):
        if checked:
            self.timeEditStart.setEnabled(True)
            self.checkboxNo.setChecked(False)  
            self.comboStatusNo.setEnabled(False)
        else:
            self.timeEditStart.setEnabled(False)

    def no_checked(self, checked):
        if checked:
            self.comboStatusNo.setEnabled(True)
            self.checkboxYes.setChecked(False)  
            self.timeEditStart.setEnabled(False)
        else:
            self.comboStatusNo.setEnabled(False)

    def mark_served_changed(self):
        if self.comboMarkServed.currentText().lower() == "yes":
            self.timeEditEnd.setEnabled(True)
        else:
            self.timeEditEnd.setEnabled(False)
            
    def being_attended(self):
        self.checkboxYes.setEnabled(False)  
        self.timeEditStart.setEnabled(False)  
        self.comboStatusNo.setEnabled(False)  
        self.comboMarkServed.setEnabled(True)
        self.timeEditEnd.setEnabled(True)
        
        if not self.timeEditStart.time().isValid(): 
            current_time = QTime.currentTime()
            self.timeEditStart.setTime(current_time)  

        self.checkboxYes.setChecked(True)
            
    def save_queue_update(self):
        queue_num = self.queueNo.text().strip()

        if not queue_num:
            QMessageBox.warning(self.queueDialog, "Missing Data", "Queue number is missing.")
            return

        queue_status = None
        actual_start_time = None
        actual_end_time = None

        if self.checkboxYes.isChecked():
            queue_status = "Being Attended"
            actual_start_time = self.timeEditStart.time().toString("HH:mm:ss")
        elif self.checkboxNo.isChecked():
            selected_status = self.comboStatusNo.currentText()
            if not selected_status:
                QMessageBox.warning(self.queueDialog, "Missing Data", "Please select a status for 'No' option.")
                return
            queue_status = selected_status
        else:
            QMessageBox.warning(self.queueDialog, "Selection Missing", "Please select Yes or No.")
            return

        if self.comboMarkServed.currentText().lower() == "yes":
            if not self.timeEditEnd.time().isValid():
                QMessageBox.warning(self.queueDialog, "Invalid Time", "Please set a valid End Time for marking as Served.")
                return
            actual_end_time = self.timeEditEnd.time().toString("HH:mm:ss")
            queue_status = "Served"
        else:
            actual_end_time = None

        try:
            cursor = self.conn.cursor()

            cursor.execute(
                "SELECT QUEUE_STATUS_ID FROM QUEUE_STATUS WHERE QUEUE_STATUS_NAME = %s",
                (queue_status,)
            )
            result = cursor.fetchone()
            if not result:
                QMessageBox.critical(self.queueDialog, "Error", f"Queue status '{queue_status}' not found in database.")
                return

            queue_status_id = result[0]

            update_query = """
                UPDATE APPOINTMENT
                SET 
                    QUEUE_STATUS_ID = %s,
                    APP_ACTUAL_START = %s,
                    APP_ACTUAL_END = %s
                WHERE 
                    QUEUE_NUM = %s
                    AND APP_DATE = CURRENT_DATE
            """
            cursor.execute(update_query, (queue_status_id, actual_start_time, actual_end_time, queue_num))

            # If served, update earlier skipped patients
            if queue_status == "Served":
                update_skipped_query = """
                    UPDATE APPOINTMENT
                    SET QUEUE_STATUS_ID = (SELECT QUEUE_STATUS_ID FROM QUEUE_STATUS WHERE QUEUE_STATUS_NAME = 'Waiting')
                    WHERE QUEUE_NUM < %s
                    AND APP_DATE = CURRENT_DATE
                    AND QUEUE_STATUS_ID = (SELECT QUEUE_STATUS_ID FROM QUEUE_STATUS WHERE QUEUE_STATUS_NAME = 'Skipped')
                """
                cursor.execute(update_skipped_query, (queue_num,))

            self.conn.commit()

            QMessageBox.information(self.queueDialog, "Success", "Queue updated successfully.")

            self.queue_table()
            self.queueDialog.close()

        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self.queueDialog, "Database Error", f"Error updating queue: {e}")
