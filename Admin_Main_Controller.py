from PyQt5.QtWidgets import (
    QApplication, QDialog, QMessageBox, QStackedWidget, 
    QPushButton, QLabel, QCalendarWidget, QLineEdit, 
    QTableWidget, QWidget
)
from PyQt5 import uic
from PyQt5.QtGui import QIcon, QPixmap
import sys
import os

from Admin_Controllers.Admin_Dashboard import AdminDashboardController
from Admin_Controllers.Admin_Patient import AdminPatientController
from Admin_Controllers.Admin_Appointment import AdminAppointmentController
from Admin_Controllers.Admin_Staff import AdminUserController
from Admin_Controllers.Admin_Settings import AdminProfileController

from Database import connect_db

class AdminMainWindow(QDialog):
    def __init__(self, username, user_id, pic=None):
        super().__init__()

        self.username = username
        self.user_id = user_id
        self.pic = pic or "staff_images/default_user.png"
        
        uic.loadUi("wfui/admin_dashboard.ui", self)
        self.setWindowTitle("WellFam Care")
        self.setWindowIcon(QIcon("wfpics/logo1.jpg"))

        self.admin_username = self.findChild(QLabel, "adminUName")
        if self.admin_username:
            self.admin_username.setText(self.username)

        self.admin_pic = self.findChild(QLabel, "userPic")
        if self.admin_pic:
            image_path = self.get_profile_image_path(self.username)
            self.set_profile_picture(image_path)
        else:
            print("QLabel for profile picture not found!")

        
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.home_button = self.findChild(QPushButton, "pushBtnHome")
        self.patients_button = self.findChild(QPushButton, "pushBtnPatient")
        self.appointments_button = self.findChild(QPushButton, "pushBtnAppointments")
        self.files_button = self.findChild(QPushButton, "pushBtnFiles")
        self.staff_button = self.findChild(QPushButton, "pushBtnStaffs")
        self.report_button = self.findChild(QPushButton, "pushBtnReports")
        self.settings_button = self.findChild(QPushButton, "pushBtnSettings")

        self.home_button.clicked.connect(self.dashboard)
        self.patients_button.clicked.connect(self.patient)
        self.appointments_button.clicked.connect(self.appointment)
        self.files_button.clicked.connect(self.files)
        self.staff_button.clicked.connect(self.staff)
        self.report_button.clicked.connect(self.report)
        self.settings_button.clicked.connect(self.settings)

        self.logout_button = self.findChild(QPushButton, "pushBtnLogout")
        if self.logout_button:
            self.logout_button.clicked.connect(self.logout)

        self.patient()
        self.dashboard()

    def get_profile_image_path(self, username):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT STAFF_PIC_PATH FROM USER_STAFF WHERE STAFF_USN = %s", (username,))
            result = cursor.fetchone()
            conn.close()

            if result and result[0] and os.path.exists(result[0]):
                return result[0]
            else:
                return "staff_images/default_user.png"

        except Exception as e:
            return "staff_images/default_user.png"

    def set_profile_picture(self, image_path):
        if not os.path.exists(image_path) or not os.path.isfile(image_path):
            image_path = "staff_images/default_user.png"

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            image_path = "staff_images/default_user.png"
            pixmap = QPixmap(image_path)

        if pixmap.isNull():
            return

        self.admin_pic.setFixedSize(130, 120)
        scaled_pixmap = pixmap.scaled(
            self.admin_pic.width(),
            self.admin_pic.height(),
            aspectRatioMode=1
        )
        self.admin_pic.setPixmap(scaled_pixmap)

    def dashboard(self):
        self.stackedWidget.setCurrentIndex(0)
        self.set_active_button(self.home_button)
        
        self.btnAppointments = self.findChild(QPushButton, "btnToApp")
        if self.btnAppointments:
            self.btnAppointments.clicked.connect(self.appointment)
            
        self.tableWidQueue = self.findChild(QTableWidget, "tableWidQueue")
        self.tableWidMonApp = self.findChild(QTableWidget, "tableWidMonApp")
        self.time_label = self.findChild(QLabel, "timeLabel")
        self.calendar_widget = self.findChild(QCalendarWidget, "adminCalendar")
        self.total_pat = self.findChild(QLabel, "NoPats")
        self.total_app = self.findChild(QLabel, "NoApps")
        self.greeting_label = self.findChild(QLabel, "greetingLabel")
        self.dashboard_controller = AdminDashboardController(
            self.tableWidQueue, self.tableWidMonApp, self.time_label, 
            self.calendar_widget, self.total_pat, self.total_app, self.greeting_label
        )

    def patient(self):
        self.clear()
        self.stackedWidget.setCurrentIndex(1)
        self.set_active_button(self.patients_button)
        self.tableWidPat = self.findChild(QTableWidget, "tableWidgetPat")
        self.searchPat = self.findChild(QLineEdit, "lineEditSearchPat")
        self.patient_controller = AdminPatientController(self.tableWidPat, self.searchPat)

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
        self.appointment_controller = AdminAppointmentController(self.tableWidApp, self.searchApp)
        
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
        self.tableWidFolder = self.findChild(QTableWidget, "")

    def staff(self):
        self.clear()
        self.stackedWidget.setCurrentIndex(4)
        self.set_active_button(self.staff_button)
        self.tableWidUser = self.findChild(QTableWidget, "tableWidgetStaff")
        self.searchUser = self.findChild(QLineEdit, "lineEditSearchStaff")
        self.user_controller = AdminUserController(self.tableWidUser, self.searchUser, self.user_id)

        self.addUser_button = self.findChild(QPushButton, "pushBtnAddStaff")
        if self.addUser_button:
            self.addUser_button.clicked.connect(self.user_controller.add_user_dialog)

        self.trashUser_button = self.findChild(QPushButton, "pushBtnTrashUser")
        if self.trashUser_button:
            self.trashUser_button.clicked.connect(self.user_controller.trashUser_list)

    def report(self):
        self.clear()
        self.stackedWidget.setCurrentIndex(5)
        self.set_active_button(self.report_button)

    def settings(self):
        self.clear()
        self.stackedWidget.setCurrentIndex(6)
        self.adminPWidget = self.findChild(QWidget, "adminInfo")
        self.adminPLname = self.findChild(QLabel, "adminPLname")
        self.adminPFname = self.findChild(QLabel, "adminPFname")
        self.adminPContact = self.findChild(QLabel, "adminPContact")

        self.adminp_controller = AdminProfileController(self.adminPWidget, self.adminPLname, self.adminPFname, self.adminPContact)
        self.adminp_controller.set_username(self.username)
        self.adminp_controller.load_admin_info()

        self.editAdmin_button = self.findChild(QPushButton, "viewAdminProfile")
        if self.editAdmin_button:
            self.editAdmin_button.clicked.connect(self.adminp_controller.view_edit_dialog)

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
            self.close()
            from Login import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
    
    def set_active_button(self, active_button):
        for btn in [self.home_button, self.patients_button, self.appointments_button, self.files_button, self.staff_button, self.report_button]:
            btn.setProperty("active", btn == active_button)
            btn.style().unpolish(btn)
            btn.style().polish(btn)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdminMainWindow("Admin", "staff_images/default_user.png")  # Pass a test image path
    window.show()
    sys.exit(app.exec_())
