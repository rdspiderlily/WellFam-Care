from PyQt5.QtWidgets import (
    QComboBox, QDialog, QMessageBox, QPushButton,
    QWidget, QLineEdit, QTableWidget, QLabel,
    QHeaderView, QTableWidgetItem, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from datetime import datetime
import os
import shutil
import webbrowser
import platform
from PyQt5 import uic
from Database import connect_db
from Database import log_audit

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.txt', '.jpg', '.jpeg', '.png'}
UPLOAD_DIRECTORY = 'uploaded_files'


class AdminFilesController:
    def __init__(self, tableWidFiles: QTableWidget, searchFiles: QLineEdit, sortFilesCombo: QComboBox, user_id):
        self.conn = connect_db()
        self.tableWidFiles = tableWidFiles
        self.searchFiles = searchFiles
        self.sortFilesCombo = sortFilesCombo
        self.user_id = user_id
        self.fileDialog = None
        self.viewImage = None

        try:
            self.tableWidFiles.cellClicked.connect(self.handle_view_file)
        except TypeError:
            pass

        self.searchFiles.textChanged.connect(self.search_file)
        self.sortFilesCombo.currentTextChanged.connect(self.sort_file_list)

        self.load_file_list()
        
    def sort_file_list(self, sort_option):
        self.sortFilesCombo.setCurrentIndex(0)

        sort_map = {
            "Date Uploaded (Ascending)": "F.FILE_DATE_UPLOADED ASC",
            "Date Uploaded (Descending)": "F.FILE_DATE_UPLOADED DESC",
            "File Name (A-Z)": "F.FILE_NAME ASC",
            "File Name (Z-A)": "F.FILE_NAME DESC",
            "Category (A-Z)": "FC.FILE_CAT_NAME ASC",
            "File Type (A-Z)": "FT.FILE_TYPE_NAME ASC",
            "Uploaded By (A-Z)": "U.STAFF_LNAME ASC, U.STAFF_FNAME ASC",
        }

        sort_clause = sort_map.get(sort_option, "F.FILE_DATE_UPLOADED DESC")

        try:
            self.tableWidFiles.setRowCount(0)
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT 
                    F.FILE_ID,
                    F.FILE_NAME,
                    FC.FILE_CAT_NAME,
                    F.FILE_DATE_UPLOADED,
                    FT.FILE_TYPE_NAME,
                    F.FILE_SIZE,
                    CONCAT(U.STAFF_LNAME, ', ', U.STAFF_FNAME) AS UPLOADED_BY
                FROM FILE_UPLOAD F
                LEFT JOIN USER_STAFF U ON F.STAFF_ID = U.STAFF_ID
                LEFT JOIN FILE_TYPE FT ON F.FILE_TYPE_ID = FT.FILE_TYPE_ID
                LEFT JOIN FILE_CATEGORY FC ON F.FILE_CAT_ID = FC.FILE_CAT_ID
                WHERE F.FILE_ISDELETED = FALSE
                ORDER BY {sort_clause}
            """)
            rows = cursor.fetchall()

            def format_file_size(size_bytes):
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 ** 2:
                    return f"{size_bytes / 1024:.2f} KB"
                elif size_bytes < 1024 ** 3:
                    return f"{size_bytes / (1024 ** 2):.2f} MB"
                else:
                    return f"{size_bytes / (1024 ** 3):.2f} GB"

            for row_data in rows:
                row_pos = self.tableWidFiles.rowCount()
                self.tableWidFiles.insertRow(row_pos)
                for col, value in enumerate(row_data):
                    if col == 3:  # Timestamp
                        if value:
                            if isinstance(value, str):
                                try:
                                    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                                except ValueError:
                                    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                            else:
                                dt = value  
                            value = dt.strftime("%m-%d-%Y %I:%M %p")
                    elif col == 5:  # File size
                        value = format_file_size(value or 0)
                    elif value is None:
                        value = ""
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.tableWidFiles.setItem(row_pos, col, item)

            self.tableWidFiles.clearSelection()
            self.tableWidFiles.scrollToTop()

        except Exception as e:
            QMessageBox.critical(None, "Database Error", f"Failed to sort files: {e}")

    def load_file_list(self):
        self.tableWidFiles.setRowCount(0)
        
        header = self.tableWidFiles.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [0, 300, 208, 135, 50, 80, 195]  # Added column for category name
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)

        self.tableWidFiles.setColumnHidden(0, True)  # Hide FILE_ID
        self.tableWidFiles.verticalHeader().setVisible(False)

        def format_file_size(size_bytes):
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 ** 2:
                return f"{size_bytes / 1024:.2f} KB"
            elif size_bytes < 1024 ** 3:
                return f"{size_bytes / (1024 ** 2):.2f} MB"
            else:
                return f"{size_bytes / (1024 ** 3):.2f} GB"

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    F.FILE_ID,
                    F.FILE_NAME,
                    FC.FILE_CAT_NAME,
                    F.FILE_DATE_UPLOADED,
                    FT.FILE_TYPE_NAME,
                    F.FILE_SIZE,
                    CONCAT(U.STAFF_LNAME, ', ', U.STAFF_FNAME) AS UPLOADED_BY
                FROM FILE_UPLOAD F
                LEFT JOIN USER_STAFF U ON F.STAFF_ID = U.STAFF_ID
                LEFT JOIN FILE_TYPE FT ON F.FILE_TYPE_ID = FT.FILE_TYPE_ID
                LEFT JOIN FILE_CATEGORY FC ON F.FILE_CAT_ID = FC.FILE_CAT_ID
                WHERE F.FILE_ISDELETED = FALSE
                ORDER BY F.FILE_DATE_UPLOADED DESC
            """)
            rows = cursor.fetchall()
            
            for row_data in rows:
                row_pos = self.tableWidFiles.rowCount()
                self.tableWidFiles.insertRow(row_pos)
                for col, value in enumerate(row_data):
                    if col == 3:  # Timestamp
                        if value:
                            if isinstance(value, str):
                                try:
                                    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                                except ValueError:
                                    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                            else:
                                dt = value  
                            value = dt.strftime("%m-%d-%Y %I:%M %p")
                    if col == 5:  # File size
                        value = format_file_size(value or 0)
                    elif value is None:
                        value = ""
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.tableWidFiles.setItem(row_pos, col, item)
            
            self.tableWidFiles.clearSelection()
            self.tableWidFiles.scrollToTop()

        except Exception as e:
            QMessageBox.critical(None, "Database Error", f"Failed to load files: {e}")

    def upload_file_dialog(self):
        if self.fileDialog and self.fileDialog.isVisible():
            self.fileDialog.raise_()
            self.fileDialog.activateWindow()
            return

        self.fileDialog = QDialog()
        self.fileDialog.setAttribute(Qt.WA_DeleteOnClose)
        self.fileDialog.destroyed.connect(lambda: setattr(self, 'fileDialog', None))

        uic.loadUi("wfui/uploadFile.ui", self.fileDialog)
        self.fileDialog.setWindowTitle("Upload File/Documents")
        self.fileDialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))

        uploadFileWidget = self.fileDialog.findChild(QWidget, "widgetUploadFile")

        upload_file_btn = self.fileDialog.findChild(QPushButton, "btnUploadFile")
        if upload_file_btn:
            upload_file_btn.clicked.connect(self.upload_file)

        select_patient_btn = self.fileDialog.findChild(QPushButton, "btnSearchPatient")
        if select_patient_btn:
            select_patient_btn.clicked.connect(lambda: self.open_select_patient_dialog(uploadFileWidget))

        comboCategory = uploadFileWidget.findChild(QComboBox, "comboBoxCategory")
        if comboCategory:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT FILE_CAT_ID, FILE_CAT_NAME FROM FILE_CATEGORY ORDER BY FILE_CAT_NAME")
                cat_list = cursor.fetchall()
                comboCategory.clear()
                comboCategory.addItem("-- Select Category --", -1)
                for cat_id, name in cat_list:
                    comboCategory.addItem(name, cat_id)
            except Exception as e:
                QMessageBox.warning(self.fileDialog, "Warning", f"Failed to load categories: {e}")

        save_button = self.fileDialog.findChild(QPushButton, "confirmUploadBtn")
        if save_button:
            save_button.clicked.connect(lambda: self.confirm_upload_file(uploadFileWidget))

        cancel_button = self.fileDialog.findChild(QPushButton, "pushBtnCancelUpload")
        if cancel_button:
            cancel_button.clicked.connect(self.fileDialog.reject)

        self.fileDialog.exec_()

    def confirm_upload_file(self, uploadWidget):
        comboCategory = uploadWidget.findChild(QComboBox, "comboBoxCategory")
        if not comboCategory:
            QMessageBox.warning(self.fileDialog, "Upload File", "Category selector not found.")
            return
        category_id = comboCategory.currentData()
        if category_id == -1 or category_id is None:
            QMessageBox.warning(self.fileDialog, "Upload File", "Please select a valid category.")
            return

        if not hasattr(self, 'selected_file_path') or not self.selected_file_path:
            QMessageBox.warning(self.fileDialog, "Upload File", "Please select a file to upload first.")
            return

        if not os.path.exists(UPLOAD_DIRECTORY):
            os.makedirs(UPLOAD_DIRECTORY)

        filename = os.path.basename(self.selected_file_path)
        dest_path = os.path.join(UPLOAD_DIRECTORY, filename)
        try:
            shutil.copy2(self.selected_file_path, dest_path)
            file_size = os.path.getsize(dest_path)
            
            file_ext = os.path.splitext(filename)[1].lower()
            
            cursor = self.conn.cursor()

            # Look up the corresponding FILE_TYPE_ID
            cursor.execute("SELECT FILE_TYPE_ID FROM FILE_TYPE WHERE LOWER(FILE_TYPE_NAME) = %s", (file_ext[1:],))  # remove the dot
            result = cursor.fetchone()
            if not result:
                QMessageBox.warning(self.fileDialog, "Upload File", f"File type '{file_ext}' is not registered in the FILE_TYPE table.")
                return

            file_type_id = result[0]

            cursor.execute("""
                INSERT INTO FILE_UPLOAD (FILE_NAME, FILE_DATE_UPLOADED, FILE_PATH, STAFF_ID, FILE_SIZE, FILE_CAT_ID, FILE_TYPE_ID, FILE_ISDELETED)
                VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, FALSE)
            """, (filename, dest_path, self.user_id, file_size, category_id, file_type_id))
            self.conn.commit()
            
            log_audit(self.user_id, 'UPLOADED', 'FILE', file_type_id) 

            QMessageBox.information(self.fileDialog, "Upload File", "File uploaded successfully.")
            self.fileDialog.accept()
            self.load_file_list()
        except Exception as e:
            QMessageBox.critical(self.fileDialog, "Upload File", f"Failed to upload file: {e}")

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

                patLDialog.accept()
            except Exception as e:
                QMessageBox.warning(patLDialog, "Error", f"Failed to select patient: {e}")

        tableWidPatA.cellClicked.connect(handle_patient_selection)

        def search_pat():
            text = searchPatApp.text().lower()
            for r in range(tableWidPatA.rowCount()):
                match = False
                for c in range(tableWidPatA.columnCount()):
                    item = tableWidPatA.item(r, c)
                    if item and text in item.text().lower():
                        match = True
                        break
                tableWidPatA.setRowHidden(r, not match)

        searchPatApp.textChanged.connect(search_pat)

        patLDialog.exec_()

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Select File to Upload", "", 
                                                   "Documents (*.pdf *.docx *.xlsx *.txt);;Images (*.jpg *.jpeg *.png)")
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            QMessageBox.warning(None, "Upload File", f"File type '{ext}' is not allowed.")
            return

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        file_name_lineedit = self.fileDialog.findChild(QLineEdit, "lineEditSelectedFile")
        if file_name_lineedit:
            file_name_lineedit.setText(base_name)

        self.selected_file_path = file_path
        QMessageBox.information(None, "Upload File", f"Selected file: {os.path.basename(file_path)}")

    def search_file(self, text):
        text = text.lower()
        for row in range(self.tableWidFiles.rowCount()):
            match = False
            for col in range(1, self.tableWidFiles.columnCount()):  # Skip hidden ID column
                item = self.tableWidFiles.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.tableWidFiles.setRowHidden(row, not match)

    def handle_view_file(self, row, column):
        file_id_item = self.tableWidFiles.item(row, 0)
        if not file_id_item:
            return

        file_id = int(file_id_item.text())
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT FILE_NAME, FILE_PATH FROM FILE_UPLOAD WHERE FILE_ID = %s", (file_id,))
            result = cursor.fetchone()

            if result:
                file_name, file_path = result

                if not os.path.exists(file_path):
                    QMessageBox.warning(self, "File Not Found", f"The file '{file_name}' does not exist.")
                    return

                msg_box = QMessageBox()
                msg_box.setWindowIcon(QIcon("wfpics/logo1.jpg")) 
                msg_box.setWindowTitle("File Action")
                msg_box.setText(f"How would you like to proceed with the file: '{file_name}'?")
                view_btn = msg_box.addButton("View", QMessageBox.AcceptRole)
                delete_btn = msg_box.addButton("Trash", QMessageBox.DestructiveRole)
                cancel_btn = msg_box.addButton("Cancel", QMessageBox.RejectRole)
                msg_box.exec_()

                if msg_box.clickedButton() == view_btn:
                    self.view_file_by_type(file_path)

                elif msg_box.clickedButton() == delete_btn:
                    self.move_file_to_trash(file_id)

        except Exception as e:
            print("Error opening file:", e)
    
    def move_file_to_trash(self, file_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE FILE_UPLOAD SET FILE_ISDELETED = TRUE WHERE FILE_ID = %s", (file_id,))
            self.conn.commit()
            QMessageBox.information(self.tableWidFiles, "File Trashed", "The file has been moved to the trash.")
            self.load_file_list()
        except Exception as e:
            QMessageBox.critical(self.tableWidFiles, "Error", f"Failed to move file to trash: {e}")
        finally:
            cursor.close()

    def view_file_by_type(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()

        if ext in ['.png', '.jpg', '.jpeg', '.bmp']:
            self.view_image(file_path)

        elif ext == '.pdf':
            self.view_pdf(file_path)

        else:
            self.open_with_default_app(file_path)

    def view_image(self, path):
        if getattr(self, 'viewImage', None) and self.viewImage.isVisible():
            self.viewImage.raise_()
            self.viewImage.activateWindow()
            return

        self.viewImage = QDialog()
        self.viewImage.setAttribute(Qt.WA_DeleteOnClose)
        self.viewImage.destroyed.connect(lambda: setattr(self, 'viewImage', None))
        uic.loadUi("wfui/viewImageFile.ui", self.viewImage)
        self.viewImage.setWindowTitle("Image Viewer")
        self.viewImage.setWindowIcon(QIcon("wfpics/logo1.jpg"))

        label = self.viewImage.findChild(QLabel, "labelImage")
        pixmap = QPixmap(path)
        label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.viewImage.exec_()

    def view_pdf(self, path):
        webbrowser.open(f'file:///{os.path.abspath(path)}')

    def open_with_default_app(self, path):
        try:
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':  # macOS
                import subprocess
                subprocess.call(['open', path])
            else:  # Linux
                import subprocess
                subprocess.call(['xdg-open', path])
        except Exception as e:
            print(f"Failed to open file: {e}")
    
    def file_trash_dialog(self):
        if hasattr(self, 'trashDialog') and self.trashDialog is not None:
            if self.trashDialog.isVisible():
                self.trashDialog.raise_()
                self.trashDialog.activateWindow()
                return
        else:
            self.trashDialog = QDialog()
            self.trashDialog.setAttribute(Qt.WA_DeleteOnClose)
            self.trashDialog.destroyed.connect(lambda: setattr(self, 'trashDialog', None))

            uic.loadUi("wfui/trashFile.ui", self.trashDialog)
            self.trashDialog.setWindowTitle("Trash")
            self.trashDialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))

            trashAppWidget = self.trashDialog.findChild(QWidget, "widgetFileTrash")
            if not trashAppWidget:
                print("ERROR: widgetFileTrash not found!")
                return

            self.searchTrash = trashAppWidget.findChild(QLineEdit, "lineEditSearchFileTrash")
            self.trashTable = trashAppWidget.findChild(QTableWidget, "tableWidgetFileTrash")

            header = self.trashTable.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Fixed)
            column_sizes = [0, 250, 200, 150, 150]
            for i, size in enumerate(column_sizes):
                header.resizeSection(i, size)

            self.trashTable.setColumnHidden(0, True)
            self.trashTable.verticalHeader().setVisible(False)

            self.searchTrash.textChanged.connect(lambda: self.search_trash(text=self.searchTrash.text(), trashTable=self.trashTable))
            self.trashTable.cellClicked.connect(lambda row, col: self.restore_or_delete_file(row, col, self.trashTable))

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
        
    def restore_or_delete_file(self, row, column, trashTable):
        file_id = trashTable.item(row, 0).text()

        msg_box = QMessageBox(self.trashDialog)
        msg_box.setWindowTitle("Restore or Delete")
        msg_box.setText("Do you want to restore or permanently delete this file?")
        msg_box.setIcon(QMessageBox.Question)

        restore_button = msg_box.addButton("Restore", QMessageBox.YesRole)
        delete_button = msg_box.addButton("Delete", QMessageBox.DestructiveRole)
        cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)

        msg_box.exec_()

        if msg_box.clickedButton() == restore_button:
            self.restore_file(file_id)
        elif msg_box.clickedButton() == delete_button:
            self.permanently_delete_file(file_id)

    def restore_file(self, file_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE FILE_UPLOAD SET FILE_ISDELETED = FALSE WHERE FILE_ID = %s", (file_id,))
            self.conn.commit()
            QMessageBox.information(self.trashDialog, "Restoration Success", "File has been restored successfully.")
            self.load_file_list()  
            self.refresh_trash_table()  
        except Exception as e:
            QMessageBox.critical(self.trashDialog, "Restore Error", f"Error restoring file: {e}")
        finally:
            cursor.close()

    def permanently_delete_file(self, file_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT FILE_PATH FROM FILE_UPLOAD WHERE FILE_ID = %s", (file_id,))
            file_record = cursor.fetchone()
        
            if file_record:
                file_path = file_record[0]
                
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except OSError as e:
                    QMessageBox.critical(self.trashDialog, "Deletion Error", f"Error deleting physical file: {e}")
                    return
                
                log_audit(self.user_id, 'DELETE', 'FILE', file_id)
                
                cursor.execute("DELETE FROM FILE_UPLOAD WHERE FILE_ID = %s", (file_id,))
                self.conn.commit()
                
                QMessageBox.information(self.trashDialog, "Deletion Success", "File has been permanently deleted.")
                self.load_file_list()  
                self.refresh_trash_table()
            else:
                QMessageBox.warning(self.trashDialog, "Not Found", "File record not found in database.")
                
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self.trashDialog, "Deletion Error", f"Error deleting file: {e}")
        finally:
            if cursor:
                cursor.close()

    def refresh_trash_table(self):
        trashTable = self.trashDialog.findChild(QTableWidget, "tableWidgetFileTrash")
        trashTable.setRowCount(0)
        
        header = self.trashTable.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [0, 250, 200, 150, 150]
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    F.FILE_ID,
                    F.FILE_NAME,
                    FC.FILE_CAT_NAME,
                    F.FILE_DATE_UPLOADED,
                    CONCAT(U.STAFF_LNAME, ', ', U.STAFF_FNAME) AS UPLOADED_BY
                FROM FILE_UPLOAD F
                LEFT JOIN USER_STAFF U ON F.STAFF_ID = U.STAFF_ID
                LEFT JOIN FILE_TYPE FT ON F.FILE_TYPE_ID = FT.FILE_TYPE_ID
                LEFT JOIN FILE_CATEGORY FC ON F.FILE_CAT_ID = FC.FILE_CAT_ID
                WHERE F.FILE_ISDELETED = TRUE
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
