from PyQt5.QtWidgets import (
    QComboBox, QDialog, QMessageBox, QPushButton, QFrame,
    QWidget, QTableWidget, QLabel, QToolTip, QFileDialog,
    QHeaderView, QTableWidgetItem, QStackedWidget, QVBoxLayout
)
from PyQt5.QtCore import QMargins, QPointF
from PyQt5 import uic
from Database import connect_db

from PyQt5.QtChart import QChartView, QChart, QLineSeries, QCategoryAxis, QValueAxis
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QCursor
import math

class AdminReportController:
    def __init__(self, servicesAvailed: QFrame, lineChart: QWidget, pregNo: QFrame, notpregNo: QFrame, monthlyVServ: QFrame, viewLogs: QPushButton):
        self.conn = connect_db()
        self.servicesAvailed = servicesAvailed
        self.pregNo = pregNo
        self.notpregNo = notpregNo
        self.lineChart = lineChart
        self.monthlyVServ = monthlyVServ
        self.viewLogs = viewLogs # Button to open a log dialog
        self.viewLogs.clicked.connect(self.open_logs_dialog)

        self.line_series = None
        self.chart_view_line = None
        self.chart_line = None

        self.slice_labels = []
        self.slice_index = 0
        self.timer = None
        
        self.stackWidServ = self.servicesAvailed.findChild(QStackedWidget, "serviceNo")
        
        self.prev_btn = self.servicesAvailed.findChild(QPushButton, "pushBtnPrev")
        self.next_btn = self.servicesAvailed.findChild(QPushButton, "pushBtnNext")
        
        self.prev_btn.clicked.connect(self.go_prev)
        self.next_btn.clicked.connect(self.go_next)
        
        self.pregLabel = self.pregNo.findChild(QLabel, "PREGNUM")
        self.notpregLabel = self.notpregNo.findChild(QLabel, "NOTPREGNUM")
        
        self.comboMonth = self.monthlyVServ.findChild(QComboBox, "comboBoxMonth")
        self.comboService = self.monthlyVServ.findChild(QComboBox, "comboBoxService")
        
        if self.comboMonth:
            self.comboMonth.currentIndexChanged.connect(self.filter_appointment_count)
        if self.comboService:
            self.comboService.currentIndexChanged.connect(self.filter_appointment_count)
        self.load_services()
        
        self.stackWidServ.setCurrentIndex(0)
        self.update_nav_buttons()
        self.noPatS()
        self.ynpregPat()
        self.filter_appointment_count()
    
    def go_prev(self):
        current_index = self.stackWidServ.currentIndex()
        if current_index > 0:
            self.stackWidServ.setCurrentIndex(current_index - 1)
        self.update_nav_buttons()

    def go_next(self):
        current_index = self.stackWidServ.currentIndex()
        if current_index < self.stackWidServ.count() - 1:
            self.stackWidServ.setCurrentIndex(current_index + 1)
        self.update_nav_buttons()

    def update_nav_buttons(self):
        current_index = self.stackWidServ.currentIndex()
        self.prev_btn.setEnabled(current_index > 0)
        self.next_btn.setEnabled(current_index < self.stackWidServ.count() - 1)
        
    def noPatS(self):
        self.matNum = self.servicesAvailed.findChild(QLabel, "MATNO")
        self.famNum = self.servicesAvailed.findChild(QLabel, "FAMNO")
        self.papNum = self.servicesAvailed.findChild(QLabel, "PAPNO")

        cursor = self.conn.cursor()
        try:
            query = """
            SELECT s.SERV_NAME, COUNT(DISTINCT ps.PAT_ID)
            FROM SERVICE s
            LEFT JOIN PATIENT_SERVICE ps ON s.SERV_ID = ps.SERV_ID
            GROUP BY s.SERV_NAME
            """
            cursor.execute(query)
            results = cursor.fetchall()

            counts = {
                'Maternal Care Package': 0,
                'Family Planning': 0,
                'Pap Smear': 0
            }
            for serv_name, count in results:
                if serv_name in counts:
                    counts[serv_name] = count

            self.matNum.setText(str(counts.get('Maternal Care Package', 0)))
            self.famNum.setText(str(counts.get('Family Planning', 0)))
            self.papNum.setText(str(counts.get('Pap Smear', 0)))
        except Exception as e:
            print("Error in noPatS:", e)
        finally:
            cursor.close()
            
    def ynpregPat(self):
        cursor = self.conn.cursor()
        try:
            query = """
                SELECT 
                    PAT_ISPREG, COUNT(*) 
                FROM PATIENT
                WHERE PAT_ISDELETED = FALSE
                GROUP BY PAT_ISPREG
            """
            cursor.execute(query)
            results = cursor.fetchall()

            # Initialize counts
            pregnant_count = 0
            notpreg_count = 0

            for is_preg, count in results:
                if is_preg == 'Y':
                    pregnant_count = count
                elif is_preg == 'N':
                    notpreg_count = count

            self.pregLabel.setText(str(pregnant_count))
            self.notpregLabel.setText(str(notpreg_count))

        except Exception as e:
            print("Error in ynpregPat:", e)
        finally:
            cursor.close()
        
    def _clear_layout(self, widget):
        layout = widget.layout()
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            QWidget().setLayout(layout)
        
    def line_chart(self):
        self._clear_layout(self.lineChart)

        cursor = self.conn.cursor()
        query = """
            SELECT 
                EXTRACT(MONTH FROM APP_DATE) AS month,
                COUNT(*) AS visit_count
            FROM APPOINTMENT
            GROUP BY month
            ORDER BY month;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        data_points = [(int(month), count) for month, count in results]
        
        self.data_points = [QPointF(x, y) for x, y in data_points]

        self.line_series = QLineSeries()
        for x, y in data_points:
            self.line_series.append(x, y)

        pen = QPen(QColor(0, 120, 215))
        pen.setWidth(3)
        self.line_series.setPen(pen)
        self.line_series.setPointsVisible(True)

        self.chart_line = QChart()
        self.chart_line.addSeries(self.line_series)
        self.chart_line.setTitle("Monthly Patient Visits")
        self.chart_line.setTitleFont(QFont("Segoe UI", 14, QFont.Black))
        self.chart_line.setTitleBrush(QColor(0, 51, 102))
        self.chart_line.legend().hide()
        
        self.chart_line.setBackgroundBrush(QColor(255, 255, 255))
        self.chart_line.setBackgroundRoundness(10)
        self.chart_line.setMargins(QMargins(0, 0, 0, 0))

        axis_x = QCategoryAxis()
        axis_x.setTitleText("Month")
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for i in range(12):
            axis_x.append(month_names[i], i+1)
        axis_x.setRange(0, 12)
        
        max_y = max([count for _, count in data_points], default=0)

        max_y_with_margin = int(max_y * 1.1) if max_y > 0 else 5
        max_y_rounded = ((max_y_with_margin + 4) // 5) * 5

        axis_y = QValueAxis()
        axis_y.setTitleText("Appointments")
        axis_y.setLabelFormat("%d")
        axis_y.setRange(0, max_y_rounded)
        axis_y.setTickInterval(5)
        axis_y.setTickCount(max_y_rounded // 5 + 1)

        self.chart_line.setAxisX(axis_x, self.line_series)
        self.chart_line.setAxisY(axis_y, self.line_series)

        self.chart_view_line = QChartView(self.chart_line)
        self.chart_view_line.setRenderHint(QPainter.Antialiasing)
        self.chart_view_line.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.chart_view_line)
        self.lineChart.setLayout(layout)
        self.lineChart.setStyleSheet("""
            background-color: white;
            border: 1px solid rgb(0, 51, 102);
            border-radius: 10px;
        """)
        
        self.line_series.hovered.connect(self.point_hovered)
        
    def point_hovered(self, point: QPointF, state: bool):
        if state:
            mouse_pos = self.chart_view_line.mapFromGlobal(QCursor.pos())
            chart_pos = self.chart_line.mapToValue(mouse_pos, self.line_series)

            radius = 0.3 

            for pt in self.data_points:
                dist = math.sqrt((chart_pos.x() - pt.x())**2 + (chart_pos.y() - pt.y())**2)
                if dist <= radius:
                    text = f"{int(pt.y())} patients"
                    QToolTip.showText(QCursor.pos(), text)
                    return

            QToolTip.hideText()

        else:
            QToolTip.hideText()
    
    def load_services(self):
        if not self.comboService:
            print("comboService not found!")
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT SERV_NAME FROM SERVICE ORDER BY SERV_NAME")
            rows = cursor.fetchall()
            services = [row[0] for row in rows]
            self.comboService.clear()
            self.comboService.addItems(services)
        except Exception as e:
            print(f"Failed to load services: {e}")
        
    def filter_appointment_count(self):
        self.labelAppointmentCount = self.monthlyVServ.findChild(QLabel, "servNO")
        
        selected_month = self.comboMonth.currentText()
        selected_service = self.comboService.currentText()

        if not selected_month or not selected_service:
            self.labelAppointmentCount.setText("0")
            return
        
        month_num = self.get_month_number(selected_month)

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT A.APP_ID)
                FROM APPOINTMENT A
                JOIN APPOINTMENT_SERVICE APS ON A.APP_ID = APS.APP_ID
                JOIN PATIENT_SERVICE PS ON APS.PS_ID = PS.PS_ID
                JOIN SERVICE S ON PS.SERV_ID = S.SERV_ID
                WHERE TO_CHAR(A.APP_DATE, 'MM') = %s
                AND S.SERV_NAME = %s
            """, (month_num, selected_service))
            
            count = cursor.fetchone()[0] or 0
            self.labelAppointmentCount.setText(str(count))

        except Exception as e:
            QMessageBox.critical(None, "Database Error", f"Failed to load appointment count: {e}")
            self.labelAppointmentCount.setText("Appointments: Error")
    
    def get_month_number(self, month_name):
        months = {
            "January": "01", "February": "02", "March": "03",
            "April": "04", "May": "05", "June": "06",
            "July": "07", "August": "08", "September": "09",
            "October": "10", "November": "11", "December": "12"
        }
        return months.get(month_name, "01")
    
    def open_logs_dialog(self):
        logs_dialog = QDialog()
        uic.loadUi("wfui/view_logs.ui", logs_dialog)
        
        # ===== VIEWING OLD LOGIN LOGS BY CSV =====
        oldlogs_btn = logs_dialog.findChild(QPushButton, "pushBtnVOL")
        
        if oldlogs_btn is None:
            QMessageBox.warning(logs_dialog, "UI Error", "Could not find the view logs button in the UI file")
        else:
            def view_csv_logs():
                import os
                logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')  # Adjust path as needed
                
                file_path, _ = QFileDialog.getOpenFileName(
                    logs_dialog,
                    "Select CSV Log File",
                    logs_dir,  
                    "CSV Files (*.csv);;All Files (*)"
                )
                
                if file_path: 
                    try:
                        with open(file_path, 'r') as csvfile:
                            from csv import reader
                            csv_reader = reader(csvfile)
                            header = next(csv_reader) 
                            
                            login_table = logs_dialog.findChild(QTableWidget, "tableLogin")
                            login_table.setRowCount(0)
                            for row_data in csv_reader:
                                row_position = login_table.rowCount()
                                login_table.insertRow(row_position)
                                for column, data in enumerate(row_data):
                                    login_table.setItem(row_position, column, QTableWidgetItem(str(data)))
                                    
                    except Exception as e:
                        QMessageBox.critical(logs_dialog, "Error", f"Could not read CSV file: {e}")
            
            oldlogs_btn.clicked.connect(view_csv_logs)
        
        # ===== VIEWING OLD LOGIN LOGS BY CSV =====
        auditoldlogs_btn = logs_dialog.findChild(QPushButton, "pushBtnVAL")
        
        if auditoldlogs_btn is None:
            QMessageBox.warning(logs_dialog, "UI Error", "Could not find the view logs button in the UI file")
        else:
            def view_csv_logs():
                import os
                logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')  # Adjust path as needed
                
                file_path, _ = QFileDialog.getOpenFileName(
                    logs_dialog,
                    "Select CSV Log File",
                    logs_dir,  
                    "CSV Files (*.csv);;All Files (*)"
                )
                
                if file_path: 
                    try:
                        with open(file_path, 'r') as csvfile:
                            from csv import reader
                            csv_reader = reader(csvfile)
                            header = next(csv_reader) 
                            
                            login_table = logs_dialog.findChild(QTableWidget, "tableLogin")
                            login_table.setRowCount(0)
                            for row_data in csv_reader:
                                row_position = login_table.rowCount()
                                login_table.insertRow(row_position)
                                for column, data in enumerate(row_data):
                                    login_table.setItem(row_position, column, QTableWidgetItem(str(data)))
                                    
                    except Exception as e:
                        QMessageBox.critical(logs_dialog, "Error", f"Could not read CSV file: {e}")
            
            auditoldlogs_btn.clicked.connect(view_csv_logs)

        # ===== TAB 1: LOGIN LOGS =====
        login_table = logs_dialog.findChild(QTableWidget, "tableLogin")
        
        login_table.setRowCount(0)
        login_table.verticalHeader().setVisible(False)
        
        header = login_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [60, 188, 100, 140, 140]  
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    ul.STAFF_ID, 
                    us.STAFF_USN, 
                    ul.LOG_ACTNTYPE, 
                    ul.LOG_IPADDRESS, 
                    TO_CHAR(ul.LOG_ACTNTIMESTMP, 'YYYY-MM-DD HH24:MI:SS') as formatted_time
                FROM USER_LOG ul
                JOIN USER_STAFF us ON ul.STAFF_ID = us.STAFF_ID
                WHERE ul.LOG_ACTNTYPE IN ('LOGIN', 'LOGOUT')
                ORDER BY ul.LOG_ACTNTIMESTMP DESC
            """)
            rows = cursor.fetchall()

            login_table.setRowCount(0)
            for row in rows:
                row_position = login_table.rowCount()
                login_table.insertRow(row_position)
                for column, data in enumerate(row):
                    login_table.setItem(row_position, column, QTableWidgetItem(str(data)))

        except Exception as e:
            QMessageBox.critical(logs_dialog, "Database Error", f"Error fetching login logs: {e}")

        # ===== TAB 2: AUDIT LOGS ===== 
        audit_table = logs_dialog.findChild(QTableWidget, "tableAudit")
        audit_table.setRowCount(0)
        audit_table.verticalHeader().setVisible(False)
        
        header = audit_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [60, 188, 100, 140, 140]  
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    us.STAFF_ID as user_id,
                    us.STAFF_USN as user_username,
                    a.AUDT_ACTIONTYPE,
                    a.AUDT_TABLE,
                    TO_CHAR(a.LOG_ACTNTIMESTMP, 'YYYY-MM-DD HH24:MI:SS') as formatted_time
                FROM AUDIT_LOG a
                JOIN USER_STAFF us ON a.STAFF_ID = us.STAFF_ID
                ORDER BY a.LOG_ACTNTIMESTMP DESC
            """)
            rows = cursor.fetchall()

            audit_table.setRowCount(0)
            for row in rows:
                row_position = audit_table.rowCount()
                audit_table.insertRow(row_position)
                for column, data in enumerate(row):
                    audit_table.setItem(row_position, column, QTableWidgetItem(str(data)))

        except Exception as e:
            QMessageBox.critical(logs_dialog, "Database Error", f"Error fetching login logs: {e}")

        logs_dialog.exec_()