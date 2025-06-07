import bcrypt
import os
import shutil
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QMessageBox, QPushButton,
    QWidget, QLineEdit, QTableWidget,
    QHeaderView, QTableWidgetItem, QLabel, QFileDialog,
    QCheckBox, QDateEdit
)
from PyQt5 import uic
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt

from Database import connect_db, get_user_id

class AdminUserController:
    def __init__(self, tableWidUser: QTableWidget, searchUser: QLineEdit, admin_username):
        self.tableWidUser = tableWidUser
        self.selected_user_pic_path = None
        self.admin_username = admin_username
        self.admin_userID = get_user_id(admin_username)
        
        self.tableWidUser.cellClicked.connect(self.view_user_dialog)

        self.searchUser = searchUser
        self.searchUser.textChanged.connect(self.search_user)

        self.user_list()

    def user_list(self):
        self.tableWidUser.setRowCount(0)

        header = self.tableWidUser.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [0, 230, 230, 150, 130, 110, 118]
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)

        self.tableWidUser.setColumnHidden(0, True)
        self.tableWidUser.verticalHeader().setVisible(False)

        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT us.STAFF_ID, us.STAFF_LNAME, us.STAFF_FNAME, us.STAFF_CONTACT, us.STAFF_USN, r.ROLE_NAME, s.STATUS_NAME
                    FROM USER_STAFF us
                    JOIN USER_ROLE r ON us.ROLE_ID = r.ROLE_ID
                    JOIN USER_STATUS s ON us.STATUS_ID = s.STATUS_ID
                    WHERE us.STAFF_ISDELETED = FALSE AND r.ROLE_NAME IN ('Midwife', 'Nursing Aide')  
                """)
                rows = cur.fetchall()

                for row in rows:
                    row_position = self.tableWidUser.rowCount()
                    self.tableWidUser.insertRow(row_position)
                    for column, data in enumerate(row):
                        self.tableWidUser.setItem(row_position, column, QTableWidgetItem(str(data)))
            except Exception as e:
                QMessageBox.critical(self.tableWidUser, "Database Error", f"Error fetching users: {e}")
            finally:
                conn.close()

    def add_user_dialog(self):
        if hasattr(self, 'user_dialog') and self.user_dialog is not None:
            if self.user_dialog.isVisible():
                self.user_dialog.raise_()
                self.user_dialog.activateWindow()
                return
        else:
            self.user_dialog = QDialog()
            self.user_dialog.setAttribute(Qt.WA_DeleteOnClose)
            self.user_dialog.destroyed.connect(lambda: setattr(self, 'user_dialog', None))
            
            uic.loadUi("wfui/add_user.ui", self.user_dialog)
            self.user_dialog.setWindowTitle("Add New User")
            self.user_dialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))

            addUserWidget = self.user_dialog.findChild(QWidget, "widgetaddUser")
            self.pic_label = addUserWidget.findChild(QLabel, "labelUserPic")

            self.load_roles(addUserWidget.findChild(QComboBox, "userRole"))
            self.load_status(addUserWidget.findChild(QComboBox, "userStatus"))
            
            password_edit = addUserWidget.findChild(QLineEdit, "lineEditPassword")
            confirm_password_edit = addUserWidget.findChild(QLineEdit, "lineEditCPassword")

            toggle_password_checkbox = addUserWidget.findChild(QCheckBox, "showPass")
            
            if toggle_password_checkbox:
                toggle_password_checkbox.stateChanged.connect(
                    lambda: self.toggle_password_visibility(password_edit, confirm_password_edit, toggle_password_checkbox)
                )

            self.user_dialog.findChild(QPushButton, "pushBtnSaveUser").clicked.connect(lambda: self.save_user(addUserWidget, self.user_dialog))
            self.user_dialog.findChild(QPushButton, "pushBtnCancelUser").clicked.connect(self.user_dialog.reject)

            upload_btn = addUserWidget.findChild(QPushButton, "pushBtnUploadUserPic")
            remove_btn = addUserWidget.findChild(QPushButton, "pushBtnRemoveUserPic")

            if upload_btn:
                upload_btn.clicked.connect(self.browse_user_pic)
            if remove_btn:
                remove_btn.clicked.connect(lambda: self.remove_user_pic(self.pic_label))

        self.user_list()
        self.user_dialog.show()

    def load_roles(self, comboBox):
        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT ROLE_NAME FROM USER_ROLE WHERE ROLE_NAME IN ('Midwife', 'Nursing Aide')")
                roles = cur.fetchall()
                comboBox.clear()
                for role in roles:
                    comboBox.addItem(role[0])
            except Exception as e:
                print("Error loading roles:", e)
            finally:
                conn.close()
                
    def load_status(self, comboBox):
        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT STATUS_NAME FROM USER_STATUS")
                status = cur.fetchall()
                comboBox.clear()
                for role in status:
                    comboBox.addItem(role[0])
            except Exception as e:
                print("Error loading roles:", e)
            finally:
                conn.close()

    def browse_user_pic(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Select Picture", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            pixmap = QPixmap(file_path).scaled(100, 100)
            self.pic_label.setPixmap(pixmap)
            self.selected_user_pic_path = file_path
            
    def save_user_image(self, src_path):
        staff_images_dir = "staff_images"
        os.makedirs(staff_images_dir, exist_ok=True)

        file_name = os.path.basename(src_path)
        dest_path = os.path.join(staff_images_dir, file_name)

        shutil.copy(src_path, dest_path)
        return dest_path

    def remove_user_pic(self, pic_label):
        if pic_label:
            pic_label.clear()
        self.selected_user_pic_path = None
    
    def toggle_password_visibility(self, password_edit, confirm_password_edit, checkbox):
        if checkbox.isChecked():
            password_edit.setEchoMode(QLineEdit.Normal)
            confirm_password_edit.setEchoMode(QLineEdit.Normal)
        else:
            password_edit.setEchoMode(QLineEdit.Password)
            confirm_password_edit.setEchoMode(QLineEdit.Password)

    def save_user(self, addUserWidget, dialog):
        required_fields = [
            "lineEditUserLname", "lineEditUserFname", "lineEditUserContact", "userRole",
            "lineEditUsername", "lineEditPassword", "lineEditCPassword"
        ]

        for field in required_fields:
            widget = addUserWidget.findChild((QLineEdit, QComboBox, QDateEdit), field)
            if not widget:
                QMessageBox.warning(addUserWidget, "Input Error", f"Field {field} is required but not found.")
                return
            if isinstance(widget, QLineEdit) and not widget.text().strip():
                QMessageBox.warning(addUserWidget, "Input Error", "All fields are required.")
                return

        user_lname = addUserWidget.findChild(QLineEdit, "lineEditUserLname").text()
        user_fname = addUserWidget.findChild(QLineEdit, "lineEditUserFname").text()
        user_contact = addUserWidget.findChild(QLineEdit, "lineEditUserContact").text()
        user_username = addUserWidget.findChild(QLineEdit, "lineEditUsername").text()
        user_password = addUserWidget.findChild(QLineEdit, "lineEditPassword").text()
        user_cpass = addUserWidget.findChild(QLineEdit, "lineEditCPassword").text()
        user_roles = addUserWidget.findChild(QComboBox, "userRole").currentText()
        user_status = addUserWidget.findChild(QComboBox, "userStatus").currentText()

        if user_password != user_cpass:
            QMessageBox.warning(addUserWidget, "Password Mismatch", "Passwords do not match.")
            return

        hashed_password = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        if self.selected_user_pic_path:
            user_pic_path = self.save_user_image(self.selected_user_pic_path)
        else:  
            user_pic_path = None

        conn = connect_db()
        if not conn:
            QMessageBox.critical(addUserWidget, "Database Error", "Unable to connect to the database.")
            return

        try:
            cur = conn.cursor()
            cur.execute(""" 
                INSERT INTO USER_STAFF (
                    STAFF_LNAME, STAFF_FNAME, STAFF_CONTACT,
                    STAFF_USN, STAFF_PASS, ROLE_ID, STATUS_ID, STAFF_PIC_PATH, STAFF_CREATEDBY
                )
                VALUES (%s, %s, %s, %s, %s, 
                    (SELECT ROLE_ID FROM USER_ROLE WHERE ROLE_NAME = %s LIMIT 1), 
                    (SELECT STATUS_ID FROM USER_STATUS WHERE STATUS_NAME = %s LIMIT 1), %s, %s)
                RETURNING STAFF_ID
            """, (
                user_lname, user_fname, user_contact,
                user_username, hashed_password, user_roles, user_status, user_pic_path, self.admin_username
            ))

            staff_id = cur.fetchone()[0]
            conn.commit()

            new_row = [staff_id, user_lname, user_fname, user_contact, user_roles, user_status]
            self.insert_user_row(new_row)

            QMessageBox.information(addUserWidget, "Success", "User added successfully!")
            dialog.close()

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(addUserWidget, "Insert Error", f"Error adding user:\n{e}")
        finally:
            conn.close()

    def insert_user_row(self, new_row):
        row_position = self.tableWidUser.rowCount()
        self.tableWidUser.insertRow(row_position)
        for column, data in enumerate(new_row):
            self.tableWidUser.setItem(row_position, column, QTableWidgetItem(str(data)))

    def search_user(self, text):
        for row in range(self.tableWidUser.rowCount()):
            match = False
            for col in range(1, self.tableWidUser.columnCount()):
                item = self.tableWidUser.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.tableWidUser.setRowHidden(row, not match)

    def view_user_dialog(self, row, column):
        if hasattr(self, 'user_dialog') and self.user_dialog is not None:
            if self.user_dialog.isVisible():
                self.user_dialog.raise_()
                self.user_dialog.activateWindow()
                return
        else:
            staff_id_item = self.tableWidUser.item(row, 0)
            if not staff_id_item:
                return

            staff_id = staff_id_item.text()

            self.user_dialog = QDialog()
            self.user_dialog.setAttribute(Qt.WA_DeleteOnClose)
            self.user_dialog.destroyed.connect(lambda: setattr(self, 'user_dialog', None))
            
            uic.loadUi("wfui/view_edit_user.ui", self.user_dialog)
            self.user_dialog.setWindowTitle("View User Information")
            self.user_dialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))

            userWidget = self.user_dialog.findChild(QWidget, "widgetviewUser")
            self.pic_label = userWidget.findChild(QLabel, "labelUserPic")

            lname_edit = userWidget.findChild(QLineEdit, "lineEditUserLname")
            fname_edit = userWidget.findChild(QLineEdit, "lineEditUserFname")
            contact_edit = userWidget.findChild(QLineEdit, "lineEditUserContact")
            username_edit = userWidget.findChild(QLineEdit, "lineEditUsername")
            role_combo = userWidget.findChild(QComboBox, "userRole")
            status_combo = userWidget.findChild(QComboBox, "userStatus")
            password_edit = userWidget.findChild(QLineEdit, "lineEditPassword")
            confirm_password_edit = userWidget.findChild(QLineEdit, "lineEditCPassword")
            show_password_checkbox = userWidget.findChild(QCheckBox, "showPass")

            edit_btn = self.user_dialog.findChild(QPushButton, "pushBtnEditUser")
            save_btn = self.user_dialog.findChild(QPushButton, "pushBtnSaveUser")
            cancel_btn = self.user_dialog.findChild(QPushButton, "pushBtnCancelUser")
            trash_btn = self.user_dialog.findChild(QPushButton, "pushBtnTrashUser")
            upload_btn = self.user_dialog.findChild(QPushButton, "pushBtnUploadUserPic")
            remove_btn = self.user_dialog.findChild(QPushButton, "pushBtnRemoveUserPic")

            self.current_pic_path = None

            self.load_roles(role_combo)
            self.load_status(status_combo)

            conn = connect_db()
            if not conn:
                QMessageBox.critical(self.user_dialog, "Error", "Database connection failed.")
                return

            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT us.STAFF_LNAME, us.STAFF_FNAME, us.STAFF_CONTACT,
                        us.STAFF_USN, r.ROLE_NAME, s.STATUS_NAME, us.STAFF_PIC_PATH
                    FROM USER_STAFF us
                    JOIN USER_ROLE r ON us.ROLE_ID = r.ROLE_ID
                    JOIN USER_STATUS s ON us.STATUS_ID = s.STATUS_ID
                    WHERE us.STAFF_ID = %s
                """, (staff_id,))
                data = cur.fetchone()

                if not data:
                    QMessageBox.warning(self.user_dialog, "Not Found", "User not found.")
                    return

                lname_edit.setText(data[0])
                fname_edit.setText(data[1])
                contact_edit.setText(data[2])
                username_edit.setText(data[3])
                role_combo.setCurrentText(data[4])
                status_combo.setCurrentText(data[5])
                self.current_pic_path = data[6]

                if self.current_pic_path and os.path.exists(self.current_pic_path):
                    pixmap = QPixmap(self.current_pic_path).scaled(100, 100)
                    self.pic_label.setPixmap(pixmap)
                else:
                    self.pic_label.clear()

            except Exception as e:
                QMessageBox.critical(self.user_dialog, "Error", f"Database error: {e}")
                return
            finally:
                conn.close()

        for widget in [lname_edit, fname_edit, contact_edit, username_edit, password_edit, confirm_password_edit, role_combo, status_combo]:
            widget.setEnabled(False)
        password_edit.setEchoMode(QLineEdit.Password)
        confirm_password_edit.setEchoMode(QLineEdit.Password)
        upload_btn.setEnabled(False)
        remove_btn.setEnabled(False)
        show_password_checkbox.setEnabled(False)

        def toggle_edit_mode(enabled):
            for widget in [lname_edit, fname_edit, contact_edit, username_edit, password_edit, confirm_password_edit, role_combo, status_combo]:
                widget.setEnabled(enabled)
            upload_btn.setEnabled(enabled)
            remove_btn.setEnabled(enabled)
            show_password_checkbox.setEnabled(enabled)

        def cancel_changes():
            lname_edit.setText(data[0])
            fname_edit.setText(data[1])
            contact_edit.setText(data[2])
            username_edit.setText(data[3])
            role_combo.setCurrentText(data[4])
            status_combo.setCurrentText(data[5])
            password_edit.clear()
            confirm_password_edit.clear()
            toggle_edit_mode(False)

        def show_password_toggled(state):
            echo_mode = QLineEdit.Normal if state else QLineEdit.Password
            password_edit.setEchoMode(echo_mode)
            confirm_password_edit.setEchoMode(echo_mode)

        def upload_photo():
            file_path, _ = QFileDialog.getOpenFileName(self.user_dialog, "Select Photo", "", "Image Files (*.png *.jpg *.jpeg)")
            if file_path:
                pixmap = QPixmap(file_path).scaled(100, 100)
                self.pic_label.setPixmap(pixmap)
                self.current_pic_path = file_path

        def remove_photo():
            self.pic_label.clear()
            self.current_pic_path = ""

        def save_changes():
            new_lname = lname_edit.text().strip()
            new_fname = fname_edit.text().strip()
            new_contact = contact_edit.text().strip()
            new_username = username_edit.text().strip()
            new_password = password_edit.text()
            confirm_password = confirm_password_edit.text()
            new_role = role_combo.currentText()
            new_status = status_combo.currentText()

            if not all([new_lname, new_fname, new_contact, new_username]):
                QMessageBox.warning(self.user_dialog, "Validation", "Please fill in all required fields.")
                return

            if new_password or confirm_password:
                if new_password != confirm_password:
                    QMessageBox.warning(self.user_dialog, "Password Mismatch", "Passwords do not match.")
                    return

            conn = connect_db()
            if not conn:
                QMessageBox.critical(self.user_dialog, "Error", "Failed to connect to DB.")
                return

            try:
                cur = conn.cursor()

                cur.execute("SELECT STAFF_LNAME, STAFF_FNAME, STAFF_CONTACT, STAFF_USN, STAFF_PASS, STAFF_PIC_PATH, ROLE_ID, STATUS_ID FROM USER_STAFF WHERE STAFF_ID = %s", (staff_id,))
                data = cur.fetchone()

                update_fields = []
                update_values = []

                if new_lname != data[0]:
                    update_fields.append("STAFF_LNAME")
                    update_values.append(new_lname)

                if new_fname != data[1]:
                    update_fields.append("STAFF_FNAME")
                    update_values.append(new_fname)

                if new_contact != data[2]:
                    update_fields.append("STAFF_CONTACT")
                    update_values.append(new_contact)

                if new_username != data[3]:
                    update_fields.append("STAFF_USN")
                    update_values.append(new_username)
                    
                if new_password:
                    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    update_fields.append("STAFF_PASS")
                    update_values.append(hashed_password)

                cur.execute("SELECT ROLE_NAME FROM USER_ROLE WHERE ROLE_ID = %s", (data[6],))
                current_role = cur.fetchone()[0]
                if new_role != current_role:
                    cur.execute("SELECT ROLE_ID FROM USER_ROLE WHERE ROLE_NAME = %s", (new_role,))
                    new_role_id = cur.fetchone()[0]
                    update_fields.append("ROLE_ID")
                    update_values.append(new_role_id)
                
                cur.execute("SELECT STATUS_NAME FROM USER_STATUS WHERE STATUS_ID = %s", (data[7],))
                current_status = cur.fetchone()[0]
                if new_status != current_status:
                    cur.execute("SELECT STATUS_ID FROM USER_STATUS WHERE STATUS_NAME = %s", (new_status,))
                    new_status_id = cur.fetchone()[0]
                    update_fields.append("STATUS_ID")
                    update_values.append(new_status_id)

                image_path = self.current_pic_path

                if image_path and image_path != data[5]:
                    if not image_path.startswith("saved_images/"):
                        os.makedirs("saved_images", exist_ok=True)
                        new_path = os.path.join("saved_images", os.path.basename(image_path))
                        shutil.copy(image_path, new_path)
                        image_path = new_path
                    update_fields.append("STAFF_PIC_PATH")
                    update_values.append(image_path)

                if not update_fields:
                    QMessageBox.information(self.user_dialog, "No Changes", "No changes were made to the user info.")
                    return

                update_query = f"""
                    UPDATE USER_STAFF
                    SET {', '.join([f"{field} = %s" for field in update_fields])}
                    WHERE STAFF_ID = %s
                """
                update_values.append(staff_id)
                cur.execute(update_query, tuple(update_values))

                conn.commit()
                QMessageBox.information(self.user_dialog, "Updated", "User info saved successfully.")
                self.user_list()
                toggle_edit_mode(False)

            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self.user_dialog, "Error", str(e))
            finally:
                conn.close()

        def move_to_trash():
            confirm = QMessageBox.question(
                self.user_dialog, "Confirm Deletion", "Are you sure you want to move this user to trash?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                conn = connect_db()
                if conn:
                    try:
                        cur = conn.cursor()
                        cur.execute("UPDATE USER_STAFF SET STAFF_ISDELETED = TRUE WHERE STAFF_ID = %s", (staff_id,))
                        conn.commit()
                        QMessageBox.information(self.user_dialog, "Moved", "User moved to trash.")
                        self.user_list()
                        self.user_dialog.accept()
                    except Exception as e:
                        conn.rollback()
                        QMessageBox.critical(self.user_dialog, "Error", str(e))
                    finally:
                        conn.close()

        edit_btn.clicked.connect(lambda: toggle_edit_mode(True))
        cancel_btn.clicked.connect(cancel_changes)
        save_btn.clicked.connect(save_changes)
        trash_btn.clicked.connect(move_to_trash)
        upload_btn.clicked.connect(upload_photo)
        remove_btn.clicked.connect(remove_photo)
        show_password_checkbox.stateChanged.connect(show_password_toggled)

        self.user_dialog.show()

    def trashUser_list(self):
        if hasattr(self, 'trashDialog') and self.trashDialog is not None:
            if self.trashDialog.isVisible():
                self.trashDialog.raise_()
                self.trashDialog.activateWindow()
                return
        
        else:
            self.trashDialog = QDialog()
            self.trashDialog.setAttribute(Qt.WA_DeleteOnClose)
            self.trashDialog.destroyed.connect(lambda: setattr(self, 'trashDialog', None))
            
            uic.loadUi("wfui/trashUser.ui", self.trashDialog)
            self.trashDialog.setWindowTitle("Trash")
            self.trashDialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))
            
            self.searchTrash = self.trashDialog.findChild(QLineEdit, "lineEditSearchTrashUser")
            trashTable = self.trashDialog.findChild(QTableWidget, "tableWidgetTrashUser")
            
            if self.searchTrash:
                self.searchTrash.textChanged.connect(lambda: self.search_trash(text=self.searchTrash.text(), trashTable=trashTable))
                
            trashTable.setRowCount(0)
            
            header = trashTable.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Fixed)
            column_sizes = [0, 200, 200, 150, 150, 150]
            for i, size in enumerate(column_sizes):
                header.resizeSection(i, size)
            
            trashTable.setColumnHidden(0, True)
            trashTable.verticalHeader().setVisible(False)

            conn = connect_db()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT us.STAFF_ID, us.STAFF_LNAME, us.STAFF_FNAME, us.STAFF_CONTACT, r.ROLE_NAME, s.STATUS_NAME
                        FROM USER_STAFF us
                        JOIN USER_ROLE r ON us.ROLE_ID = r.ROLE_ID
                        JOIN USER_STATUS s ON us.STATUS_ID = s.STATUS_ID
                        WHERE us.STAFF_ISDELETED = TRUE AND r.ROLE_NAME IN ('Midwife', 'Nursing Aide')
                    """)
                    rows = cur.fetchall()

                    for row in rows:
                        row_position = trashTable.rowCount()
                        trashTable.insertRow(row_position)
                        for column, data in enumerate(row):
                            trashTable.setItem(row_position, column, QTableWidgetItem(str(data)))
                    
                    trashTable.cellClicked.connect(lambda row, col: self.restore_or_delete_user(row, col, trashTable))

                except Exception as e:
                    QMessageBox.critical(self.trashDialog, "Database Error", f"Error fetching trash data: {e}")
                finally:
                    conn.close()

        self.trashDialog.show()
            
    def search_trash(self, text, trashTable):
        for row in range(trashTable.rowCount()):
            match = False
            for col in range(1, trashTable.columnCount()): 
                item = trashTable.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            trashTable.setRowHidden(row, not match)

    def restore_or_delete_user(self, row, column, trashTable):
        if column == 1:
            staff_id = trashTable.item(row, 0).text()

            msg_box = QMessageBox(self.trashDialog)
            msg_box.setWindowTitle("Restore or Delete")
            msg_box.setText("Do you want to restore or permanently delete this user account?")
            msg_box.setIcon(QMessageBox.Question)

            restore_button = msg_box.addButton("Restore", QMessageBox.YesRole)
            delete_button = msg_box.addButton("Delete", QMessageBox.DestructiveRole)
            cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)

            msg_box.exec_()

            if msg_box.clickedButton() == restore_button:
                self.restore_user(staff_id)
            elif msg_box.clickedButton() == delete_button:
                self.delete_user(staff_id)

    def restore_user(self, staff_id):
        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("UPDATE USER_STAFF SET STAFF_ISDELETED = FALSE WHERE STAFF_ID = %s", (staff_id,))
                conn.commit()
                QMessageBox.information(self.trashDialog, "Restoration Success", "User Account has been restored successfully.")
                self.user_list()
                self.refresh_trash_table()  
            except Exception as e:
                QMessageBox.critical(self.trashDialog, "Restore Error", f"Error restoring user: {e}")
            finally:
                conn.close()

    def delete_user(self, staff_id):
        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM USER_STAFF WHERE STAFF_ID = %s", (staff_id,))
                conn.commit()
                QMessageBox.information(self.trashDialog, "Deletion Success", "User Account has been permanently deleted.")
                self.user_list()
                self.refresh_trash_table() 
            except Exception as e:
                QMessageBox.critical(self.trashDialog, "Deletion Error", f"Error deleting user: {e}")
            finally:
                conn.close()

    def refresh_trash_table(self):
        trashTable = self.trashDialog.findChild(QTableWidget, "tableWidgetTrashUser")
        trashTable.setRowCount(0)

        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT us.STAFF_ID, us.STAFF_LNAME, us.STAFF_FNAME, us.STAFF_CONTACT, r.ROLE_NAME, s.STATUS_NAME
                    FROM USER_STAFF us
                    JOIN USER_ROLE r ON us.ROLE_ID = r.ROLE_ID
                    JOIN USER_STATUS s ON us.STATUS_ID = s.STATUS_ID
                    WHERE us.STAFF_ISDELETED = TRUE AND r.ROLE_NAME IN ('Midwife', 'Nursing Aide')
                """)
                rows = cur.fetchall()

                for row in rows:
                    row_position = trashTable.rowCount()
                    trashTable.insertRow(row_position)
                    for column, data in enumerate(row):
                        trashTable.setItem(row_position, column, QTableWidgetItem(str(data)))

            except Exception as e:
                QMessageBox.critical(self.trashDialog, "Error", f"Failed to refresh trash:\n{e}")
            finally:
                conn.close()
