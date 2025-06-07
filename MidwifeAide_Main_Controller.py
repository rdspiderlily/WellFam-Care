from PyQt5.QtWidgets import (
    QApplication, QDialog, QMessageBox, QStackedWidget, 
    QPushButton, QLabel, QCalendarWidget, QLineEdit, 
    QTableWidget, QWidget, QComboBox, QFrame
)
from PyQt5 import uic
from PyQt5.QtGui import QIcon, QPixmap
import sys
import os

from MidwifeAide_Controllers.MA_Dashboard import MADashboardController
from MidwifeAide_Controllers.MA_Patient import MAPatientController
from MidwifeAide_Controllers.MA_Appointment import MAAppointmentController
from MidwifeAide_Controllers.MA_Files import MAFilesController
from MidwifeAide_Controllers.MA_Reports import MAReportController
from MidwifeAide_Controllers.MA_Settings import MAProfileController

from Database import connect_db

class MidwifeAideMainWindow(QDialog):
    def __init__(self, username, user_id, pic=None):
        super().__init__()

        self.username = username
        self.user_id = user_id
        self.pic = pic or "staff_images/default_user.png"
        
        uic.loadUi("wfui/midwifeui/midwife_dashboard.ui", self)
        self.setWindowTitle("WellFam Care")
        self.setWindowIcon(QIcon("wfpics/logo1.jpg"))

        self.midwife_username = self.findChild(QLabel, "midwifeUName")
        if self.midwife_username:
            self.midwife_username.setText(self.username)

        self.midwife_pic = self.findChild(QLabel, "userPic")
        if self.midwife_pic:
            image_path = self.get_profile_image_path(self.username)
            self.set_profile_picture(image_path)
        else:
            print("QLabel for profile picture not found!")

        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.home_button = self.findChild(QPushButton, "pushBtnHome")
        self.patients_button = self.findChild(QPushButton, "pushBtnPatient")
        self.appointments_button = self.findChild(QPushButton, "pushBtnAppointments")
        self.files_button = self.findChild(QPushButton, "pushBtnFiles")
        self.report_button = self.findChild(QPushButton, "pushBtnReports")
        self.settings_button = self.findChild(QPushButton, "pushBtnSettings")

        self.home_button.clicked.connect(self.dashboard)
        self.patients_button.clicked.connect(self.patient)
        self.appointments_button.clicked.connect(self.appointment)
        self.files_button.clicked.connect(self.files)
        self.report_button.clicked.connect(self.report)
        self.settings_button.clicked.connect(self.settings)

        self.logout_button = self.findChild(QPushButton, "pushBtnLogout")
        if self.logout_button:
            self.logout_button.clicked.connect(self.logout)
        
        self.patient()
        self.dashboard()
    
    def open_admin_settings(self):
        profile_controller = MAProfileController(self, None, None, None)
        profile_controller.set_username(self.username)

        profile_controller.view_edit_dialog()

        image_path = self.get_profile_image_path(self.username)
        self.set_profile_picture(image_path)
    
    def get_profile_image_path(self, username):
        conn = connect_db()
        if not conn:
            return "staff_images/default_user.png"

        try:
            cur = conn.cursor()
            cur.execute("SELECT STAFF_PIC_PATH FROM USER_STAFF WHERE STAFF_USN = %s", (username,))
            result = cur.fetchone()
            if result and result[0] and os.path.exists(result[0]):
                return result[0]
            else:
                return "staff_images/default_user.png"
        finally:
            conn.close()

    def set_profile_picture(self, image_path):
        if self.midwife_pic:
            pixmap = QPixmap(image_path).scaled(80, 80)
            self.midwife_pic.setPixmap(pixmap)

    def dashboard(self):
        self.stackedWidget.setCurrentIndex(0)
        self.set_active_button(self.home_button)
        
        self.btnAppointments = self.findChild(QPushButton, "btnToApp")
        if self.btnAppointments:
            self.btnAppointments.clicked.connect(self.appointment)
            
        self.tableWidQueue = self.findChild(QTableWidget, "tableWidQueue")
        self.tableWidMonApp = self.findChild(QTableWidget, "tableWidMonApp")
        self.time_label = self.findChild(QLabel, "timeLabel")
        self.calendar_widget = self.findChild(QCalendarWidget, "midwifeCalendar")
        self.total_pat = self.findChild(QLabel, "NoPats")
        self.total_app = self.findChild(QLabel, "NoApps")
        self.greeting_label = self.findChild(QLabel, "greetingLabel")
        self.dashboard_controller = MADashboardController(
            self.tableWidQueue, self.tableWidMonApp, self.time_label, 
            self.calendar_widget, self.total_pat, self.total_app, self.greeting_label
        )

    def patient(self):
        self.clear()
        self.stackedWidget.setCurrentIndex(1)
        self.set_active_button(self.patients_button)
        self.tableWidPat = self.findChild(QTableWidget, "tableWidgetPat")
        self.searchPat = self.findChild(QLineEdit, "lineEditSearchPat")
        self.patient_controller = MAPatientController(self.tableWidPat, self.searchPat, self.user_id)

        self.addPat_button = self.findChild(QPushButton, "pushBtnAddNPat")
        if self.addPat_button:
            self.addPat_button.clicked.connect(self.patient_controller.add_patient_dialog)
            
        self.trashPat_button = self.findChild(QPushButton, "pushBtnTrashPat")
        if self.trashPat_button:
            self.trashPat_button.clicked.connect(self.patient_controller.trash_list)
       
    def appointment(self):
        self.clear()
        self.stackedWidget.setCurrentIndex(2)
        self.set_active_button(self.appointments_button)
        self.tableWidApp = self.findChild(QTableWidget, "tableWidgetApp")
        self.searchApp = self.findChild(QLineEdit, "lineEditSearchApp")
        self.sortAppCombo = self.findChild(QComboBox, "sortAppBtn")
        self.appointment_controller = MAAppointmentController(self.tableWidApp, self.searchApp, self.sortAppCombo, self.user_id)
        
        self.addApp_button = self.findChild(QPushButton, "pushBtnAddApp")
        if self.addApp_button:
            self.addApp_button.clicked.connect(self.appointment_controller.add_appointment_dialog)

        self.trashApp_button = self.findChild(QPushButton, "pushBtnTrashApp")
        if self.trashApp_button:
            self.trashApp_button.clicked.connect(self.appointment_controller.trashAppointment_list)

    def files(self):
        self.clear()
        self.stackedWidget.setCurrentIndex(3)
        self.set_active_button(self.files_button)
        self.tableWidFiles = self.findChild(QTableWidget, "tableWidgetFile")
        self.searchFiles = self.findChild(QLineEdit, "lineEditSearchFile")
        self.sortFilesCombo = self.findChild(QComboBox, "sortFilesBtn")
        self.files_controller = MAFilesController(self.tableWidFiles, self.searchFiles, self.sortFilesCombo, self.user_id)
        
        self.uploadFile_button = self.findChild(QPushButton, "pushBtnUploadFile")
        if self.uploadFile_button:
            self.uploadFile_button.clicked.connect(self.files_controller.upload_file_dialog)
        
        self.trashFile_button = self.findChild(QPushButton, "pushBtnTrashFile")
        if self.trashFile_button:
            self.trashFile_button.clicked.connect(self.files_controller.file_trash_dialog)
    
    def report(self):
        self.clear()
        self.stackedWidget.setCurrentIndex(4)
        self.set_active_button(self.report_button)
        self.servicesAvailed = self.findChild(QFrame, "serviceAvailed")
        self.pregNo = self.findChild(QFrame, "pregPat")
        self.notpregNo = self.findChild(QFrame, "notpregPat")
        self.lineChart = self.findChild(QFrame, "lineChart")
        self.monthlyVServ = self.findChild(QFrame, "visitsService")
        self.report_controller = MAReportController(self.servicesAvailed, self.lineChart, self.pregNo, self.notpregNo, self.monthlyVServ)
        self.report_controller.line_chart()

    def settings(self):
        self.clear()
        self.stackedWidget.setCurrentIndex(5)
        self.maPWidget = self.findChild(QWidget, "adminInfo")
        self.maPLname = self.findChild(QLabel, "adminPLname")
        self.maPFname = self.findChild(QLabel, "adminPFname")
        self.maPContact = self.findChild(QLabel, "adminPContact")

        self.map_controller = MAProfileController(self.maPWidget, self.maPLname, self.maPFname, self.maPContact, self.user_id)
        self.map_controller.set_username(self.username)
        self.map_controller.load_ma_info()

        self.editMA_button = self.findChild(QPushButton, "viewAdminProfile")
        if self.editMA_button:
            self.editMA_button.clicked.connect(self.map_controller.view_edit_dialog)
        
    def clear(self):
        for widget in self.stackedWidget.currentWidget().findChildren(QLineEdit):
            widget.clear()

    def logout(self):
        reply = QMessageBox.question(
            self,
            "Logout Confirmation",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            from Database import log_user_action
            from socket import gethostname, gethostbyname
            
            ip_address = gethostbyname(gethostname())
            log_user_action(self.user_id, 'LOGOUT', ip_address)
            
            self.close()
            from Login import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
    
    def set_active_button(self, active_button):
        for btn in [self.home_button, self.patients_button, self.appointments_button, self.files_button]:
            btn.setProperty("active", btn == active_button)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MidwifeAideMainWindow("Midwife", "staff_images/default_user.png")  # Pass a test image path
    window.show()
    sys.exit(app.exec_())