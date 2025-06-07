import bcrypt
import os
import shutil
from PyQt5.QtWidgets import (
    QDialog, QMessageBox, QPushButton, QInputDialog,
    QWidget, QLineEdit, QLabel, QFileDialog, QCheckBox
)
from PyQt5 import uic
from PyQt5.QtGui import QIcon, QPixmap

from Database import connect_db
from Database import log_audit

class AdminProfileController:
    def __init__(self, widget, lname_label, fname_label, contact_label, user_id):
        self.widget = widget
        self.lname_label = lname_label
        self.fname_label = fname_label
        self.contact_label = contact_label
        self.username = None
        self.current_pic_path = None
        self.user_id = user_id
        
        self.load_admin_info()

    def set_username(self, username):
        self.username = username

    def load_admin_info(self):
        if not self.username:
            return

        conn = connect_db()
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute(""" 
                SELECT s.STAFF_LNAME, s.STAFF_FNAME, s.STAFF_CONTACT, s.STAFF_PIC_PATH
                FROM USER_STAFF s
                JOIN USER_ROLE r ON s.ROLE_ID = r.ROLE_ID
                WHERE s.STAFF_USN = %s AND r.ROLE_NAME = 'Admin'
            """, (self.username,))
            result = cur.fetchone()

            if result:
                fname, lname, contact, pic_path = result
                self.fname_label.setText(fname)
                self.lname_label.setText(lname)
                self.contact_label.setText(contact)
                self.current_pic_path = pic_path

                pic_label = self.widget.findChild(QLabel, "labelAdminPic")
                if pic_label:
                    if pic_path and os.path.exists(pic_path):
                        pixmap = QPixmap(pic_path).scaled(100, 100)
                        pic_label.setPixmap(pixmap)
                    else:
                        pic_label.clear()
        finally:
            conn.close()

    def view_edit_dialog(self):
        if not self.username:
            QMessageBox.warning(None, "Missing Info", "Username not set.")
            return

        if hasattr(self, "profile_dialog") and self.profile_dialog is not None and self.profile_dialog.isVisible():
            self.profile_dialog.raise_()
            self.profile_dialog.activateWindow()
            return

        self.profile_dialog = QDialog()
        uic.loadUi("wfui/view_edit_admin.ui", self.profile_dialog)
        self.profile_dialog.setWindowTitle("Edit Admin Profile")
        self.profile_dialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))

        self.profile_dialog.finished.connect(lambda: setattr(self, "profile_dialog", None))

        widget = self.profile_dialog.findChild(QWidget, "widgetAdminProfile")
        pic_label = widget.findChild(QLabel, "labelAdminPic")
        username_edit = widget.findChild(QLineEdit, "lineEditUsername")
        lname_edit = widget.findChild(QLineEdit, "lineEditAdminLname")
        fname_edit = widget.findChild(QLineEdit, "lineEditAdminFname")
        contact_edit = widget.findChild(QLineEdit, "lineEditAdminContact")
        password_edit = widget.findChild(QLineEdit, "lineEditPassword")
        confirm_password_edit = widget.findChild(QLineEdit, "lineEditCPassword")
        show_pass_checkbox = widget.findChild(QCheckBox, "showPass")
        upload_btn = widget.findChild(QPushButton, "pushBtnUploadAdminPic")
        remove_btn = widget.findChild(QPushButton, "pushBtnRemoveAdminPic")
        save_btn = self.profile_dialog.findChild(QPushButton, "pushBtnSaveAdmin")
        cancel_btn = self.profile_dialog.findChild(QPushButton, "pushBtnCancelAdmin")
        edit_btn = self.profile_dialog.findChild(QPushButton, "pushBtnEditAdmin")

        input_fields = [username_edit, lname_edit, fname_edit, contact_edit, password_edit, confirm_password_edit]

        for field in input_fields:
            if field:
                field.setReadOnly(True)
        upload_btn.setEnabled(False)
        remove_btn.setEnabled(False)
        show_pass_checkbox.setEnabled(False)

        conn = connect_db()
        if not conn:
            QMessageBox.critical(self.profile_dialog, "Error", "Failed to connect to database.")
            return

        try:
            cur = conn.cursor()
            cur.execute(""" 
                SELECT STAFF_USN, STAFF_LNAME, STAFF_FNAME, STAFF_CONTACT, STAFF_PIC_PATH
                FROM USER_STAFF
                WHERE STAFF_USN = %s
            """, (self.username,))
            data = cur.fetchone()
            if not data:
                QMessageBox.warning(self.profile_dialog, "Not Found", "Admin not found.")
                return

            if username_edit: username_edit.setText(data[0])
            if lname_edit: lname_edit.setText(data[1])
            if fname_edit: fname_edit.setText(data[2])
            if contact_edit: contact_edit.setText(data[3])
            self.current_pic_path = data[4]

            if self.current_pic_path and os.path.exists(self.current_pic_path):
                pic_label.setPixmap(QPixmap(self.current_pic_path).scaled(100, 100))
            else:
                pic_label.clear()
        finally:
            conn.close()

        def toggle_password_visibility(state):
            mode = QLineEdit.Normal if state else QLineEdit.Password
            password_edit.setEchoMode(mode)
            confirm_password_edit.setEchoMode(mode)

        def enable_editing():
            for field in input_fields:
                field.setReadOnly(False)
            upload_btn.setEnabled(True)
            remove_btn.setEnabled(True)
            show_pass_checkbox.setEnabled(True)
            edit_btn.setEnabled(False)

        def disable_editing():
            for field in input_fields:
                field.setReadOnly(True)
            password_edit.clear()
            confirm_password_edit.clear()
            upload_btn.setEnabled(False)
            remove_btn.setEnabled(False)
            show_pass_checkbox.setEnabled(False)
            edit_btn.setEnabled(True)

        def upload_photo():
            file_path, _ = QFileDialog.getOpenFileName(self.profile_dialog, "Select Photo", "", "Images (*.png *.jpg *.jpeg)")
            if file_path:
                pic_label.setPixmap(QPixmap(file_path).scaled(100, 100))
                self.current_pic_path = file_path

        def remove_photo():
            pic_label.clear()
            self.current_pic_path = ""

        def save_changes():
            lname = lname_edit.text().strip()
            fname = fname_edit.text().strip()
            contact = contact_edit.text().strip()
            password = password_edit.text()
            confirm = confirm_password_edit.text()

            if not all([lname, fname, contact]):
                QMessageBox.warning(self.profile_dialog, "Validation", "All fields must be filled.")
                return

            if password and password != confirm:
                QMessageBox.warning(self.profile_dialog, "Validation", "Passwords do not match.")
                return
            
            current_password, ok = QInputDialog.getText(
                self.profile_dialog,
                "Password Verification",
                "Enter your current password to save changes:",
                QLineEdit.Password
            )
            
            if not ok:
                return  
                
            if not current_password:
                QMessageBox.warning(self.profile_dialog, "Validation", "Please enter your current password to save changes.")
                return

            # hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode() if password else None

            conn = connect_db()
            if not conn:
                QMessageBox.critical(self.profile_dialog, "Error", "Database connection failed.")
                return

            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT STAFF_PASS FROM USER_STAFF WHERE STAFF_USN = %s
                """, (self.username,))
                result = cur.fetchone()
                
                if not result or not bcrypt.checkpw(current_password.encode(), result[0].encode()):
                    QMessageBox.warning(self.profile_dialog, "Error", "Incorrect password.")
                    return
                    
                # Password verified - proceed with update
                hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode() if password else None
                
                update_fields = "STAFF_LNAME = %s, STAFF_FNAME = %s, STAFF_CONTACT = %s"
                values = [lname, fname, contact]

                if hashed_pw:
                    update_fields += ", STAFF_PASS = %s"
                    values.append(hashed_pw)

                if self.current_pic_path:
                    if not self.current_pic_path.startswith("staff_images/"):
                        os.makedirs("staff_images", exist_ok=True)
                        new_path = os.path.join("staff_images", os.path.basename(self.current_pic_path))
                        shutil.copy(self.current_pic_path, new_path)
                        self.current_pic_path = new_path
                    update_fields += ", STAFF_PIC_PATH = %s"
                    values.append(self.current_pic_path)

                values.append(self.username)

                cur.execute(f"""
                    UPDATE USER_STAFF SET {update_fields}
                    WHERE STAFF_USN = %s
                """, tuple(values))
                
                cur.execute("SELECT STAFF_ID FROM USER_STAFF WHERE STAFF_USN = %s", (self.username,))
                staff_id = cur.fetchone()[0]
                log_audit(self.user_id, 'UPDATE', 'USER PROFILE', staff_id)

                conn.commit()
                QMessageBox.information(self.profile_dialog, "Success", "Profile updated.")
                self.fname_label.setText(fname)
                self.lname_label.setText(lname)
                self.contact_label.setText(contact)
                disable_editing()
                self.profile_dialog.accept()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self.profile_dialog, "Error", str(e))
            finally:
                conn.close()

        show_pass_checkbox.stateChanged.connect(toggle_password_visibility)
        upload_btn.clicked.connect(upload_photo)
        remove_btn.clicked.connect(remove_photo)
        save_btn.clicked.connect(save_changes)
        cancel_btn.clicked.connect(lambda: disable_editing() or self.profile_dialog.reject())
        edit_btn.clicked.connect(enable_editing)

        self.profile_dialog.exec_()
