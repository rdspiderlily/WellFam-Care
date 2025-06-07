from PyQt5.QtWidgets import QLineEdit, QComboBox, QDateEdit, QPushButton, QMessageBox, QSpinBox, QCheckBox
from PyQt5 import uic
from Database import connect_db

class PersonalInfoController:
    def __init__(self, page, patient_id):
        self.page = page
        self.patient_id = patient_id

        self.lname_edit = self.page.findChild(QLineEdit, "lineEditPatLname")
        self.fname_edit = self.page.findChild(QLineEdit, "lineEditPatFname")
        self.mname_edit = self.page.findChild(QLineEdit, "lineEditPatMname")
        self.dob_edit = self.page.findChild(QDateEdit, "datePatDOB")
        self.age_edit = self.page.findChild(QLineEdit, "lineEditPatAge")
        self.status_edit = self.page.findChild(QComboBox, "statusPat")
        self.contact_edit = self.page.findChild(QLineEdit, "lineEditPatContact")
        self.occu_edit = self.page.findChild(QLineEdit, "lineEditPatOccu")
        self.phm_edit = self.page.findChild(QComboBox, "pHMember")
        self.phnum_edit = self.page.findChild(QLineEdit, "pHNum")
        self.pat_ispreg_edit = self.page.findChild(QComboBox, "comboPregnancyStatus")
        self.lmp_edit = self.page.findChild(QDateEdit, "datePatLMP")
        self.edc_edit = self.page.findChild(QDateEdit, "datePatEDC")
        self.aog_edit = self.page.findChild(QSpinBox, "spinBoxAOG")
        self.addressNS_edit = self.page.findChild(QLineEdit, "lineEditPatAddressNS")
        self.addressB_edit = self.page.findChild(QLineEdit, "lineEditPatAddressB")
        self.addressMC_edit = self.page.findChild(QLineEdit, "lineEditPatAddressMC")
        self.addressP_edit = self.page.findChild(QLineEdit, "lineEditPatAddressP")
        
        self.spo_lname_edit = self.page.findChild(QLineEdit, "lineEditSpoLname")
        self.spo_fname_edit = self.page.findChild(QLineEdit, "lineEditSpoFname")
        self.spo_mname_edit = self.page.findChild(QLineEdit, "lineEditSpoMname")
        self.spo_occu_edit = self.page.findChild(QLineEdit, "lineEditSpoOccu")
        self.spo_dob_edit = self.page.findChild(QDateEdit, "dateSpoDOB")
        self.spo_contact_edit = self.page.findChild(QLineEdit, "lineEditSpoContact")
        self.spo_age_edit = self.page.findChild(QLineEdit, "lineEditSpoAge")
        
        self.fm = self.page.findChild(QCheckBox, "checkBoxFamilyPlanning")
        self.fm_dateAvailed = self.page.findChild(QDateEdit, "dateAvailedFamPlan")
        self.fm_counseling = self.page.findChild(QCheckBox, "checkBoxCounseling")
        self.fm_iud = self.page.findChild(QCheckBox, "checkBoxIUD")
        self.fm_condom = self.page.findChild(QCheckBox, "checkBoxCondom")
        self.fm_injectible = self.page.findChild(QCheckBox, "checkBoxInjectible")
        self.fm_pills = self.page.findChild(QCheckBox, "checkBoxPills")
        
        self.mc = self.page.findChild(QCheckBox, "checkBoxMaternalCare")
        self.mc_dateAvailed = self.page.findChild(QDateEdit, "dateAvailedMCare")
        self.mc_prenatal = self.page.findChild(QCheckBox, "checkBoxPrenatal")
        self.mc_laborm = self.page.findChild(QCheckBox, "checkBoxLaborM")
        self.mc_nsd = self.page.findChild(QCheckBox, "checkBoxNSD")
        self.mc_postpartum = self.page.findChild(QCheckBox, "checkBoxPostpartum")
        
        self.paps = self.page.findChild(QCheckBox, "checkBoxPapSmear")
        self.paps_dateAvailed = self.page.findChild(QDateEdit, "dateAvailedPSmear")
        self.paps_sall = self.page.findChild(QCheckBox, "checkBoxPapSmear")

        self.edit_btn = self.page.findChild(QPushButton, "pushBtnEditPat")
        self.save_btn = self.page.findChild(QPushButton, "pushBtnSavePat")
        self.cancel_btn = self.page.findChild(QPushButton, "pushBtnCancelPat")

        self.edit_btn.clicked.connect(self.enable_editing)
        self.save_btn.clicked.connect(self.save_patient_info)
        self.cancel_btn.clicked.connect(self.cancel_editing)

        self.load_patient_data()
        self.disable_editing()
        self.delete_btn = self.page.findChild(QPushButton, "pushBtnTrashPat")
        self.delete_btn.clicked.connect(self.pat_to_trash)

    def load_patient_data(self):
        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT PAT_LNAME, PAT_FNAME, PAT_MNAME, PAT_DOB, PAT_AGE, PAT_STATUS,
                        PAT_CNUM, PAT_OCCU, PAT_PHM, PAT_PHNUM, 
                        PAT_ISPREG, PAT_LMP, PAT_EDC, PAT_AOG,
                        PAT_ADDNS, PAT_ADDB, PAT_ADDMC, PAT_ADDP 
                    FROM PATIENT WHERE PAT_ID = %s AND PAT_ISDELETED = FALSE
                """, (self.patient_id,))
                result = cur.fetchone()
                
                if result:
                    self.lname_edit.setText(result[0])
                    self.fname_edit.setText(result[1])
                    self.mname_edit.setText(result[2])
                    self.dob_edit.setDate(result[3])
                    self.age_edit.setText(str(result[4]))
                    self.status_edit.setCurrentText(result[5])
                    self.contact_edit.setText(result[6])
                    self.occu_edit.setText(result[7])
                    self.phm_edit.setCurrentText(result[8])
                    self.phnum_edit.setText(result[9])
                    self.pat_ispreg_edit.setCurrentText(result[10])
                    if result[11]:
                        self.lmp_edit.setDate(result[11])
                    if result[12]:
                        self.edc_edit.setDate(result[12])
                    if result[13] is not None:
                        self.aog_edit.setValue(result[13])
                    self.addressNS_edit.setText(result[14])
                    self.addressB_edit.setText(result[15])
                    self.addressMC_edit.setText(result[16])
                    self.addressP_edit.setText(result[17])
                    
                cur.execute("""
                    SELECT SP_LNAME, SP_FNAME, SP_MNAME, SP_OCCU, SP_DOB, SP_CNUM, SP_AGE
                    FROM SPOUSE
                    WHERE PAT_ID = %s
                """, (self.patient_id,))
                spouse = cur.fetchone()
                if spouse:
                    self.spo_lname_edit.setText(spouse[0])
                    self.spo_fname_edit.setText(spouse[1])
                    self.spo_mname_edit.setText(spouse[2])
                    self.spo_occu_edit.setText(spouse[3])
                    self.spo_dob_edit.setDate(spouse[4])
                    self.spo_contact_edit.setText(spouse[5])
                    self.spo_age_edit.setText(spouse[6])
                
                self.load_services_and_subtypes()

            except Exception as e:
                QMessageBox.critical(self.page, "Error", str(e))
            finally:
                conn.close()
    
    def load_services_and_subtypes(self):
        conn = connect_db()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            service_map = {
                2: {
                    "main_checkbox": self.fm,
                    "date_field": self.fm_dateAvailed,
                    "subtypes": {
                        11: self.fm_counseling,
                        12: self.fm_iud,
                        13: self.fm_condom,
                        14: self.fm_injectible,
                        15: self.fm_pills,
                    }
                },
                3: {
                    "main_checkbox": self.mc,
                    "date_field": self.mc_dateAvailed,
                    "subtypes": {
                        16: self.mc_prenatal,
                        17: self.mc_laborm,
                        18: self.mc_nsd,
                        19: self.mc_postpartum,
                    }
                },
                13: {
                    "main_checkbox": self.paps,
                    "date_field": self.paps_dateAvailed,
                    "subtypes": {
                        20: self.paps_sall,
                    }
                }
            }

            cursor.execute("""
                SELECT PS_ID, SERV_ID, PS_DATEAVAILED
                FROM PATIENT_SERVICE
                WHERE PAT_ID = %s
            """, (self.patient_id,))
            services = cursor.fetchall()

            for ps_id, serv_id, date_availed in services:
                service = service_map.get(serv_id)
                if service:
                    if service["main_checkbox"]:
                        service["main_checkbox"].setChecked(True)
                    if service["date_field"] and date_availed:
                        service["date_field"].setDate(date_availed)

                    cursor.execute("""
                        SELECT SERV_TYPE_ID FROM PATIENT_SERVICE_TYPE
                        WHERE PS_ID = %s
                    """, (ps_id,))
                    subtype_ids = [row[0] for row in cursor.fetchall()]
                    for st_id in subtype_ids:
                        checkbox = service["subtypes"].get(st_id)
                        if checkbox:
                            checkbox.setChecked(True)

            cursor.close()
        except Exception as e:
            print("Error loading services:", e)
            QMessageBox.warning(self.page, "Load Warning", f"Error loading services:\n{str(e)}")
        finally:
            conn.close()

    def enable_editing(self):
        editable_widgets = [
            self.lname_edit, self.fname_edit, self.mname_edit, self.dob_edit, self.age_edit,
            self.status_edit, self.contact_edit, self.occu_edit, 
            self.addressNS_edit, self.addressB_edit, self.addressMC_edit, self.addressP_edit,
            self.phm_edit, self.phnum_edit, self.pat_ispreg_edit, self.lmp_edit,
            self.edc_edit, self.aog_edit,
            self.spo_lname_edit, self.spo_fname_edit, self.spo_mname_edit,
            self.spo_occu_edit, self.spo_dob_edit, self.spo_contact_edit, self.spo_age_edit
        ]

        service_widgets = [
            self.fm, self.fm_dateAvailed, self.fm_counseling, self.fm_iud,
            self.fm_condom, self.fm_injectible, self.fm_pills,
            self.mc, self.mc_dateAvailed, self.mc_prenatal,
            self.mc_laborm, self.mc_nsd, self.mc_postpartum,
            self.paps, self.paps_dateAvailed, self.paps_sall
        ]

        for widget in editable_widgets + service_widgets:
            if widget:
                widget.setEnabled(True)

        self.save_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.edit_btn.setEnabled(False)

    def cancel_editing(self):
        reply = QMessageBox.question(
            self.page,
            "Cancel Editing",
            "Are you sure you want to discard any changes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.load_patient_data()
            self.disable_editing() 

    def disable_editing(self):
        readonly_widgets = [
            self.lname_edit, self.fname_edit, self.mname_edit, self.dob_edit, self.age_edit,
            self.status_edit, self.contact_edit, self.occu_edit, 
            self.addressNS_edit, self.addressB_edit, self.addressMC_edit, self.addressP_edit,
            self.phm_edit, self.phnum_edit, self.pat_ispreg_edit, self.lmp_edit,
            self.edc_edit, self.aog_edit,
            self.spo_lname_edit, self.spo_fname_edit, self.spo_mname_edit,
            self.spo_occu_edit, self.spo_dob_edit, self.spo_contact_edit, self.spo_age_edit
        ]

        service_widgets = [
            self.fm, self.fm_dateAvailed, self.fm_counseling, self.fm_iud,
            self.fm_condom, self.fm_injectible, self.fm_pills,
            self.mc, self.mc_dateAvailed, self.mc_prenatal,
            self.mc_laborm, self.mc_nsd, self.mc_postpartum,
            self.paps, self.paps_dateAvailed, self.paps_sall
        ]

        for widget in readonly_widgets + service_widgets:
            if widget:
                widget.setEnabled(False)

        self.save_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.edit_btn.setEnabled(True)

    def save_patient_info(self):
        if QMessageBox.question(
            self.page, "Confirm Save", "Are you sure you want to save these changes?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) != QMessageBox.Yes:
            return

        patient_values = (
        self.lname_edit.text(), self.fname_edit.text(), self.mname_edit.text(),
        self.dob_edit.date().toString("yyyy-MM-dd"), self.age_edit.text(),
        self.status_edit.currentText(), self.contact_edit.text(), self.occu_edit.text(),
        self.phm_edit.currentText(), self.phnum_edit.text(),
        self.pat_ispreg_edit.currentText(), self.lmp_edit.date().toString("yyyy-MM-dd"),
        self.edc_edit.date().toString("yyyy-MM-dd"), self.aog_edit.value(),
        self.addressNS_edit.text(), self.addressB_edit.text(), self.addressMC_edit.text(), self.addressP_edit.text()
        )

        spouse_values = (
            self.spo_lname_edit.text() or None, self.spo_fname_edit.text() or None, self.spo_mname_edit.text() or None,
            self.spo_occu_edit.text() or None, self.spo_dob_edit.date().toString("yyyy-MM-dd") or None,
            self.spo_contact_edit.text() or None, self.spo_age_edit.text() or None
        )

        if not patient_values[0] or not patient_values[1] or not patient_values[3] or not patient_values[6] or not patient_values[7]:
            QMessageBox.warning(self.page, "Input Error", "All required patient fields must be filled.")
            return

        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()

                # Update patient table
                cur.execute("""
                    UPDATE PATIENT
                    SET PAT_LNAME=%s, PAT_FNAME=%s, PAT_MNAME=%s, PAT_DOB=%s, PAT_AGE=%s, 
                        PAT_STATUS=%s, PAT_CNUM=%s, PAT_OCCU=%s,
                        PAT_PHM=%s, PAT_PHNUM=%s, PAT_ISPREG=%s, PAT_LMP=%s, PAT_EDC=%s, PAT_AOG=%s,
                        PAT_ADDNS=%s, PAT_ADDB=%s, PAT_ADDMC=%s, PAT_ADDP=%s
                    WHERE PAT_ID=%s AND PAT_ISDELETED = FALSE
                """, (*patient_values, self.patient_id))

                # Update or insert spouse
                cur.execute("SELECT COUNT(*) FROM SPOUSE WHERE PAT_ID = %s", (self.patient_id,))
                if cur.fetchone()[0] > 0:
                    cur.execute("""
                        UPDATE SPOUSE
                        SET SP_LNAME=%s, SP_FNAME=%s, SP_MNAME=%s, SP_OCCU=%s, SP_DOB=%s, SP_CNUM=%s, SP_AGE=%s
                        WHERE PAT_ID=%s
                    """, (*spouse_values, self.patient_id))
                else:
                    cur.execute("""
                        INSERT INTO SPOUSE (SP_LNAME, SP_FNAME, SP_MNAME, SP_OCCU, SP_DOB, SP_CNUM, SP_AGE, PAT_ID)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (*spouse_values, self.patient_id))

                # --- Handle services ---
                # Remove existing services first
                cur.execute("SELECT PS_ID FROM PATIENT_SERVICE WHERE PAT_ID = %s", (self.patient_id,))
                old_ps_ids = [row[0] for row in cur.fetchall()]
                for ps_id in old_ps_ids:
                    cur.execute("DELETE FROM PATIENT_SERVICE_TYPE WHERE PS_ID = %s", (ps_id,))
                cur.execute("DELETE FROM PATIENT_SERVICE WHERE PAT_ID = %s", (self.patient_id,))

                # Map service structure
                service_map = {
                    2: {
                        "main_checkbox": self.fm,
                        "date_field": self.fm_dateAvailed,
                        "subtypes": {
                            11: self.fm_counseling,
                            12: self.fm_iud,
                            13: self.fm_condom,
                            14: self.fm_injectible,
                            15: self.fm_pills,
                        }
                    },
                    3: {
                        "main_checkbox": self.mc,
                        "date_field": self.mc_dateAvailed,
                        "subtypes": {
                            16: self.mc_prenatal,
                            17: self.mc_laborm,
                            18: self.mc_nsd,
                            19: self.mc_postpartum,
                        }
                    },
                    13: {
                        "main_checkbox": self.paps,
                        "date_field": self.paps_dateAvailed,
                        "subtypes": {
                            20: self.paps_sall,
                        }
                    }
                }

                for serv_id, service in service_map.items():
                    if service["main_checkbox"].isChecked():
                        date_availed = service["date_field"].date().toString("yyyy-MM-dd")
                        cur.execute("""
                            INSERT INTO PATIENT_SERVICE (PAT_ID, SERV_ID, PS_DATEAVAILED)
                            VALUES (%s, %s, %s) RETURNING PS_ID
                        """, (self.patient_id, serv_id, date_availed))
                        ps_id = cur.fetchone()[0]

                        for st_id, checkbox in service["subtypes"].items():
                            if checkbox.isChecked():
                                cur.execute("""
                                    INSERT INTO PATIENT_SERVICE_TYPE (PS_ID, SERV_TYPE_ID)
                                    VALUES (%s, %s)
                                """, (ps_id, st_id))

                conn.commit()

                QMessageBox.information(self.page, "Success", "Patient and spouse info updated successfully!")
                self.disable_editing()

            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self.page, "Error", f"Update failed: {e}")
            finally:
                conn.close()
                
    def pat_to_trash(self):
        reply = QMessageBox.question(
            self.page,
            "Move to Trash",
            "Are you sure you want to move this patient to trash?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            conn = connect_db()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("UPDATE PATIENT SET PAT_ISDELETED = TRUE WHERE PAT_ID = %s", (self.patient_id,))
                    conn.commit()
                    QMessageBox.information(self.page, "Deleted", "Patient has been moved to trash successfully.")
                    self.page.window().close()

                except Exception as e:
                    conn.rollback()
                    QMessageBox.critical(self.page, "Error", f"Failed to move patient to trash: {e}")
                finally:
                    conn.close()