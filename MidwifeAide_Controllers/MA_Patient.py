from PyQt5.QtWidgets import (
    QComboBox, QDialog, QMessageBox, QPushButton, 
    QWidget, QDateEdit, QLineEdit, QTableWidget, 
    QHeaderView, QTableWidgetItem, QSpinBox, QCheckBox
)
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import os
import glob

from Database import connect_db
from Database import log_audit
from MidwifeAide_Controllers.MA_Patient_View.MA_ViewPatCat import MAViewPatientDialog

class MAPatientController:
    def __init__(self, tableWidPat: QTableWidget, search: QLineEdit, user_id):
        self.conn = connect_db()
        self.tableWidPat = tableWidPat
        self.patient_list()
        self.user_id = user_id
        
        self.tableWidPat.cellClicked.connect(self.view_patient)
        
        self.search = search
        self.search.textChanged.connect(self.search_patient)

    def patient_list(self):
        self.tableWidPat.setRowCount(0)
        
        header = self.tableWidPat.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [0, 230, 230, 150, 80, 128, 150]
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)
        
        self.tableWidPat.setColumnHidden(0, True)
        self.tableWidPat.verticalHeader().setVisible(False)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT PAT_ID, PAT_LNAME, PAT_FNAME, PAT_CNUM, PAT_AGE, PAT_DOB, PAT_STATUS FROM PATIENT WHERE PAT_ISDELETED = FALSE")
            rows = cursor.fetchall()

            existing_ids = [self.tableWidPat.item(row, 0).text() for row in range(self.tableWidPat.rowCount())]

            for row in rows:
                if row[0] not in existing_ids:
                    row_position = self.tableWidPat.rowCount()
                    self.tableWidPat.insertRow(row_position)
                    for column, data in enumerate(row):
                        self.tableWidPat.setItem(row_position, column, QTableWidgetItem(str(data)))
        except Exception as e:
            QMessageBox.critical(self.tableWidPat, "Database Error", f"Error fetching updated data: {e}")

    def add_patient_dialog(self):
        dialog = QDialog()
        uic.loadUi("wfui/add_patient.ui", dialog)
        dialog.setWindowTitle("Add New Patient")
        dialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))
        
        addPatWidget = dialog.findChild(QWidget, "widgetaddPat")
        if not addPatWidget:
            print("ERROR: widgetAddPat not found!")
                
        save_button = dialog.findChild(QPushButton, "pushBtnSavePat")
        if save_button:
            save_button.clicked.connect(lambda: self.save_patient(addPatWidget, dialog))
        
        cancel_button = dialog.findChild(QPushButton, "pushBtnCancelPat")
        if cancel_button:
            cancel_button.clicked.connect(dialog.reject)
        
        dialog.exec_()

    def save_patient(self, addPatWidget, dialog):
        try:
            required_fields = [
                "lineEditPatLname", "lineEditPatFname", "datePatDOB", "lineEditPatAge",
                "lineEditPatContact", "lineEditPatOccu", 
                "lineEditPatAddressNS", "lineEditPatAddressB", "lineEditPatAddressMC", "lineEditPatAddressP",
                "statusPat", "pHMember", "comboPregnancyStatus"
            ]
            for field in required_fields:
                widget = addPatWidget.findChild((QLineEdit, QComboBox, QDateEdit), field)
                if not widget:
                    QMessageBox.warning(addPatWidget, "Missing Widget", f"Widget '{field}' is missing.")
                    return
                value = widget.text() if isinstance(widget, QLineEdit) else widget.currentText() if isinstance(widget, QComboBox) else widget.date().toString("yyyy-MM-dd")
                if not value.strip():
                    QMessageBox.warning(addPatWidget, "Validation Error", f"Field '{field}' is required.")
                    return

            pat_lname = addPatWidget.findChild(QLineEdit, "lineEditPatLname").text()
            pat_fname = addPatWidget.findChild(QLineEdit, "lineEditPatFname").text()
            pat_mname = addPatWidget.findChild(QLineEdit, "lineEditPatMname").text()
            pat_dob = addPatWidget.findChild(QDateEdit, "datePatDOB").date().toPyDate()
            pat_age = addPatWidget.findChild(QLineEdit, "lineEditPatAge").text()
            pat_status = addPatWidget.findChild(QComboBox, "statusPat").currentText()
            pat_contact = addPatWidget.findChild(QLineEdit, "lineEditPatContact").text()
            pat_occu = addPatWidget.findChild(QLineEdit, "lineEditPatOccu").text()
            pat_phm = addPatWidget.findChild(QComboBox, "pHMember").currentText()[0]  # e.g., 'Y' or 'N'
            pat_phnum = addPatWidget.findChild(QLineEdit, "pHNum").text()
            pat_is_preg = addPatWidget.findChild(QComboBox, "comboPregnancyStatus").currentText()
            pat_ispreg = 'Y' if pat_is_preg == "Y" else 'N'
            pat_lmp = addPatWidget.findChild(QDateEdit, "datePatLMP").date().toPyDate() if pat_is_preg == "Y" else None
            pat_edc = addPatWidget.findChild(QDateEdit, "datePatEDC").date().toPyDate() if pat_is_preg == "Y" else None
            pat_aog = addPatWidget.findChild(QSpinBox, "spinBoxAOG").value() if pat_is_preg == "Y" else None
            pat_addressNS = addPatWidget.findChild(QLineEdit, "lineEditPatAddressNS").text()
            pat_addressB = addPatWidget.findChild(QLineEdit, "lineEditPatAddressB").text()
            pat_addressMC = addPatWidget.findChild(QLineEdit, "lineEditPatAddressMC").text()
            pat_addressP = addPatWidget.findChild(QLineEdit, "lineEditPatAddressP").text()

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO PATIENT (
                    PAT_LNAME, PAT_FNAME, PAT_MNAME, PAT_DOB, PAT_AGE, PAT_STATUS,
                    PAT_CNUM, PAT_OCCU, PAT_PHM, PAT_PHNUM,
                    PAT_LMP, PAT_EDC, PAT_AOG, PAT_ISPREG, 
                    PAT_ADDNS, PAT_ADDB, PAT_ADDMC, PAT_ADDP 
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING PAT_ID
            """, (
                pat_lname, pat_fname, pat_mname, pat_dob, pat_age, pat_status,
                pat_contact, pat_occu, pat_phm, pat_phnum,
                pat_lmp, pat_edc, pat_aog, pat_ispreg,
                pat_addressNS, pat_addressB, pat_addressMC, pat_addressP
            ))
            pat_id = cursor.fetchone()[0]
            log_audit(self.user_id, 'CREATE', 'PATIENTS', pat_id)

            spouse_fname = addPatWidget.findChild(QLineEdit, "lineEditSpoFname").text()
            spouse_lname = addPatWidget.findChild(QLineEdit, "lineEditSpoLname").text()
            spouse_occu = addPatWidget.findChild(QLineEdit, "lineEditSpoOccu").text()
            spouse_dob = addPatWidget.findChild(QDateEdit, "dateSpoDOB").date().toPyDate()
            spouse_contact = addPatWidget.findChild(QLineEdit, "lineEditSpoContact").text()
            spouse_age = addPatWidget.findChild(QLineEdit, "lineEditSpoAge").text()

            if spouse_fname and spouse_lname:
                cursor.execute("""
                    INSERT INTO SPOUSE (SP_LNAME, SP_FNAME, SP_OCCU, SP_DOB, SP_CNUM, SP_AGE, PAT_ID)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (spouse_lname, spouse_fname, spouse_occu, spouse_dob, spouse_contact, spouse_age, pat_id))

            # --- Service Checkboxes ---
            def insert_service(service_id, date_availed, subtypes_ids=[]):
                cursor.execute("""
                    INSERT INTO PATIENT_SERVICE (PS_DATEAVAILED, PAT_ID, SERV_ID)
                    VALUES (%s, %s, %s) RETURNING PS_ID
                """, (date_availed, pat_id, service_id))
                ps_id = cursor.fetchone()[0]
                for st_id in subtypes_ids:
                    cursor.execute("""
                        INSERT INTO PATIENT_SERVICE_TYPE (PS_ID, SERV_TYPE_ID)
                        VALUES (%s, %s)
                    """, (ps_id, st_id))

            # --- Family Planning ---
            if addPatWidget.findChild(QCheckBox, "checkBoxFamilyPlanning").isChecked():
                fm_dateA = addPatWidget.findChild(QDateEdit, "dateAvailedFamPlan").date().toPyDate()
                family_subtypes = {
                    "checkBoxCounseling": 11,
                    "checkBoxIUD": 12,
                    "checkBoxCondom": 13,
                    "checkBoxInjectible": 14,
                    "checkBoxPills": 15,
                }
                sub_ids = []
                for name, id in family_subtypes.items():
                    check_box = addPatWidget.findChild(QCheckBox, name)
                    if check_box and check_box.isChecked():  
                        sub_ids.append(id)
                if sub_ids:  
                    insert_service(2, fm_dateA, sub_ids)

            # --- Maternal Care ---
            if addPatWidget.findChild(QCheckBox, "checkBoxMaternalCare").isChecked():
                mc_dateA = addPatWidget.findChild(QDateEdit, "dateAvailedMCare").date().toPyDate()
                maternal_subtypes = {
                    "checkBoxPrenatal": 16,
                    "checkBoxLaborM": 17,
                    "checkBoxNSD": 18,
                    "checkBoxPostpartum": 19,
                }
                sub_ids = []
                for name, id in maternal_subtypes.items():
                    check_box = addPatWidget.findChild(QCheckBox, name)
                    if check_box and check_box.isChecked():  
                        sub_ids.append(id)
                if sub_ids:  
                    insert_service(3, mc_dateA, sub_ids)

            # --- Pap Smear ---
            if addPatWidget.findChild(QCheckBox, "checkBoxPapSmear").isChecked():
                ps_dateA = addPatWidget.findChild(QDateEdit, "dateAvailedPSmear").date().toPyDate()
                insert_service(13, ps_dateA, [20])

            self.conn.commit()
            cursor.close()
            self.patient_list()
            QMessageBox.information(addPatWidget, "Success", "Patient added successfully.")
            dialog.accept()

        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(addPatWidget, "Database Error", f"An error occurred:\n{str(e)}")
            print("Database error:", e)

    def insert_patient_row(self, new_row):
        row_position = self.tableWidPat.rowCount()
        self.tableWidPat.insertRow(row_position)
        for column, data in enumerate(new_row):
            self.tableWidPat.setItem(row_position, column, QTableWidgetItem(str(data)))

    def search_patient(self, text):
        for row in range(self.tableWidPat.rowCount()):
            match = False
            for col in range(1, self.tableWidPat.columnCount()):
                item = self.tableWidPat.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.tableWidPat.setRowHidden(row, not match)
            
    def trash_list(self):
        if hasattr(self, 'trashDialog') and self.trashDialog is not None:
            if self.trashDialog.isVisible():
                self.trashDialog.raise_()
                self.trashDialog.activateWindow()
                return
        else:
            self.trashDialog = QDialog()
            self.trashDialog.setAttribute(Qt.WA_DeleteOnClose)
            self.trashDialog.destroyed.connect(lambda: setattr(self, 'trashDialog', None))

            uic.loadUi("wfui/trash_patient.ui", self.trashDialog)
            self.trashDialog.setWindowTitle("Trash")
            self.trashDialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))

            trashPatWidget = self.trashDialog.findChild(QWidget, "widgetPatTrash")
            if not trashPatWidget:
                print("ERROR: widgetPatTrash not found!")
                return

            self.searchTrash = trashPatWidget.findChild(QLineEdit, "lineEditSearchTrash")
            self.trashTable = trashPatWidget.findChild(QTableWidget, "tableWidgetTrash")

            header = self.trashTable.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Fixed)
            column_sizes = [0, 210, 210, 150, 50, 130, 120]
            for i, size in enumerate(column_sizes):
                header.resizeSection(i, size)

            self.trashTable.setColumnHidden(0, True)
            self.trashTable.verticalHeader().setVisible(False)

            if self.searchTrash:
                self.searchTrash.textChanged.connect(lambda: self.search_trash(text=self.searchTrash.text(), trashTable=self.trashTable))
            self.trashTable.cellClicked.connect(lambda row, col: self.restore_or_delete_patient(row, col, self.trashTable))

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

    def restore_or_delete_patient(self, row, column, trashTable):
        patient_id = trashTable.item(row, 0).text()

        msg_box = QMessageBox(self.trashDialog)
        msg_box.setWindowTitle("Restore or Delete")
        msg_box.setText("Do you want to restore or permanently delete this patient?")
        msg_box.setIcon(QMessageBox.Question)

        restore_button = msg_box.addButton("Restore", QMessageBox.YesRole)
        delete_button = msg_box.addButton("Delete", QMessageBox.DestructiveRole)
        cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)

        msg_box.exec_()

        if msg_box.clickedButton() == restore_button:
            self.restore_patient(patient_id)
        elif msg_box.clickedButton() == delete_button:
            self.delete_patient(patient_id)

    def restore_patient(self, patient_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE PATIENT SET PAT_ISDELETED = FALSE WHERE PAT_ID = %s", (patient_id,))
            log_audit(self.user_id, 'RESTORE', 'PATIENTS', patient_id)
            self.conn.commit()
            QMessageBox.information(self.trashDialog, "Restoration Success", "Patient has been restored successfully.")
            self.patient_list()  
            self.refresh_trash_table()  
        except Exception as e:
            QMessageBox.critical(self.trashDialog, "Restore Error", f"Error restoring patient: {e}")
        finally:
            cursor.close()


    def delete_patient(self, patient_id):
        cursor = None
        try:
            temp_dir = "temp"
            pdf_patterns = [
                f"MaternalServiceRecord_{patient_id}.pdf",
                f"FamilyPlanning_{patient_id}.pdf",
                f"PatientDataSheet_{patient_id}.pdf",
                f"*_{patient_id}.pdf"  # Catch-all pattern
            ]
            
            deleted_files = []
            for pattern in pdf_patterns:
                for pdf_file in glob.glob(os.path.join(temp_dir, pattern)):
                    try:
                        os.remove(pdf_file)
                        deleted_files.append(os.path.basename(pdf_file))
                    except OSError as e:
                        print(f"Error deleting PDF {pdf_file}: {e}")

            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM PATIENT WHERE PAT_ID = %s", (patient_id,))
            log_audit(self.user_id, 'DELETE', 'PATIENTS', patient_id)
            self.conn.commit()
            
            QMessageBox.information(self.trashDialog, "Deletion Success", "Patient has been permanently deleted.")
            self.patient_list()  
            self.refresh_trash_table() 
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self.trashDialog, "Deletion Error", f"Error deleting patient: {e}")
        finally:
            cursor.close()

    def refresh_trash_table(self):
        trashTable = self.trashDialog.findChild(QTableWidget, "tableWidgetTrash")
        trashTable.setRowCount(0)

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT PAT_ID, PAT_LNAME, PAT_FNAME, PAT_CNUM, PAT_AGE, PAT_DOB FROM PATIENT WHERE PAT_ISDELETED = TRUE")
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

    def view_patient(self, row, column):
        pat_id_item = self.tableWidPat.item(row, 0)
        
        if pat_id_item is None:
            return
        
        pat_id = pat_id_item.text()
        
        dialog = MAViewPatientDialog(pat_id, self.user_id)  #Passing PAT_ID and STAFF_ID to View Patient Details and Forms
        dialog.exec_()