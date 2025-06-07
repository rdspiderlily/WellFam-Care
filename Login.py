from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QLineEdit, QPushButton, QCheckBox
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt 
import sys
import os

from Admin_Main_Controller import AdminMainWindow
from MidwifeAide_Main_Controller import MidwifeAideMainWindow

from Database import connect_db, check_user_credentials, get_user_role, get_user_id

# Add this function at the top of your file
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        ui_path = resource_path('wfui/login.ui')
        uic.loadUi(ui_path, self)

        self.setWindowTitle("WellFam Care")
        self.setWindowIcon(QIcon(resource_path("wfpics/logo1.jpg")))
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
        
        from Database import check_login_attempts
        lock_message = check_login_attempts(username)
        if lock_message:
            QMessageBox.warning(self, "Account Locked", lock_message)
            return

        try:
            if check_user_credentials(username, password):
                from Database import reset_attempts, log_user_action
                reset_attempts(username)
                
                role = get_user_role(username)
                user_id = get_user_id(username)
                
                from Database import log_user_action
                log_user_action(user_id, 'LOGIN')

                if role == "Admin":
                    try:
                        self.main_window = AdminMainWindow(username, user_id)  # if it requires these
                        self.main_window.show()
                        self.close()
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to load Admin window:\n{e}")

                elif role == "Midwife":
                    try:
                        self.main_window = MidwifeAideMainWindow(username, user_id)  # if it requires these
                        self.main_window.show()
                        self.close()
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to load Midwife window:\n{e}")
                
                elif role == "Nursing Aide":
                    try:
                        self.main_window = MidwifeAideMainWindow(username, user_id)  # if it requires these
                        self.main_window.show()
                        self.close()
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to load Nursing Aide window:\n{e}")

                else:
                    QMessageBox.warning(self, "Login Error", "User role not recognized.")
            else:
                from Database import record_failed_attempt
                record_failed_attempt(username)
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
    
    test_conn = connect_db()
    if not test_conn:
        QMessageBox.critical(None, "Database Error", "Could not connect to the database.\nPlease check your db_config.py or network settings.")
        sys.exit()
    else:
        test_conn.close()
    
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
