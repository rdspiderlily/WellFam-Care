from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QLineEdit, QPushButton, QCheckBox
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt 
import sys

from Admin_Main_Controller import AdminMainWindow
#from Midwife_Controller import MidwifeWindow
#from Aide_Controller import AideWindow

from Database import check_user_credentials, get_user_role, get_user_id

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("wfui/login.ui", self)

        self.setWindowTitle("WellFam Care")
        self.setWindowIcon(QIcon("wfpics/logo1.jpg"))
        self.setWindowFlags(Qt.Window)

        self.username_input = self.findChild(QLineEdit, "lineEditUsername")
        self.password_input = self.findChild(QLineEdit, "lineEditPassword")
        self.login_button = self.findChild(QPushButton, "signInButton")
        self.show_password_checkbox = self.findChild(QCheckBox, "checkBoxShowPassword")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)

        self.login_button.clicked.connect(self.check_login)
        
        self.main_window = None

    def check_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.")
            return

        try:
            if check_user_credentials(username, password):
                role = get_user_role(username)
                user_id = get_user_id(username)

                if role == "Admin":
                    if self.main_window is None:
                        self.main_window = AdminMainWindow(username, user_id)
                    self.main_window.show()
                    self.close()

                # elif role == "Midwife":
                #     self.main_window = MidwifeWindow()
                # elif role == "Nursing Aide":
                #     self.main_window = AideWindow()

                else:
                    QMessageBox.warning(self, "Login Error", "User role not recognized.")
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

        except Exception as e:
            QMessageBox.critical(self, "Unexpected Error", f"Something went wrong:\n{str(e)}")
    
    def toggle_password_visibility(self):
        if self.show_password_checkbox.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
