from PyQt5.QtWidgets import (
    QMessageBox, QHeaderView, QTableWidgetItem, QTableWidget
)
from PyQt5.QtCore import Qt

from Database import connect_db

class AppointmentHistoryController:
    def __init__(self, appHpage, patient_id):
        self.conn = connect_db()
        self.appHpage = appHpage
        self.patient_id = patient_id
        
        self.tableWidAppH = self.appHpage.findChild(QTableWidget, "tableWidgetAppH")
        self.appointment_history()

    def appointment_history(self):
        self.tableWidAppH.setRowCount(0)
        
        header = self.tableWidAppH.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [0, 100, 100, 200, 200, 80, 80, 100, 200]
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)

        self.tableWidAppH.setColumnHidden(0, True)
        self.tableWidAppH.verticalHeader().setVisible(False)
                
        try:
            cursor = self.conn.cursor()
            query = """
                SELECT 
                    A.APP_ID, 
                    A.APP_DATE, 
                    TO_CHAR(A.APP_TIME, 'HH12:MI AM') AS APP_TIME,  -- Format the appointment time
                    S.SERV_NAME AS SERVICE_AVAILED,  -- Service availed by the patient
                    ST.SERV_TYPE_NAME AS APPOINTMENT_TYPE,  -- Appointment type (from patient service type)
                    TO_CHAR(A.APP_ACTUAL_START, 'HH12:MI AM') AS START_TIME,  -- Appointment start time
                    TO_CHAR(A.APP_ACTUAL_END, 'HH12:MI AM') AS END_TIME,  -- Appointment end time
                    AS1.APP_STATUS_NAME AS STATUS,  -- Status of the appointment
                    CONCAT(U.STAFF_LNAME, ', ', U.STAFF_FNAME) AS ATTENDANT  -- Attendant details
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
                AND P.PAT_ID = %s  -- Patient ID placeholder
                AND A.APP_STATUS_ID IN (2, 3, 4)  -- Filter for Completed, Cancelled, No Show statuses
                ORDER BY A.APP_DATE ASC, A.APP_TIME ASC;
            """
            cursor.execute(query, (self.patient_id,))
            rows = cursor.fetchall()

            for row in rows:
                row_position = self.tableWidAppH.rowCount()
                self.tableWidAppH.insertRow(row_position)
                for column, data in enumerate(row):
                    item = QTableWidgetItem(str(data))
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # Make it read-only
                    self.tableWidAppH.setItem(row_position, column, item)

        except Exception as e:
            QMessageBox.critical(self.tableWidAppH, "Database Error", f"Error fetching appointment history: {e}")