from PyQt5.QtWidgets import (
    QPushButton, QStackedWidget, QLineEdit,
    QDateEdit, QComboBox, QTimeEdit, QCheckBox,
    QTextEdit, QSpinBox, QDoubleSpinBox, QMessageBox
)

from PyQt5.QtCore import QDate, QTime
from datetime import date
import os
import webbrowser
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, TextStringObject, NumberObject, BooleanObject

from Database import connect_db
from Admin_Controllers.Admin_Patient_View.AutofillPersonalInfo import AutofillPersonalInfoController
from Admin_Controllers.Admin_Patient_View.AutofillMF import AutofillMatFamController

class MaternalRecordsController:
    def __init__(self, pageMSR, patient_id, user_id):
        self.conn = connect_db()
        self.pageMSR = pageMSR
        self.patient_id = patient_id
        self.user_id = user_id
        self.autofill = AutofillPersonalInfoController(self.conn)
        self.autofillM = AutofillMatFamController(self.conn)
        
        self.stackWidMSR = self.pageMSR.findChild(QStackedWidget, "stackWidMSR")
        
        self.save_btn = self.pageMSR.findChild(QPushButton, "btnSaveMSR")
        self.edit_btn = self.pageMSR.findChild(QPushButton, "btnEditMSR")
        self.cancel_btn = self.pageMSR.findChild(QPushButton, "btnCancelMSR")
        self.autofill_btn = self.pageMSR.findChild(QPushButton, "btnLoadFromFamPlan")
        self.viewPDF_btn = self.pageMSR.findChild(QPushButton, "viewMatPDF")
        
        if not self.has_maternal_package_service():
            self.edit_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            QMessageBox.information(self.pageMSR, "Information Forms", "This patient did not avail Maternal Care Package service. Form is view-only.")
        
        self.prev_btn = self.pageMSR.findChild(QPushButton, "pushBtnPrev")
        self.next_btn = self.pageMSR.findChild(QPushButton, "pushBtnNext")
        
        self.autofill_btn.clicked.connect(self.on_autofill_clicked)
        
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.edit_btn.clicked.connect(self.enable_editing_mode)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        self.viewPDF_btn.clicked.connect(self.show_pdfPrint)

        self.set_all_fields_read_only()
        
        self.prev_btn.clicked.connect(self.go_prev)
        self.next_btn.clicked.connect(self.go_next)

        self.stackWidMSR.setCurrentIndex(0)
        self.personal_info()
        self.medicalH_info()
        self.physicalE_info()
        self.birthEPlan_info()
        self.update_nav_buttons()
    
    def has_maternal_package_service(self):
        query = """
            SELECT 1 FROM PATIENT_SERVICE ps
            JOIN SERVICE s ON ps.SERV_ID = s.SERV_ID
            WHERE ps.PAT_ID = %s AND s.SERV_NAME = 'Maternal Care Package'
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (self.patient_id,))
        result = cursor.fetchone()
        cursor.close()
        return bool(result)
    
    def go_prev(self):
        current_index = self.stackWidMSR.currentIndex()
        if current_index > 0:
            self.stackWidMSR.setCurrentIndex(current_index - 1)
        self.update_nav_buttons()

    def go_next(self):
        current_index = self.stackWidMSR.currentIndex()
        if current_index < self.stackWidMSR.count() - 1:
            self.stackWidMSR.setCurrentIndex(current_index + 1)
        self.update_nav_buttons()

    def update_nav_buttons(self):
        current_index = self.stackWidMSR.currentIndex()
        self.prev_btn.setEnabled(current_index > 0)
        self.next_btn.setEnabled(current_index < self.stackWidMSR.count() - 1)
    
    # View-only Maternal Dialog
    def set_all_fields_read_only(self):
        def disable_widgets(widget):
            if isinstance(widget, (QLineEdit, QTextEdit)):
                widget.setReadOnly(True)
            elif isinstance(widget, (QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox)):
                widget.setEnabled(False)
            elif isinstance(widget, QCheckBox):
                widget.setEnabled(False)
            elif isinstance(widget, QStackedWidget):
                for i in range(widget.count()):
                    disable_widgets(widget.widget(i))
            elif hasattr(widget, "children"):
                for child in widget.children():
                    disable_widgets(child)

        disable_widgets(self.pageMSR)
        self.cancel_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

    def enable_editing_mode(self):
        def enable_widgets(widget):
            if isinstance(widget, (QLineEdit, QTextEdit)):
                widget.setReadOnly(False)
            elif isinstance(widget, (QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox)):
                widget.setEnabled(True)
                if isinstance(widget, QDateEdit) and widget.date() is None:
                    widget.setDate(QDate.currentDate())  # Set default if no date
                if isinstance(widget, QTimeEdit) and widget.time() is None:
                    widget.setTime(QTime.currentTime())  # Set default if no time
            elif isinstance(widget, QCheckBox):
                widget.setEnabled(True)
            elif isinstance(widget, QStackedWidget):
                for i in range(widget.count()):
                    enable_widgets(widget.widget(i))
            elif hasattr(widget, "children"):
                for child in widget.children():
                    enable_widgets(child)

        enable_widgets(self.pageMSR)
        self.cancel_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

        # Keep prefilled fields disabled
        self.clt_lname.setReadOnly(True)
        self.clt_fname.setReadOnly(True)
        self.clt_minit.setReadOnly(True)
        self.clt_dob.setEnabled(False)
        self.clt_NSAdd.setReadOnly(True)
        self.clt_BarAdd.setReadOnly(True)
        self.clt_MuniAdd.setReadOnly(True)
        self.clt_ProvAdd.setReadOnly(True)
    
    def save_all_page(self):
        try:
            self.save_basic_pinfo()
            self.save_other_pinfo()
            self.save_medical()
            self.save_obstetrical()
            self.save_physicalE()
            self.save_pelvicE()
            self.save_birthEPlan()
            
            form_id = self.get_form_id('Maternal Service Record')
            if form_id is None:
                print("Form ID for Maternal is not found.")
                return
            ps_id = self.get_patient_service_id()
            if ps_id is None:
                print("Patient service ID not found.")
                return
            
            # Before inserting, ensure that PS_ID exists in PATIENT_SERVICE
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM PATIENT_SERVICE WHERE PS_ID = %s", (ps_id,))
            count = cursor.fetchone()[0]
            cursor.close()
            
            if count == 0:
                print(f"PS_ID {ps_id} not found in PATIENT_SERVICE table.")
                return
            
            cursor = self.conn.cursor()
            # Check if the form ID, patient ID, and patient service ID are correct before inserting
            cursor.execute("""
                INSERT INTO PATIENT_FORM (PF_DATEFILLED, FORM_ID, PAT_ID, PS_ID, PF_FILLEDBY)
                VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s)
            """, (form_id, self.patient_id, ps_id, self.user_id))
            self.conn.commit()
            cursor.close()
            
            QMessageBox.information(self.pageMSR, "Success", "Maternal record saved successfully.")
        except Exception as e:
            print("Error while saving:", e)
    
    def get_form_id(self, form_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT FORM_ID FROM FORM WHERE FORM_NAME = %s", (form_name,))
        form_id = cursor.fetchone()
        cursor.close()
        return form_id[0] if form_id else None
    
    def get_patient_service_id(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT PS_ID
            FROM PATIENT_SERVICE
            WHERE PAT_ID = %s AND SERV_ID = 3
        """, (self.patient_id,))  # Ensure the service ID for Maternal Care Package (3)
        ps_id = cursor.fetchone()
        cursor.close()
        if ps_id:
            return ps_id[0]  # Return the PS_ID
        else:
            print(f"No patient service found for PAT_ID {self.patient_id} and SERV_ID 3.")
            return None  
        
    def on_autofill_clicked(self):
        reply = QMessageBox.question(
            self.pageMSR,
            "Autofill Form",
            "Are you sure you want to autofill some fields from Maternal Service Record?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.autofill_famTOmat()
            QMessageBox.information(self.pageMSR, "Success Autofill", "Some maternal data has been autofilled from family planning form.")
            self.set_all_fields_read_only()
            
    def autofill_famTOmat(self):
        try:
            self.load_basic_pinfo_widgets()
            self.load_other_pinfo_widgets()
            self.load_obstetrical_widgets()
            self.load_physicalE_widgets()
            self.enable_editing_mode()
            
            if not all([
                #Addons personal info
                self.clt_num, self.clt_eduA, 
                self.clt_planMKidsY, self.clt_planMKidsN,
                
                #Medical History
                self.med_shdY, self.med_fhcY, self.med_scpY, self.med_ydY, self.med_sY,
                self.med_shdN, self.med_fhcN, self.med_scpN, self.med_ydN, self.med_sN,
                
                #Obstetrical History
                self.obs_ft, self.obs_pt, self.obs_abort, self.obs_livekids,
                self.obs_dold, self.obs_tod, self.obs_pmp,
                
                #Physical Examination
                self.phye_weight, self.phye_height,  self.phye_bps, self.phye_bpd,
                self.phye_pY, self.phye_yY,
                self.phye_pN, self.phye_yN,
                
                self.phye_elnY, self.phye_mY, self.phye_ndY,
                self.phye_elnN, self.phye_mN, self.phye_ndN
            ]):
                print("Some client input fields are not initialized. Please check objectNames in the UI.")
                return

            info = self.autofillM.famTOmat(self.patient_id)
            if info:
                self.clt_num.setText(info["clientno"])
                self.clt_eduA.setCurrentText(info["educAtt"])
                
                plan_moreKids = info.get("planmorekids", "").lower()
                if plan_moreKids == "yes":
                    self.clt_planMKidsY.setChecked(True)
                elif plan_moreKids == "no":
                    self.clt_planMKidsN.setChecked(True)
                
                #Medical History
                fields = [
                    ("svheadache", self.med_shdY, self.med_shdN),
                    ("CVAhistory", self.med_fhcY, self.med_fhcN),
                    ("svchestpain", self.med_scpY, self.med_scpN),
                    ("yellow/jaundice", self.med_ydY, self.med_ydN),
                    ("smoking", self.med_sY, self.med_sN),
                ]

                for key, radio_yes, radio_no in fields:
                    value = info.get(key, "").lower()
                    if value == "yes":
                        radio_yes.setChecked(True)
                    elif value == "no":
                        radio_no.setChecked(True)
                
                #Obstetrical History
                self.obs_ft.setValue(int(info["NOPfullterm"]))
                self.obs_pt.setValue(int(info["NOPpreterm"]))
                self.obs_abort.setValue(int(info["NOPabortion"]))
                self.obs_livekids.setValue(int(info["nooflivkids"]))
                self.obs_dold.setDate(QDate.fromString(info["dateOLdelivery"], "MM-dd-yyyy"))
                vaginal = info.get("typeOLdelivery_vaginal", "No")
                csection = info.get("typeOLdelivery_csection", "No")

                if vaginal == "Yes":
                    self.obs_tod.setCurrentText("Vaginal")
                elif csection == "Yes":
                    self.obs_tod.setCurrentText("Cesarean")
                else:
                    self.obs_tod.setCurrentText("")
                self.obs_pmp.setDate(QDate.fromString(info["pmp"], "MM-dd-yyyy"))
                
                #Physical Examination
                self.phye_weight.setValue(float(info["PEweight"]))
                self.phye_height.setValue(float(info["PEheight"]))
                self.phye_bps.setValue(int(info["bpS"]))
                self.phye_bpd.setValue(int(info["bpD"]))
                
                fieldsPE = [
                    ("conjuPale", self.phye_pY, self.phye_pN),
                    ("conjuYellowish", self.phye_yY, self.phye_yN),
                    ("neckEnNodes", self.phye_elnY, self.phye_elnN),
                    ("breastMass", self.phye_mY, self.phye_mN),
                    ("breastNipD", self.phye_ndY, self.phye_ndN),
                ]

                for key, radio_yes, radio_no in fieldsPE:
                    value = info.get(key, "").lower()
                    if value == "yes":
                        radio_yes.setChecked(True)
                    elif value == "no":
                        radio_no.setChecked(True)
                
            else:
                print("No data returned for autofill.")
    
        except Exception as e:
            print("Error in autofill:", e)
            self.conn.rollback()
        
    def personal_info(self):
        self.load_basic_pinfo_widgets()
        self.load_other_pinfo_widgets()
        self.load_basic_pinfo()
        self.load_other_pinfo()
        self.prefilled_pinfo()
        
    def prefilled_pinfo(self):
        try:
            self.load_basic_pinfo_widgets()
            self.load_other_pinfo_widgets()

            if not all([
                self.clt_lname, 
                self.clt_fname, 
                self.clt_minit, 
                self.clt_dob,
                self.clt_NSAdd,
                self.clt_BarAdd,
                self.clt_MuniAdd,
                self.clt_ProvAdd
                
            ]):
                print("Some input fields are not initialized. Please check objectNames in the UI.")
                return

            info = self.autofill.get_basic_info(self.patient_id)
            if info:
                self.clt_lname.setText(info["lname"])
                self.clt_fname.setText(info["fname"])
                self.clt_minit.setText(info["minit"])
                self.clt_dob.setDate(info["dob"])
                self.clt_NSAdd.setText(info["add_ns"])
                self.clt_BarAdd.setText(info["add_b"])
                self.clt_MuniAdd.setText(info["add_mc"])
                self.clt_ProvAdd.setText(info["add_p"])
                
            self.autofill.close()

        except Exception as e:
            self.conn.rollback()
            print("Error in prefilled_pinfo:", e)

    def load_basic_pinfo_widgets(self):
        self.clt_lname = self.pageMSR.findChild(QLineEdit, "clientLName")
        self.clt_fname = self.pageMSR.findChild(QLineEdit, "clientFname")
        self.clt_minit = self.pageMSR.findChild(QLineEdit, "clientMidI")
        self.clt_dob = self.pageMSR.findChild(QDateEdit, "clientDOB")
        
        self.clt_PNEName = self.pageMSR.findChild(QLineEdit, "PNEName")
        self.clt_PNEContact = self.pageMSR.findChild(QLineEdit, "PNEContact")
        self.clt_PNEAdd = self.pageMSR.findChild(QLineEdit, "PNEAdd")
        
        self.clt_num = self.pageMSR.findChild(QLineEdit, "clientNumMSR")
        self.clt_eduA = self.pageMSR.findChild(QComboBox, "clientEduAtt")
        self.clt_NSAdd = self.pageMSR.findChild(QLineEdit, "clientNSAdd")
        self.clt_BarAdd = self.pageMSR.findChild(QLineEdit, "clientBarAdd")
        self.clt_MuniAdd = self.pageMSR.findChild(QLineEdit, "clientMuniAdd")
        self.clt_ProvAdd = self.pageMSR.findChild(QLineEdit, "clientProvAdd")
    
    def load_basic_pinfo(self):
        try:
            cursor = self.conn.cursor()
            label_to_widget = {
                "Client No.": self.clt_num,
                "Educational Attainment": self.clt_eduA,
                "Name": self.clt_PNEName,
                "Contact No.": self.clt_PNEContact,
                "Address": self.clt_PNEAdd
            }

            for label, widget in label_to_widget.items():
                cursor.execute("""
                    SELECT FR.FORM_RES_VAL
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FO.FORM_OPT_LABEL = %s AND FR.PAT_ID = %s
                """, (label, self.patient_id))
                result = cursor.fetchone()
                if result:
                    value = result[0]
                    if isinstance(widget, QLineEdit):
                        widget.setText(value)
                    elif isinstance(widget, QComboBox):
                        index = widget.findText(value)
                        if index != -1:
                            widget.setCurrentIndex(index)
                            
        except Exception as e:
            print("Error loading basic personal info:", e)
    
    def save_basic_pinfo(self):
        try:
            cursor = self.conn.cursor()
            
            # Create a mapping of widget values to FORM_OPT_LABEL (you must make sure labels match)
            responses = {
                "Client No.": self.clt_num.text(),
                "Educational Attainment": self.clt_eduA.currentText(),
                "Name": self.clt_PNEName.text(),
                "Contact No.": self.clt_PNEContact.text(),
                "Address": self.clt_PNEAdd.text()
            }

            for label, value in responses.items():
                # Fetch FORM_OPT_ID based on label (and maybe category)
                cursor.execute("""
                    SELECT FORM_OPT_ID FROM FORM_OPTION
                    WHERE FORM_OPT_LABEL = %s
                """, (label,))
                opt_result = cursor.fetchone()
                if opt_result:
                    form_opt_id = opt_result[0]

                    # Check if response exists
                    cursor.execute("""
                        SELECT FORM_RES_ID FROM FORM_RESPONSE
                        WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                    """, (form_opt_id, self.patient_id))
                    exists = cursor.fetchone()

                    if exists:
                        # Update existing response
                        cursor.execute("""
                            UPDATE FORM_RESPONSE
                            SET FORM_RES_VAL = %s
                            WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                        """, (value, form_opt_id, self.patient_id))
                    else:
                        # Insert new response
                        cursor.execute("""
                            INSERT INTO FORM_RESPONSE (FORM_RES_VAL, FORM_OPT_ID, PAT_ID)
                            VALUES (%s, %s, %s)
                        """, (value, form_opt_id, self.patient_id))
                else:
                    print(f"[Warning] FORM_OPTION not found for label: {label}")

            self.conn.commit()
        except Exception as e:
            print("Error saving basic personal info:", e)
            self.conn.rollback()

    def load_other_pinfo_widgets(self):
        self.clt_dateArrival = self.pageMSR.findChild(QDateEdit, "clientDateArrival")
        self.clt_timeArrival = self.pageMSR.findChild(QTimeEdit, "clientTimeArrival")
        self.clt_timeDisposition = self.pageMSR.findChild(QTimeEdit, "clientTimeDis")
        self.clt_planMKidsY = self.pageMSR.findChild(QCheckBox, "planMoreKidYes")
        self.clt_planMKidsN = self.pageMSR.findChild(QCheckBox, "planMoreKidNo")
        self.clt_FPMCurY = self.pageMSR.findChild(QCheckBox, "FPMetCurrYes")
        self.clt_FPMCurN = self.pageMSR.findChild(QCheckBox, "FPMetCurrNo")
        self.clt_FPMPrevY = self.pageMSR.findChild(QCheckBox, "FPMetPrevYes")
        self.clt_FPMPrevN = self.pageMSR.findChild(QCheckBox, "FPMetPrevNo")
        self.clt_FPUv = self.pageMSR.findChild(QCheckBox, "FPMETUvss")
        self.clt_FPUi = self.pageMSR.findChild(QCheckBox, "FPMETUiud")
        self.clt_FPUp = self.pageMSR.findChild(QCheckBox, "FPMETUpill")
        self.clt_FPUd = self.pageMSR.findChild(QCheckBox, "FPMETUdmpa")
        self.clt_FPUn = self.pageMSR.findChild(QCheckBox, "FPMETUnfp")
        self.clt_FPUl = self.pageMSR.findChild(QCheckBox, "FPMETUlam")
        self.clt_FPUc = self.pageMSR.findChild(QCheckBox, "FPMETUcondom")
        self.clt_FPUothers = self.pageMSR.findChild(QLineEdit, "FPMETUothers")
        self.clt_PLANS = self.pageMSR.findChild(QTextEdit, "textEditPLANS")
    
    def load_other_pinfo(self):
        try:
            cursor = self.conn.cursor()
            label_to_widget = {
                "Date of Arrival": self.clt_dateArrival,
                "Time of Arrival": self.clt_timeArrival,
                "Time of Disposition": self.clt_timeDisposition,
                "Plan to have more children?": (self.clt_planMKidsY, self.clt_planMKidsN),
                "Current Use": (self.clt_FPMCurY, self.clt_FPMCurN),
                "Previous Use": (self.clt_FPMPrevY, self.clt_FPMPrevN),
                "Others": self.clt_FPUothers,
                "PLANS": self.clt_PLANS
            }

            for label, widget in label_to_widget.items():
                cursor.execute("""
                    SELECT FR.FORM_RES_VAL
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FO.FORM_OPT_LABEL = %s AND FR.PAT_ID = %s
                """, (label, self.patient_id))
                result = cursor.fetchone()
                if result:
                    value = result[0]
                    if isinstance(widget, tuple):  # radio button pairs
                        yes_widget, no_widget = widget
                        yes_widget.setChecked(value == "Yes")
                        no_widget.setChecked(value == "No")
                    elif isinstance(widget, QDateEdit):
                        widget.setDate(QDate.fromString(value, "yyyy-MM-dd"))
                    elif isinstance(widget, QTimeEdit):
                        widget.setTime(QTime.fromString(value, "HH:mm:ss"))
                    elif isinstance(widget, QLineEdit):
                        widget.setText(value)
                    elif isinstance(widget, QTextEdit):
                        widget.setPlainText(value)

            # Load FP Methods Used (multiple checkboxes)
            multi_fp_methods = {
                "VSS": self.clt_FPUv,
                "IUD": self.clt_FPUi,
                "PILL": self.clt_FPUp,
                "DMPA": self.clt_FPUd,
                "NFP": self.clt_FPUn,
                "LAM": self.clt_FPUl,
                "CONDOM": self.clt_FPUc
            }

            for label, checkbox in multi_fp_methods.items():
                cursor.execute("""
                    SELECT FR.FORM_RES_VAL
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FO.FORM_OPT_LABEL = %s AND FR.PAT_ID = %s
                """, (label, self.patient_id))
                result = cursor.fetchone()
                if result:
                    checkbox.setChecked(result[0] == "Yes")

        except Exception as e:
            print("Error loading other personal info:", e)
            
    def save_other_pinfo(self):
        try:
            cursor = self.conn.cursor()
            
            responses = {
                "Date of Arrival": self.clt_dateArrival.date().toString("yyyy-MM-dd"),
                "Time of Arrival": self.clt_timeArrival.time().toString("HH:mm:ss"),
                "Time of Disposition": self.clt_timeDisposition.time().toString("HH:mm:ss"),
                "Plan to have more children?": "Yes" if self.clt_planMKidsY.isChecked() else "No",
                "Current Use": "Yes" if self.clt_FPMCurY.isChecked() else "No",
                "Previous Use": "Yes" if self.clt_FPMPrevY.isChecked() else "No",
                "Others": self.clt_FPUothers.text(),
                "PLANS": self.clt_PLANS.toPlainText()
            }

            # Save single-option responses
            for label, value in responses.items():
                cursor.execute("""
                    SELECT FORM_OPT_ID FROM FORM_OPTION
                    WHERE FORM_OPT_LABEL = %s
                """, (label,))
                opt_result = cursor.fetchone()
                if opt_result:
                    form_opt_id = opt_result[0]

                    cursor.execute("""
                        SELECT FORM_RES_ID FROM FORM_RESPONSE
                        WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                    """, (form_opt_id, self.patient_id))
                    exists = cursor.fetchone()

                    if exists:
                        cursor.execute("""
                            UPDATE FORM_RESPONSE
                            SET FORM_RES_VAL = %s
                            WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                        """, (value, form_opt_id, self.patient_id))
                    else:
                        cursor.execute("""
                            INSERT INTO FORM_RESPONSE (FORM_RES_VAL, FORM_OPT_ID, PAT_ID)
                            VALUES (%s, %s, %s)
                        """, (value, form_opt_id, self.patient_id))
                else:
                    print(f"[Warning] FORM_OPTION not found for label: {label}")

            # Save multiple checkboxes under FP Methods Used
            multi_fp_methods = {
                "VSS": self.clt_FPUv,
                "IUD": self.clt_FPUi,
                "PILL": self.clt_FPUp,
                "DMPA": self.clt_FPUd,
                "NFP": self.clt_FPUn,
                "LAM": self.clt_FPUl,
                "CONDOM": self.clt_FPUc
            }

            for label, checkbox in multi_fp_methods.items():
                is_checked = checkbox.isChecked()
                cursor.execute("""
                    SELECT FORM_OPT_ID FROM FORM_OPTION
                    WHERE FORM_OPT_LABEL = %s
                """, (label,))
                opt_result = cursor.fetchone()
                if opt_result:
                    form_opt_id = opt_result[0]

                    # Check if record exists
                    cursor.execute("""
                        SELECT FORM_RES_ID FROM FORM_RESPONSE
                        WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                    """, (form_opt_id, self.patient_id))
                    exists = cursor.fetchone()

                    if exists:
                        cursor.execute("""
                            UPDATE FORM_RESPONSE
                            SET FORM_RES_VAL = %s
                            WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                        """, ("Yes" if is_checked else "No", form_opt_id, self.patient_id))
                    else:
                        cursor.execute("""
                            INSERT INTO FORM_RESPONSE (FORM_RES_VAL, FORM_OPT_ID, PAT_ID)
                            VALUES (%s, %s, %s)
                        """, ("Yes" if is_checked else "No", form_opt_id, self.patient_id))
                else:
                    print(f"[Warning] FORM_OPTION not found for checkbox: {label}")

            self.conn.commit()
            
        except Exception as e:
            print("Error saving other personal info:", e)
            self.conn.rollback()
            
    def medicalH_info(self):
        self.load_medical_widgets()
        self.load_obstetrical_widgets()
        self.load_medical()
        self.load_obstetrical()
        self.prefilled_obstetrical()
            
    def load_medical_widgets(self):
        self.med_ecN = self.pageMSR.findChild(QCheckBox, "med_ecN")
        self.med_ecY = self.pageMSR.findChild(QCheckBox, "med_ecY")
        self.med_shdN = self.pageMSR.findChild(QCheckBox, "med_shdN")
        self.med_shdY = self.pageMSR.findChild(QCheckBox, "med_shdY")
        self.med_vdN = self.pageMSR.findChild(QCheckBox, "med_vdN")
        self.med_vdY = self.pageMSR.findChild(QCheckBox, "med_vdY")
        self.med_ydN = self.pageMSR.findChild(QCheckBox, "med_ydN")
        self.med_ydY = self.pageMSR.findChild(QCheckBox, "med_ydY")
        self.med_etN = self.pageMSR.findChild(QCheckBox, "med_etN")
        self.med_etY = self.pageMSR.findChild(QCheckBox, "med_etY")
        self.med_scpN = self.pageMSR.findChild(QCheckBox, "med_scpN")
        self.med_scpY = self.pageMSR.findChild(QCheckBox, "med_scpY")
        self.med_sobefN = self.pageMSR.findChild(QCheckBox, "med_sobefN")
        self.med_sobefY = self.pageMSR.findChild(QCheckBox, "med_sobefY")
        self.med_bamN = self.pageMSR.findChild(QCheckBox, "med_bamN")
        self.med_bamY = self.pageMSR.findChild(QCheckBox, "med_bamY")
        self.med_ndN = self.pageMSR.findChild(QCheckBox, "med_ndN")
        self.med_ndY = self.pageMSR.findChild(QCheckBox, "med_ndY")
        self.med_soaaN = self.pageMSR.findChild(QCheckBox, "med_soaaN")
        self.med_soaaY = self.pageMSR.findChild(QCheckBox, "med_soaaY")
        self.med_doaaN = self.pageMSR.findChild(QCheckBox, "med_doaaN")
        self.med_doaaY = self.pageMSR.findChild(QCheckBox, "med_doaaY")
        self.med_fhcN = self.pageMSR.findChild(QCheckBox, "med_fhcN")
        self.med_fhcY = self.pageMSR.findChild(QCheckBox, "med_fhcY")
        self.med_mitaN = self.pageMSR.findChild(QCheckBox, "med_mitaN")
        self.med_mitaY = self.pageMSR.findChild(QCheckBox, "med_mitaY")
        self.med_hogdN = self.pageMSR.findChild(QCheckBox, "med_hogdN")
        self.med_hogdY = self.pageMSR.findChild(QCheckBox, "med_hogdY")
        self.med_holdN = self.pageMSR.findChild(QCheckBox, "med_holdN")
        self.med_holdY = self.pageMSR.findChild(QCheckBox, "med_holdY")
        self.med_psoN = self.pageMSR.findChild(QCheckBox, "med_psoN")
        self.med_psoY = self.pageMSR.findChild(QCheckBox, "med_psoY")
        
        self.med_svN = self.pageMSR.findChild(QCheckBox, "med_svN")
        self.med_svY = self.pageMSR.findChild(QCheckBox, "med_svY")
        self.med_dN = self.pageMSR.findChild(QCheckBox, "med_dN")
        self.med_dY = self.pageMSR.findChild(QCheckBox, "med_dY")
        self.med_sovpN = self.pageMSR.findChild(QCheckBox, "med_sovpN")
        self.med_sovpY = self.pageMSR.findChild(QCheckBox, "med_sovpY")
        self.med_SydN = self.pageMSR.findChild(QCheckBox, "med_SydN")
        self.med_SydY = self.pageMSR.findChild(QCheckBox, "med_SydY")
        self.med_sN = self.pageMSR.findChild(QCheckBox, "med_sN")
        self.med_sY = self.pageMSR.findChild(QCheckBox, "med_sY")
        self.med_aN = self.pageMSR.findChild(QCheckBox, "med_aN")
        self.med_aY = self.pageMSR.findChild(QCheckBox, "med_aY")
        self.med_diN = self.pageMSR.findChild(QCheckBox, "med_diN")
        self.med_diY = self.pageMSR.findChild(QCheckBox, "med_diY")
        self.med_daaaN = self.pageMSR.findChild(QCheckBox, "med_daaaN")
        self.med_daaaY = self.pageMSR.findChild(QCheckBox, "med_daaaY")
        self.med_stdmpN = self.pageMSR.findChild(QCheckBox, "med_stdmpN")
        self.med_stdmpY = self.pageMSR.findChild(QCheckBox, "med_stdmpY")
        self.med_btaN = self.pageMSR.findChild(QCheckBox, "med_btaN")
        self.med_btaY = self.pageMSR.findChild(QCheckBox, "med_btaY")
        self.med_dcaN = self.pageMSR.findChild(QCheckBox, "med_dcaN")
        self.med_dcaY = self.pageMSR.findChild(QCheckBox, "med_dcaY")
    
    def load_medical(self):
        try:
            cursor = self.conn.cursor()
            checkbox_to_widget = {
                "Epilepsy/Convulsion": (self.med_ecN, self.med_ecY),
                "Severe Headache/Dizziness": (self.med_shdN, self.med_shdY),
                "Visual Disturbance": (self.med_vdN, self.med_vdY),
                "Yellowish discoloration": (self.med_ydN, self.med_ydY),
                "Enlarged thyroid": (self.med_etN, self.med_etY),
                
                "Severe chest pain": (self.med_scpN, self.med_scpY),
                "Shortness of breath, easily fatigue": (self.med_sobefN, self.med_sobefY),
                "Breast/axilary masses": (self.med_bamN, self.med_bamY),
                "Nipple discharge (blood or pus)": (self.med_ndN, self.med_ndY),
                "Systolic of 140 and above": (self.med_soaaN, self.med_soaaY),
                "Diastolic of 190 and above": (self.med_doaaN, self.med_doaaY),
                "Family history of CVA (strokes)": (self.med_fhcN, self.med_fhcY),
                
                "Mass in the abdomen": (self.med_mitaN, self.med_mitaY),
                "History of gallbladder disease": (self.med_hogdN, self.med_hogdY),
                "History of liver disease": (self.med_holdN, self.med_holdY),
                "Previous surgical operation": (self.med_psoN, self.med_psoY),
                
                "Severe varicosities": (self.med_svN, self.med_svY),
                "Deformities": (self.med_dN, self.med_dY),
                "Swelling of severe pain in the legs not related to injuries": (self.med_sovpN, self.med_sovpY),
                
                "Skin Yellowish discoloration": (self.med_SydN, self.med_SydY),
                
                "Smoking": (self.med_sN, self.med_sY),
                "Allergies": (self.med_aN, self.med_aY),
                "Drug intake": (self.med_diN, self.med_diY),
                "Drug abuse and alcoholism": (self.med_daaaN, self.med_daaaY),
                "STD, multiple partners": (self.med_stdmpN, self.med_stdmpY),
                "Bleeding tendencies, anemia": (self.med_btaN, self.med_btaY),
                "Diabetes/congenital anomalies": (self.med_dcaN, self.med_dcaY)
            }
            
            for checkbox, widget in checkbox_to_widget.items():
                cursor.execute("""
                    SELECT FR.FORM_RES_VAL
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FO.FORM_OPT_LABEL = %s AND FR.PAT_ID = %s
                """, (checkbox, self.patient_id))
                result = cursor.fetchone()
                if result:
                    value = result[0]
                    if isinstance(widget, tuple):
                        no_widget, yes_widget = widget
                        no_widget.setChecked(value == "No")
                        yes_widget.setChecked(value == "Yes")
            
        except Exception as e:
            print("Error loading medical history:", e)
    
    def save_medical(self):
        try:
            cursor = self.conn.cursor()
            
            mcheckbox = {
                "Epilepsy/Convulsion": "No" if self.med_ecN.isChecked() else "Yes",
                "Severe Headache/Dizziness": "No" if self.med_shdN.isChecked() else "Yes",
                "Visual Disturbance": "No" if self.med_vdN.isChecked() else "Yes",
                "Yellowish discoloration": "No" if self.med_ydN.isChecked() else "Yes",
                "Enlarged thyroid": "No" if self.med_etN.isChecked() else "Yes",
                
                "Severe chest pain": "No" if self.med_scpN.isChecked() else "Yes",
                "Shortness of breath, easily fatigue": "No" if self.med_sobefN.isChecked() else "Yes",
                "Breast/axilary masses": "No" if self.med_bamN.isChecked() else "Yes",
                "Nipple discharge (blood or pus)": "No" if self.med_ndN.isChecked() else "Yes",
                "Systolic of 140 and above": "No" if self.med_soaaN.isChecked() else "Yes",
                "Diastolic of 190 and above": "No" if self.med_doaaN.isChecked() else "Yes",
                "Family history of CVA (strokes)": "No" if self.med_fhcN.isChecked() else "Yes",
                
                "Mass in the abdomen": "No" if self.med_mitaN.isChecked() else "Yes",
                "History of gallbladder disease": "No" if self.med_hogdN.isChecked() else "Yes",
                "History of liver disease": "No" if self.med_holdN.isChecked() else "Yes",
                "Previous surgical operation": "No" if self.med_psoN.isChecked() else "Yes",
                
                "Severe varicosities": "No" if self.med_svN.isChecked() else "Yes",
                "Deformities": "No" if self.med_dN.isChecked() else "Yes",
                "Swelling of severe pain in the legs not related to injuries": "No" if self.med_sovpN.isChecked() else "Yes",
                
                "Skin Yellowish discoloration": "No" if self.med_SydN.isChecked() else "Yes",
                
                "Smoking": "No" if self.med_sN.isChecked() else "Yes",
                "Allergies": "No" if self.med_aN.isChecked() else "Yes",
                "Drug intake": "No" if self.med_diN.isChecked() else "Yes",
                "Drug abuse and alcoholism": "No" if self.med_daaaN.isChecked() else "Yes",
                "STD, multiple partners": "No" if self.med_stdmpN.isChecked() else "Yes",
                "Bleeding tendencies, anemia": "No" if self.med_btaN.isChecked() else "Yes",
                "Diabetes/congenital anomalies": "No" if self.med_dcaN.isChecked() else "Yes"
            }
            
            for checkbox, value in mcheckbox.items():
                cursor.execute("""
                    SELECT FORM_OPT_ID FROM FORM_OPTION
                    WHERE FORM_OPT_LABEL = %s
                """, (checkbox,))
                opt_result = cursor.fetchone()
                if opt_result:
                    form_opt_id = opt_result[0]

                    cursor.execute("""
                        SELECT FORM_RES_ID FROM FORM_RESPONSE
                        WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                    """, (form_opt_id, self.patient_id))
                    exists = cursor.fetchone()

                    if exists:
                        cursor.execute("""
                            UPDATE FORM_RESPONSE
                            SET FORM_RES_VAL = %s
                            WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                        """, (value, form_opt_id, self.patient_id))
                    else:
                        cursor.execute("""
                            INSERT INTO FORM_RESPONSE (FORM_RES_VAL, FORM_OPT_ID, PAT_ID)
                            VALUES (%s, %s, %s)
                        """, (value, form_opt_id, self.patient_id))
                else:
                    print(f"[Warning] FORM_OPTION not found for label: {checkbox}")
            
            self.conn.commit()
        except Exception as e:
            print("Error saving medical history:", e)
    
    def prefilled_obstetrical(self):
        try:
            self.load_obstetrical_widgets()

            if not all([
                self.obs_lmp, 
                self.obs_aog, 
                self.obs_edc            
            ]):
                print("Some input fields are not initialized. Please check objectNames in the UI.")
                return

            info = self.autofill.get_basic_info(self.patient_id)
            if info:
                lmp = info.get("lmp")
                edc = info.get("edc")
                aog = info.get("aog")

                # Set or clear LMP
                if lmp:
                    if isinstance(lmp, date):
                        self.obs_lmp.setDate(QDate(lmp.year, lmp.month, lmp.day))
                    elif isinstance(lmp, QDate):
                        self.obs_lmp.setDate(lmp)
                else:
                    self.obs_lmp.clear()  # clears the date field

                # Set or clear EDC
                if edc:
                    if isinstance(edc, date):
                        self.obs_edc.setDate(QDate(edc.year, edc.month, edc.day))
                    elif isinstance(edc, QDate):
                        self.obs_edc.setDate(edc)
                else:
                    self.obs_edc.clear()

                # Set or clear AOG
                if aog is not None and isinstance(aog, int):
                    self.obs_aog.setValue(aog)
                else:
                    self.obs_aog.clear()  # or setValue(0), depending on behavior you want

            self.autofill.close()

        except Exception as e:
            self.conn.rollback()
            print("Error in prefilled_obstetrical:", e)

            
    def load_obstetrical_widgets(self):
        self.obs_lmp = self.pageMSR.findChild(QDateEdit, "obs_lmp")
        self.obs_aog = self.pageMSR.findChild(QSpinBox, "obs_aog")
        self.obs_edc = self.pageMSR.findChild(QDateEdit, "obs_edc")
        
        self.obs_ft = self.pageMSR.findChild(QSpinBox, "obs_ft")
        self.obs_pt = self.pageMSR.findChild(QSpinBox, "obs_pt")
        self.obs_abort = self.pageMSR.findChild(QSpinBox, "obs_abort")
        self.obs_livekids = self.pageMSR.findChild(QSpinBox, "obs_livekids")
        self.obs_dold = self.pageMSR.findChild(QDateEdit, "obs_dold")
        self.obs_tod = self.pageMSR.findChild(QComboBox, "obs_tod")
        self.obs_pmp = self.pageMSR.findChild(QDateEdit, "obs_pmp")
        
        self.obs_pcsN = self.pageMSR.findChild(QCheckBox, "obs_pcsN")
        self.obs_pcsY = self.pageMSR.findChild(QCheckBox, "obs_pcsY")
        self.obs_3cmN = self.pageMSR.findChild(QCheckBox, "obs_3cmN")
        self.obs_3cmY = self.pageMSR.findChild(QCheckBox, "obs_3cmY")
        self.obs_ephN = self.pageMSR.findChild(QCheckBox, "obs_ephN")
        self.obs_ephY = self.pageMSR.findChild(QCheckBox, "obs_ephY")
        self.obs_phN = self.pageMSR.findChild(QCheckBox, "obs_phN")
        self.obs_phY = self.pageMSR.findChild(QCheckBox, "obs_phY")
        self.obs_fdN = self.pageMSR.findChild(QCheckBox, "obs_fdN")
        self.obs_fdY = self.pageMSR.findChild(QCheckBox, "obs_fdY")
        self.obs_pihN = self.pageMSR.findChild(QCheckBox, "obs_pihN")
        self.obs_pihY = self.pageMSR.findChild(QCheckBox, "obs_pihY")
        self.obs_wobN = self.pageMSR.findChild(QCheckBox, "obs_wobN")
        self.obs_wobY = self.pageMSR.findChild(QCheckBox, "obs_wobY")
    
    def load_obstetrical(self):
        try:
            cursor = self.conn.cursor()
            label_to_widget = {
                "Full Term": self.obs_ft,
                "Preterm": self.obs_pt,
                "Abortion": self.obs_abort,
                "Living children": self.obs_livekids,
                "Date of last delivery": self.obs_dold,
                "Type of Delivery": self.obs_tod,
                "Past Menstrual Period": self.obs_pmp,
                
                "Previous Cesarean Section": (self.obs_pcsN, self.obs_pcsY),
                "3 Consecutive Miscarriages": (self.obs_3cmN, self.obs_3cmY),
                "Ectopic Pregnancy/H.mole": (self.obs_ephN, self.obs_ephY),
                "Postpartum hemorrhage": (self.obs_phN, self.obs_phY),
                "Forceps delivery": (self.obs_fdN, self.obs_fdY),
                "Pregnancy Induced Hypertension": (self.obs_pihN, self.obs_pihY),
                "Weight of baby > 4kgs": (self.obs_wobN, self.obs_wobY),
            }

            for label, widget in label_to_widget.items():
                cursor.execute("""
                    SELECT FR.FORM_RES_VAL
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FO.FORM_OPT_LABEL = %s AND FR.PAT_ID = %s
                """, (label, self.patient_id))
                result = cursor.fetchone()
                if result:
                    value = result[0]
                    if isinstance(widget, QSpinBox):
                        widget.setValue(int(value))
                    elif isinstance(widget, QDateEdit):
                        widget.setDate(QDate.fromString(value, "MM-dd-yyyy"))
                    elif isinstance(widget, QComboBox):
                        index = widget.findText(value)
                        if index != -1:
                            widget.setCurrentIndex(index)
                    elif isinstance(widget, tuple):  # radio button pairs
                        no_widget, yes_widget = widget
                        no_widget.setChecked(value == "No")
                        yes_widget.setChecked(value == "Yes")

        except Exception as e:
            print("Error loading obstetrical:", e)
    
    def save_obstetrical(self):
        try:
            cursor = self.conn.cursor()
            
            responses = {
                "Full Term": str(self.obs_ft.value()),
                "Preterm": str(self.obs_pt.value()),
                "Abortion": str(self.obs_abort.value()),
                "Living children": str(self.obs_livekids.value()),
                "Date of last delivery": self.obs_dold.date().toString("MM-dd-yyyy"),
                "Type of Delivery": self.obs_tod.currentText(), 
                "Past Menstrual Period": self.obs_pmp.date().toString("MM-dd-yyyy"),
                
                "Previous Cesarean Section": "No" if self.obs_pcsN.isChecked() else "Yes",
                "3 Consecutive Miscarriages": "No" if self.obs_3cmN.isChecked() else "Yes",
                "Ectopic Pregnancy/H.mole": "No" if self.obs_ephN.isChecked() else "Yes",
                "Postpartum hemorrhage": "No" if self.obs_phN.isChecked() else "Yes",
                "Forceps delivery": "No" if self.obs_fdN.isChecked() else "Yes",
                "Pregnancy Induced Hypertension": "No" if self.obs_pihN.isChecked() else "Yes",
                "Weight of baby > 4kgs": "No" if self.obs_wobN.isChecked() else "Yes",
            }

            # Save single-option responses
            for label, value in responses.items():
                cursor.execute("""
                    SELECT FORM_OPT_ID FROM FORM_OPTION
                    WHERE FORM_OPT_LABEL = %s
                """, (label,))
                opt_result = cursor.fetchone()
                if opt_result:
                    form_opt_id = opt_result[0]

                    cursor.execute("""
                        SELECT FORM_RES_ID FROM FORM_RESPONSE
                        WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                    """, (form_opt_id, self.patient_id))
                    exists = cursor.fetchone()

                    if exists:
                        cursor.execute("""
                            UPDATE FORM_RESPONSE
                            SET FORM_RES_VAL = %s
                            WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                        """, (value, form_opt_id, self.patient_id))
                    else:
                        cursor.execute("""
                            INSERT INTO FORM_RESPONSE (FORM_RES_VAL, FORM_OPT_ID, PAT_ID)
                            VALUES (%s, %s, %s)
                        """, (value, form_opt_id, self.patient_id))
                else:
                    print(f"[Warning] FORM_OPTION not found for label: {label}")

            self.conn.commit()
        except Exception as e:
            print("Error saving obstetrical:", e)
            self.conn.rollback()
    
    def physicalE_info(self):
        self.load_physicalE_widgets()
        self.load_pelvicE_widgets()
        self.load_physicalE()
        self.load_pelvicE()
    
    def load_physicalE_widgets(self):
        self.phye_bps = self.pageMSR.findChild(QSpinBox, "phye_bps")
        self.phye_bpd = self.pageMSR.findChild(QSpinBox, "phye_bpd")
        self.phye_weight = self.pageMSR.findChild(QDoubleSpinBox, "phye_weight")
        self.phye_height = self.pageMSR.findChild(QDoubleSpinBox, "phye_height")
        self.phye_bloodt = self.pageMSR.findChild(QComboBox, "phye_bloodt")
        
        self.phye_pN = self.pageMSR.findChild(QCheckBox, "phye_pN")
        self.phye_pY = self.pageMSR.findChild(QCheckBox, "phye_pY")
        self.phye_yN = self.pageMSR.findChild(QCheckBox, "phye_yN")
        self.phye_yY = self.pageMSR.findChild(QCheckBox, "phye_yY")
        self.phye_etN = self.pageMSR.findChild(QCheckBox, "phye_etN")
        self.phye_etY = self.pageMSR.findChild(QCheckBox, "phye_etY")
        self.phye_elnN = self.pageMSR.findChild(QCheckBox, "phye_elnN")
        self.phye_elnY = self.pageMSR.findChild(QCheckBox, "phye_elnY")
        self.phye_mN = self.pageMSR.findChild(QCheckBox, "phye_mN")
        self.phye_mY = self.pageMSR.findChild(QCheckBox, "phye_mY")
        self.phye_ndN = self.pageMSR.findChild(QCheckBox, "phye_ndN")
        self.phye_ndY = self.pageMSR.findChild(QCheckBox, "phye_ndY")
        self.phye_sodN = self.pageMSR.findChild(QCheckBox, "phye_sodN")
        self.phye_sodY = self.pageMSR.findChild(QCheckBox, "phye_sodY")
        self.phye_ealnN = self.pageMSR.findChild(QCheckBox, "phye_ealnN")
        self.phye_ealnY = self.pageMSR.findChild(QCheckBox, "phye_ealnY")
        self.phye_ahscrN = self.pageMSR.findChild(QCheckBox, "phye_ahscrN")
        self.phye_ahscrY = self.pageMSR.findChild(QCheckBox, "phye_ahscrY")
        self.phye_ahsrrN = self.pageMSR.findChild(QCheckBox, "phye_ahsrrN")
        self.phye_ahsrrY = self.pageMSR.findChild(QCheckBox, "phye_ahsrrY")
        
        self.phye_fhic = self.pageMSR.findChild(QDoubleSpinBox, "phye_fhic")
        self.phye_fht = self.pageMSR.findChild(QSpinBox, "phye_fht")
        self.phye_fm = self.pageMSR.findChild(QComboBox, "phye_fm")
        
        self.phye_fpitf = self.pageMSR.findChild(QComboBox, "phye_fpitf")
        self.phye_pofb = self.pageMSR.findChild(QComboBox, "phye_pofb")
        self.phye_pp = self.pageMSR.findChild(QComboBox, "phye_pp")
        self.phye_sopp = self.pageMSR.findChild(QComboBox, "phye_sopp")
        self.phye_ua = self.pageMSR.findChild(QComboBox, "phye_ua")
        
        self.phye_cc = self.pageMSR.findChild(QComboBox, "phye_cc")
        self.phye_cd = self.pageMSR.findChild(QSpinBox, "phye_cd")
        self.phye_ppp = self.pageMSR.findChild(QComboBox, "phye_ppp")
        self.phye_sobow = self.pageMSR.findChild(QComboBox, "phye_sobow")
    
    def load_physicalE(self):
        try:
            cursor = self.conn.cursor()
            field_to_widget = {
                "Blood Pressure: Systolic": self.phye_bps,
                "Blood Pressure: Diastolic": self.phye_bpd,
                "Weight": self.phye_weight,
                "Height": self.phye_height,
                "Blood Type": self.phye_bloodt,
                
                "Pale": (self.phye_pN, self.phye_pY),
                "Yellowish": (self.phye_yN, self.phye_yY),
                "Enlarged Thyroid": (self.phye_etN, self.phye_etY),
                "Enlarged lymph nodes": (self.phye_elnN, self.phye_elnY),
                "Mass": (self.phye_mN, self.phye_mY),
                "Nipple discharge": (self.phye_ndN, self.phye_ndY),
                "Skin-orange-peel or dimpling": (self.phye_sodN, self.phye_sodY),
                "Enlarged axillary lymph nodes": (self.phye_ealnN, self.phye_ealnY),
                "Abnormal heart sounds/cardiac rate": (self.phye_ahscrN, self.phye_ahscrY),
                "Abnormal health sounds/respiratory rate": (self.phye_ahsrrN, self.phye_ahsrrY),
                
                "Fundic height in cms.": self.phye_fhic,
                "Fetal heart tone": self.phye_fht,
                "Fetal movement": self.phye_fm,
                
                "Fetal part in the fundus": self.phye_fpitf,
                "Position of Fetal Back": self.phye_pofb,
                "Presenting Part": self.phye_pp,
                "Status of Presenting Part": self.phye_sopp,
                "Uterine Activity": self.phye_ua,
                
                "Cervix Consistency": self.phye_cc,
                "Cervix Dilatation": self.phye_cd,
                "Palpable Presenting Part": self.phye_ppp,
                "Status of Bag of Water": self.phye_sobow
            }
            
            for field, widget in field_to_widget.items():
                cursor.execute("""
                    SELECT FR.FORM_RES_VAL
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FO.FORM_OPT_LABEL = %s AND FR.PAT_ID = %s
                """, (field, self.patient_id))
                result = cursor.fetchone()
                if result:
                    value = result[0]
                    if isinstance(widget, QSpinBox):
                        widget.setValue(int(value))
                    elif isinstance(widget, QDoubleSpinBox):
                        widget.setValue(float(value))
                    elif isinstance(widget, QComboBox):
                        index = widget.findText(value)
                        if index != -1:
                            widget.setCurrentIndex(index)
                    elif isinstance(widget, tuple):  # Checkbox pair
                        no_cb, yes_cb = widget
                        no_cb.setChecked(value == "No")
                        yes_cb.setChecked(value == "Yes")
            
        except Exception as e:
            print("Error loading physical examination:", e)
            
    def save_physicalE(self):
        try:
            cursor = self.conn.cursor()
            
            responses = {
                "Blood Pressure: Systolic": str(self.phye_bps.value()),
                "Blood Pressure: Diastolic": str(self.phye_bpd.value()),
                "Weight": str(self.phye_weight.value()),
                "Height": str(self.phye_height.value()),
                "Blood Type": self.phye_bloodt.currentText(),

                "Pale": "No" if self.phye_pN.isChecked() else "Yes",
                "Yellowish": "No" if self.phye_yN.isChecked() else "Yes",
                "Enlarged Thyroid": "No" if self.phye_etN.isChecked() else "Yes",
                "Enlarged lymph nodes": "No" if self.phye_elnN.isChecked() else "Yes",
                "Mass": "No" if self.phye_mN.isChecked() else "Yes",
                "Nipple discharge": "No" if self.phye_ndN.isChecked() else "Yes",
                "Skin-orange-peel or dimpling": "No" if self.phye_sodN.isChecked() else "Yes",
                "Enlarged axillary lymph nodes": "No" if self.phye_ealnN.isChecked() else "Yes",
                "Abnormal heart sounds/cardiac rate": "No" if self.phye_ahscrN.isChecked() else "Yes",
                "Abnormal health sounds/respiratory rate": "No" if self.phye_ahsrrN.isChecked() else "Yes",

                "Fundic height in cms.": str(self.phye_fhic.value()),
                "Fetal heart tone": str(self.phye_fht.value()),
                "Fetal movement": self.phye_fm.currentText(),

                "Fetal part in the fundus": self.phye_fpitf.currentText(),
                "Position of Fetal Back": self.phye_pofb.currentText(),
                "Presenting Part": self.phye_pp.currentText(),
                "Status of Presenting Part": self.phye_sopp.currentText(),
                "Uterine Activity": self.phye_ua.currentText(),

                "Cervix Consistency": self.phye_cc.currentText(),
                "Cervix Dilatation": str(self.phye_cd.value()),
                "Palpable Presenting Part": self.phye_ppp.currentText(),
                "Status of Bag of Water": self.phye_sobow.currentText()
            }

            # Save single-option responses
            for label, value in responses.items():
                cursor.execute("""
                    SELECT FORM_OPT_ID FROM FORM_OPTION
                    WHERE FORM_OPT_LABEL = %s
                """, (label,))
                opt_result = cursor.fetchone()
                if opt_result:
                    form_opt_id = opt_result[0]

                    cursor.execute("""
                        SELECT FORM_RES_ID FROM FORM_RESPONSE
                        WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                    """, (form_opt_id, self.patient_id))
                    exists = cursor.fetchone()

                    if exists:
                        cursor.execute("""
                            UPDATE FORM_RESPONSE
                            SET FORM_RES_VAL = %s
                            WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                        """, (value, form_opt_id, self.patient_id))
                    else:
                        cursor.execute("""
                            INSERT INTO FORM_RESPONSE (FORM_RES_VAL, FORM_OPT_ID, PAT_ID)
                            VALUES (%s, %s, %s)
                        """, (value, form_opt_id, self.patient_id))
                else:
                    print(f"[Warning] FORM_OPTION not found for label: {label}")

            self.conn.commit()
        except Exception as e:
            print("Error saving physical examination:", e)
            self.conn.rollback()
    
    def load_pelvicE_widgets(self):
        self.pelv_sN = self.pageMSR.findChild(QCheckBox, "pelv_sN")
        self.pelv_sY = self.pageMSR.findChild(QCheckBox, "pelv_sY")
        self.pelv_wmN = self.pageMSR.findChild(QCheckBox, "pelv_wmN")
        self.pelv_wmY = self.pageMSR.findChild(QCheckBox, "pelv_wmY")
        self.pelv_lacN = self.pageMSR.findChild(QCheckBox, "pelv_lacN")
        self.pelv_lacY = self.pageMSR.findChild(QCheckBox, "pelv_lacY")
        self.pelv_sevaN = self.pageMSR.findChild(QCheckBox, "pelv_sevaN")
        self.pelv_sevaY = self.pageMSR.findChild(QCheckBox, "pelv_sevaY")
        
        self.pelv_bcN = self.pageMSR.findChild(QCheckBox, "pelv_bcN")
        self.pelv_bcY = self.pageMSR.findChild(QCheckBox, "pelv_bcY")
        self.pelv_wsgdN = self.pageMSR.findChild(QCheckBox, "pelv_wsgdN")
        self.pelv_wsgdY = self.pageMSR.findChild(QCheckBox, "pelv_wsgdY")
        self.pelv_crN = self.pageMSR.findChild(QCheckBox, "pelv_crN")
        self.pelv_crY = self.pageMSR.findChild(QCheckBox, "pelv_crY")
        self.pelv_pdbN = self.pageMSR.findChild(QCheckBox, "pelv_pdbN")
        self.pelv_pdbY = self.pageMSR.findChild(QCheckBox, "pelv_pdbY")
        self.pelv_epfN = self.pageMSR.findChild(QCheckBox, "pelv_epfN")
        self.pelv_epfY = self.pageMSR.findChild(QCheckBox, "pelv_epfY")
        
    def load_pelvicE(self):
        try:
            cursor = self.conn.cursor()
            checkbox_to_widget = {
                "Scars": (self.pelv_sN, self.pelv_sY),
                "Warts/mass": (self.pelv_wmN, self.pelv_wmY),
                "Laceration": (self.pelv_lacN, self.pelv_lacY),
                "Pelvic Severe Varicosities": (self.pelv_sevaN, self.pelv_sevaY),
                
                "Bartholins cyst": (self.pelv_bcN, self.pelv_bcY),
                "Warts/Skenes gland discharge": (self.pelv_wsgdN, self.pelv_wsgdY),
                "Cystocele/rectocele": (self.pelv_crN, self.pelv_crY),
                "Purulent discharge/bleeding": (self.pelv_pdbN, self.pelv_pdbY),
                "Erosion/polyp/foreign body": (self.pelv_epfN, self.pelv_epfY)
            }
            
            for checkbox, widget in checkbox_to_widget.items():
                cursor.execute("""
                    SELECT FR.FORM_RES_VAL
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FO.FORM_OPT_LABEL = %s AND FR.PAT_ID = %s
                """, (checkbox, self.patient_id))
                result = cursor.fetchone()
                if result:
                    value = result[0]
                    if isinstance(widget, tuple):
                        no_widget, yes_widget = widget
                        no_widget.setChecked(value == "No")
                        yes_widget.setChecked(value == "Yes")
            
        except Exception as e:
            print("Error loading pelvic examination:", e)
            
    def save_pelvicE(self):
        try:
            cursor = self.conn.cursor()
            
            pelvEcheckbox = {
                "Scars": "No" if self.pelv_sN.isChecked() else "Yes",
                "Warts/mass": "No" if self.pelv_wmN.isChecked() else "Yes",
                "Laceration": "No" if self.pelv_lacN.isChecked() else "Yes",
                "Pelvic Severe Varicosities": "No" if self.pelv_sevaN.isChecked() else "Yes",
                
                "Bartholins cyst": "No" if self.pelv_bcN.isChecked() else "Yes",
                "Warts/Skenes gland discharge": "No" if self.pelv_wsgdN.isChecked() else "Yes",
                "Cystocele/rectocele": "No" if self.pelv_crN.isChecked() else "Yes",
                "Purulent discharge/bleeding": "No" if self.pelv_pdbN.isChecked() else "Yes",
                "Erosion/polyp/foreign body": "No" if self.pelv_epfN.isChecked() else "Yes",
            }
            
            for checkbox, value in pelvEcheckbox.items():
                cursor.execute("""
                    SELECT FORM_OPT_ID FROM FORM_OPTION
                    WHERE FORM_OPT_LABEL = %s
                """, (checkbox,))
                opt_result = cursor.fetchone()
                if opt_result:
                    form_opt_id = opt_result[0]

                    cursor.execute("""
                        SELECT FORM_RES_ID FROM FORM_RESPONSE
                        WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                    """, (form_opt_id, self.patient_id))
                    exists = cursor.fetchone()

                    if exists:
                        cursor.execute("""
                            UPDATE FORM_RESPONSE
                            SET FORM_RES_VAL = %s
                            WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                        """, (value, form_opt_id, self.patient_id))
                    else:
                        cursor.execute("""
                            INSERT INTO FORM_RESPONSE (FORM_RES_VAL, FORM_OPT_ID, PAT_ID)
                            VALUES (%s, %s, %s)
                        """, (value, form_opt_id, self.patient_id))
                else:
                    print(f"[Warning] FORM_OPTION not found for label: {checkbox}")
            
            self.conn.commit()
        except Exception as e:
            print("Error saving pelvic examination:", e)
            
    def birthEPlan_info(self):
        self.load_birthEPlan_widgets()
        self.load_birthEPlan()
        self.prefilled_birthEPlan()
    
    def load_birthEPlan_widgets(self):
        self.bep_ptnn = self.pageMSR.findChild(QLineEdit, "bep_ptnn")
        self.bep_ptna = self.pageMSR.findChild(QLineEdit, "bep_ptna")
        self.bep_ptnc = self.pageMSR.findChild(QLineEdit, "bep_ptnc")
            
        self.bep_ptnr = self.pageMSR.findChild(QLineEdit, "bep_ptnr")
        
        self.bep_dan = self.pageMSR.findChild(QLineEdit, "bep_dan")
        self.bep_dfna = self.pageMSR.findChild(QLineEdit, "bep_dfna")
        self.bep_dfpaY = self.pageMSR.findChild(QCheckBox, "bep_dfpaY")
        self.bep_dfpaN = self.pageMSR.findChild(QCheckBox, "bep_dfpaN")
        self.bep_dfmpc = self.pageMSR.findChild(QLineEdit, "bep_dfmpc")
        self.bep_dft = self.pageMSR.findChild(QLineEdit, "bep_dft")
        
        self.bep_cnn = self.pageMSR.findChild(QLineEdit, "bep_cnn")
        self.bep_cn = self.pageMSR.findChild(QLineEdit, "bep_cn")
        self.bep_can = self.pageMSR.findChild(QLineEdit, "bep_can")
        self.bep_dn1 = self.pageMSR.findChild(QLineEdit, "bep_dn1")
        self.bep_dn2 = self.pageMSR.findChild(QLineEdit, "bep_dn2")
        self.bep_rf = self.pageMSR.findChild(QLineEdit, "bep_rf")
    
    def prefilled_birthEPlan(self):
        try:
            self.load_birthEPlan_widgets()
            self.load_basic_pinfo()

            # List of fields to check and prefill
            fields = {
                self.clt_PNEName: self.bep_ptnn,
                self.clt_PNEAdd: self.bep_ptna,
                self.clt_PNEContact: self.bep_ptnc
            }

            for clt_field, bep_field in fields.items():
                if clt_field:
                    bep_field.setText(clt_field.text())
                else:
                    print(f"Warning: {clt_field} is None.")
            
        except Exception as e:
            print("Error prefilling birth plan data:", e)
        
    def load_birthEPlan(self):
        try:
            cursor = self.conn.cursor()
            label_to_widget = {
                "BEPPerson to Notify: Relationship": self.bep_ptnr,
                
                "BEPDelivery Attendant Name": self.bep_dan,
                "BEPDelivery Facility Name or Address": self.bep_dfna,
                "BEPDelivery Facility: PhilHealth accredited": (self.bep_dfpaY, self.bep_dfpaN),
                "BEPDelivery Facility Maternal Package Cost": self.bep_dfmpc,
                "BEPDelivery Facility Transportation": self.bep_dft,
                
                "BEPContact Name/Number": self.bep_cnn,
                "BEPCompanion Name": self.bep_cn,
                "BEPChildren Attendant Name": self.bep_can,
                "BEPDonor Name 1": self.bep_dn1,
                "BEPDonor Name 2": self.bep_dn2,
                "BEPReferred Facility": self.bep_rf
            }

            for label, widget in label_to_widget.items():
                cursor.execute("""
                    SELECT FR.FORM_RES_VAL
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FO.FORM_OPT_LABEL = %s AND FR.PAT_ID = %s
                """, (label, self.patient_id))
                result = cursor.fetchone()
                if result:
                    value = result[0]
                    if isinstance(widget, QLineEdit):
                        widget.setText(value)
                    elif isinstance(widget, tuple):  # radio button pairs
                        yes_widget, no_widget = widget
                        yes_widget.setChecked(value == "Yes")
                        no_widget.setChecked(value == "No")
    
        except Exception as e:
            print("Error loading other personal info:", e)
            
    def save_birthEPlan(self):
        try:
            cursor = self.conn.cursor()
            
            birthEPlan = {
                "BEPPerson to Notify: Relationship": self.bep_ptnr.text(),
                
                "BEPDelivery Attendant Name": self.bep_dan.text(),
                "BEPDelivery Facility Name or Address": self.bep_dfna.text(),
                "BEPDelivery Facility: PhilHealth accredited": "Yes" if self.bep_dfpaY.isChecked() else "No",
                "BEPDelivery Facility Maternal Package Cost": self.bep_dfmpc.text(),
                "BEPDelivery Facility Transportation": self.bep_dft.text(),
                
                "BEPContact Name/Number": self.bep_cnn.text(),
                "BEPCompanion Name": self.bep_cn.text(),
                "BEPChildren Attendant Name": self.bep_can.text(),
                "BEPDonor Name 1": self.bep_dn1.text(),
                "BEPDonor Name 2": self.bep_dn2.text(),
                "BEPReferred Facility": self.bep_rf.text()
            }

            # Save single-option responses
            for bep, value in birthEPlan.items():
                cursor.execute("""
                    SELECT FORM_OPT_ID FROM FORM_OPTION
                    WHERE FORM_OPT_LABEL = %s
                """, (bep,))
                opt_result = cursor.fetchone()
                if opt_result:
                    form_opt_id = opt_result[0]

                    cursor.execute("""
                        SELECT FORM_RES_ID FROM FORM_RESPONSE
                        WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                    """, (form_opt_id, self.patient_id))
                    exists = cursor.fetchone()

                    if exists:
                        cursor.execute("""
                            UPDATE FORM_RESPONSE
                            SET FORM_RES_VAL = %s
                            WHERE FORM_OPT_ID = %s AND PAT_ID = %s
                        """, (value, form_opt_id, self.patient_id))
                    else:
                        cursor.execute("""
                            INSERT INTO FORM_RESPONSE (FORM_RES_VAL, FORM_OPT_ID, PAT_ID)
                            VALUES (%s, %s, %s)
                        """, (value, form_opt_id, self.patient_id))
                else:
                    print(f"[Warning] FORM_OPTION not found for label: {bep}")
            
            self.conn.commit()
            
            print("Birth Emergency Plan saved successfully.")
        except Exception as e:
            print("Error saving other personal info:", e)
            self.conn.rollback()

    def on_save_clicked(self):
        reply = QMessageBox.question(
            self.pageMSR,
            "Confirm Save",
            "Are you sure you want to save the changes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.save_all_page()
            self.set_all_fields_read_only()

    def on_cancel_clicked(self):
        reply = QMessageBox.question(
            self.pageMSR,
            "Confirm Cancel",
            "Are you sure you want to cancel? Unsaved changes will be lost.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.cancel_editing()

    def reset_fields(self):
        #Basic Personal Information Category
        self.clt_num.clear()
        self.clt_eduA.setCurrentIndex(-1)
        self.clt_PNEName.clear()
        self.clt_PNEContact.clear()
        self.clt_PNEAdd.clear()
        
        #Other Personal Information Category
        self.clt_dateArrival.setDate(date.today())
        self.clt_timeArrival.clear()
        self.clt_timeDisposition.clear()
        
        for otherp_chk in [
            self.clt_planMKidsY, self.clt_planMKidsN,
            self.clt_FPMCurY, self.clt_FPMCurN,
            self.clt_FPMPrevY, self.clt_FPMPrevN,
            self.clt_FPUv, self.clt_FPUi, self.clt_FPUp,
            self.clt_FPUd, self.clt_FPUn, self.clt_FPUl,
            self.clt_FPUc
        ]:
            otherp_chk.setChecked(False)
        
        self.clt_FPUothers.clear()
        self.clt_PLANS.clear()
        
        #Medical History Category
        for med_chk in [
            self.med_ecN, self.med_shdN, self.med_vdN, self.med_ydN, self.med_etN,
            self.med_ecY, self.med_shdY, self.med_vdY, self.med_ydY, self.med_etY,
            
            self.med_scpN, self.med_sobefN, self.med_bamN, self.med_ndN, self.med_soaaN, self.med_doaaN, self.med_fhcN,
            self.med_scpY, self.med_sobefY, self.med_bamY, self.med_ndY, self.med_soaaY, self.med_doaaY, self.med_fhcY,
            
            self.med_mitaN, self.med_hogdN, self.med_holdN, self.med_psoN, 
            self.med_mitaY, self.med_hogdY, self.med_holdY, self.med_psoY,
            
            self.med_svN, self.med_dN, self.med_sovpN,
            self.med_svY, self.med_dY, self.med_sovpY,
            
            self.med_SydN, self.med_SydY, 
            
            self.med_sN, self.med_aN, self.med_diN, self.med_daaaN, self.med_stdmpN, self.med_btaN, self.med_dcaN,
            self.med_sY, self.med_aY, self.med_diY, self.med_daaaY, self.med_stdmpY, self.med_btaY, self.med_dcaY
        ]:
            med_chk.setChecked(False)
        
        #Obstetrical History Category
        self.obs_ft.setValue(0)
        self.obs_pt.setValue(0)
        self.obs_abort.setValue(0)
        self.obs_livekids.setValue(0)
        
        self.obs_dold.setDate(date.today())
        self.obs_tod.setCurrentIndex(0)
        self.obs_pmp.setDate(date.today())
        
        for obs_chk in [
            self.obs_pcsN, self.obs_3cmN, self.obs_ephN, self.obs_phN, self.obs_fdN, self.obs_pihN, self.obs_wobN,
            self.obs_pcsY, self.obs_3cmY, self.obs_ephY, self.obs_phY, self.obs_fdY, self.obs_pihY, self.obs_wobY
        ]:
            obs_chk.setChecked(False)
            
        #Physical Examination Category
        self.phye_bps.setValue(0)
        self.phye_bpd.setValue(0)
        self.phye_weight.setValue(0)
        self.phye_height.setValue(0)
        self.phye_bloodt.setCurrentIndex(0)
        
        for phye_chk in [
            self.phye_pN, self.phye_yN, self.phye_etN, self.phye_elnN, self.phye_mN, self.phye_ndN, 
            self.phye_pY, self.phye_yY, self.phye_etY, self.phye_elnY, self.phye_mY, self.phye_ndY,
            self.phye_sodY, self.phye_ealnY, self.phye_ahscrY, self.phye_ahsrrY,
            self.phye_sodN, self.phye_ealnN, self.phye_ahscrN, self.phye_ahsrrN
        ]:
            phye_chk.setChecked(False)
        
        self.phye_fhic.setValue(0)
        self.phye_fht.setValue(0)
        self.phye_fm.setCurrentIndex(0)
        
        self.phye_fpitf.setCurrentIndex(0)
        self.phye_pofb.setCurrentIndex(0)
        self.phye_pp.setCurrentIndex(0)
        self.phye_sopp.setCurrentIndex(0)
        self.phye_ua.setCurrentIndex(0)
        
        self.phye_cc.setCurrentIndex(0)
        self.phye_cd.setValue(0)
        self.phye_ppp.setCurrentIndex(0)
        self.phye_sobow.setCurrentIndex(0)
        
        #Pelvic Examination Category
        for pelvE_chk in [
            self.pelv_sN, self.pelv_wmN, self.pelv_lacN, self.pelv_sevaN,
            self.pelv_sY, self.pelv_wmY, self.pelv_lacY, self.pelv_sevaY,
            self.pelv_bcN, self.pelv_wsgdN, self.pelv_crN, self.pelv_pdbN, self.pelv_epfN,
            self.pelv_bcY, self.pelv_wsgdY, self.pelv_crY, self.pelv_pdbY, self.pelv_epfY
        ]:
            pelvE_chk.setChecked(False)
            
        #Birth and Emergency Plan Category
        self.bep_ptnr.clear()

        self.bep_dan.clear()
        self.bep_dfna.clear()
        self.bep_dfpaY.setChecked(False)
        self.bep_dfpaN.setChecked(False)
        self.bep_dfmpc.clear()
        self.bep_dft.clear()

        self.bep_cnn.clear()
        self.bep_cn.clear()
        self.bep_can.clear()
        self.bep_dn1.clear()
        self.bep_dn2.clear()
        self.bep_rf.clear()
    
    def cancel_editing(self):
        self.reset_fields()
        self.set_all_fields_read_only()
        self.prefilled_pinfo()
        self.prefilled_obstetrical()
        self.load_basic_pinfo()
        self.load_other_pinfo()
        self.load_medical()
        self.load_obstetrical()
        self.load_physicalE()
        self.load_pelvicE()
        self.load_birthEPlan()
    
    def show_pdfPrint(self):
        # Button: app → open filled PDF in browser
        self.view_filled_pdf()

    def fetch_patient_data(self):
        # Fetch patient data from the database
        try:
            cursor = self.conn.cursor()
            
            data = {}
            
            cursor.execute("""
                SELECT
                    CONCAT(
                        PAT_FNAME, ' ',
                        CASE
                            WHEN PAT_MNAME IS NOT NULL AND PAT_MNAME != ''
                                THEN CONCAT(LEFT(PAT_MNAME, 1), '. ')
                            ELSE ''
                        END,
                        PAT_LNAME
                    ) AS PATIENT_NAME,
                    TO_CHAR(PAT_LMP, 'MM-DD-YYYY') AS lmp, PAT_AOG, 
                    TO_CHAR(PAT_EDC, 'MM-DD-YYYY') AS edc
                FROM PATIENT
                WHERE PAT_ID = %s
            """, (self.patient_id,))
            patient_data = cursor.fetchone()

            if patient_data:
                data["PatientName"] = (patient_data[0] or "").upper()
                data["lmp"] = patient_data[1]
                data["aog"] = patient_data[2] or ""
                data["edc"] = patient_data[3]
            else:
                print("No data found for the patient for Maternal.")
            
            cursor.execute("""
                SELECT
                    CONCAT(
                        COALESCE(
                            (SELECT FR.FORM_RES_VAL FROM FORM_RESPONSE FR
                            JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                            WHERE FO.FORM_OPT_LABEL = 'Blood Pressure: Systolic' AND FR.PAT_ID = P.PAT_ID
                            ), ''
                        ),
                        '/',
                        COALESCE(
                            (SELECT FR.FORM_RES_VAL FROM FORM_RESPONSE FR
                            JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                            WHERE FO.FORM_OPT_LABEL = 'Blood Pressure: Diastolic' AND FR.PAT_ID = P.PAT_ID
                            ), ''
                        )
                    ) AS CONCATENATED_FORM_RESPONSES
                FROM PATIENT P
                WHERE P.PAT_ID = %s
            """, (self.patient_id,))
            patient_data = cursor.fetchone()

            if patient_data:
                data["bps"] = patient_data[0] or ""
            else:
                print("No data found for the patient for maternal.")

            label_to_field = {
                "PLANS": "plans",
                
                "Epilepsy/Convulsion": ("epiconvulsionY", "epiconvulsionN"),
                "Severe Headache/Dizziness": ("svhdizzinesY", "svhdizzinesN"),
                "Visual Disturbance": ("vdisturbanceY", "vdisturbanceN"),
                "Yellowish discoloration": ("ydiscolorY", "ydiscolorN"),
                "Enlarged thyroid": ("ethyroidY", "ethyroidN"),
                "Severe chest pain": ("svcpainY", "svcpainN"),
                "Shortness of breath, easily fatigue": ("sobefatigueY", "sobefatigueN"),
                "Breast/axilary masses": ("bamassesY", "bamassesN"),
                "Nipple discharge (blood or pus)": ("ndischargeY", "ndischargeN"),
                "Systolic of 140 and above": ("systolicY", "systolicN"),
                "Diastolic of 190 and above": ("diastolicY", "diastolicN"),
                "Family history of CVA (strokes)": ("fhoCVAY", "fhoCVAN"),
                "Mass in the abdomen": ("mitabdomenY", "mitabdomenN"),
                "History of gallbladder disease": ("hogdiseaseY", "hogdiseaseN"),
                "History of liver disease": ("holiverdiseaseY", "holiverdiseaseN"),
                "Previous surgical operation": ("psoperationY", "psoperationN"),
                "Severe varicosities": ("svaricositiesY", "svaricositiesN"),
                "Deformities": ("deformitiesY", "deformitiesN"),
                "Swelling of severe pain in the legs not related to injuries": ("sosvilnrtinjuryY", "sosvilnrtinjuryN"),
                "Skin Yellowish discoloration": ("skinyellowishY", "skinyellowishN"),
                "Smoking": ("smokingY", "smokingN"),
                "Allergies": ("allergiesY", "allergiesN"),
                "Drug intake": ("dintakeY", "dintakeN"),
                "Drug abuse and alcoholism": ("daalcoholismY", "daalcoholismN"),
                "STD, multiple partners":  ("stdmpartnersY", "stdmpartnersN"),
                "Bleeding tendencies, anemia": ("btanemiaY", "btanemiaN"),
                "Diabetes/congenital anomalies": ("dcanomaliesY", "dcanomaliesN"),
                
                "Full Term": "fullterm",
                "Preterm": "preterm",
                "Abortion": "abortion",
                "Living children": "lchildren",
                "Date of last delivery": "doldelivery",
                "Type of Delivery": "todelivery",
                "Past Menstrual Period": "pmperiod",
                #THE LMP, AOG, AND EDC IS IN THE PATIENT TABLE
                
                "Previous Cesarean Section": ("pcsectionY", "pcsectionN"),
                "3 Consecutive Miscarriages": ("threeconmisY", "threeconmisN"),
                "Ectopic Pregnancy/H.mole": ("epreghmoleY", "epreghmoleN"),
                "Postpartum hemorrhage": ("phemorrhageY", "phemorrhageN"),
                "Forceps delivery": ("fdeliveryY", "fdeliveryN"),
                "Pregnancy Induced Hypertension": ("pihypertensionY", "pihypertensionN"),
                "Weight of baby > 4kgs": ("weightbabykgsY", "weightbabykgsN"),
                
                "Weight": "weight",
                "Height": "height",
                "Blood Type": "btype",
                "Pale": ("phyPaleY", "phyPaleN"),
                "Yellowish": ("phyYellowishY", "phyYellowishN"),
                "Enlarged Thyroid": ("phyEThyroidY", "phyEThyroidN"),
                "Enlarged lymph nodes": ("phyElnodesY", "phyElnodesN"),
                "Mass": ("phyMassY", "phyMassN"),
                "Nipple discharge": ("phyNdischargeY", "phyNdischargeN"),
                "Skin-orange-peel or dimpling": ("phySordimplingY", "phySordimplingN"),
                "Enlarged axillary lymph nodes": ("phyEalnodesY", "phyEalnodesN"),
                "Abnormal heart sounds/cardiac rate": ("phyAhscardiacY", "phyAhscardiacN"),
                "Abnormal health sounds/respiratory rate": ("phyAhsrespiratoryY", "phyAhsrespiratoryN"),
                "Fundic height in cms.": "fhincms",
                "Fetal heart tone": "fhtone",
                "Fetal movement": "fmovement",
                "Fetal part in the fundus": "fpitfundus",
                "Position of Fetal Back": "pofback",
                "Presenting Part": "ppart",
                "Status of Presenting Part": "soppart",
                "Uterine Activity": "uactivity",
                
                "Scars": ("scarsY", "scarsN"),
                "Warts/mass": ("wartsmY", "wartsmN"),
                "Laceration": ("lacerationY", "lacerationN"),
                "Pelvic Severe Varicosities": ("psvaricositiesY", "psvaricositiesN"),
                "Bartholins cyst": ("bcystY", "bcystN"),
                "Warts/Skenes gland discharge": ("wsgdischargeY", "wsgdischargeN"),
                "Cystocele/rectocele": ("crY", "crN"),
                "Purulent discharge/bleeding": ("pdbleedingY", "pdbleedingN"),
                "Erosion/polyp/foreign body": ("erosionpfbodyY", "erosionpfbodyN"),
                "Cervix Consistency": "cervconsistency",
                "Cervix Dilatation": "cervdilatation",
                "Palpable Presenting Part": "palpppart",
                "Status of Bag of Water": "sobowater",
                
                "BEPDelivery Attendant Name": "AttendantName",
                "BEPDelivery Facility Name or Address": "DeliveryNameAdd",
                "BEPDelivery Facility: PhilHealth accredited": ("phAccreditedFY", "phAccreditedFN"),
                "BEPDelivery Facility Maternal Package Cost": "MPCost",
                "BEPDelivery Facility Transportation": "DFTransport",
                "BEPContact Name/Number": "ContactName",
                "BEPCompanion Name": "CompanionName",
                "BEPChildren Attendant Name": "ChildrenAttendantName",
                "BEPDonor Name 1": "DonorName1",
                "BEPDonor Name 2": "DonorName2",
                "BEPReferred Facility": "ReferredF",
                "Name": "PNEname",
                "Contact No.": "PNEcontact",
                "Address": "PNEaddress",
            }
        
            for label, field_name in label_to_field.items():                  
                cursor.execute("""
                    SELECT FR.FORM_RES_VAL
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FO.FORM_OPT_LABEL = %s AND FR.PAT_ID = %s
                """, (label, self.patient_id))
                result = cursor.fetchone()
                value = result[0] if result else ""

                if isinstance(field_name, tuple):
                    yes_field, no_field = field_name
                    if value == "Yes":
                        data[yes_field] = "Yes"  
                        data[no_field] = "No"    
                    elif value == "No":
                        data[yes_field] = "No"   
                        data[no_field] = "Yes"   
                    else:
                        data[yes_field] = ""   
                        data[no_field] = ""
                else:
                    data[field_name] = value.upper() if value else ""

            return data

        except Exception as e:
            print("Error fetching patient data for Maternal Record Form:", e)
            return {}

    def view_filled_pdf(self):
        data = self.fetch_patient_data()
        if data:
            input_pdf = "form_templates/MaternalServiceRecordview.pdf"
            output_pdf = f"temp/MaternalServiceRecord_{self.patient_id}.pdf"
            self.fill_pdf_form(input_pdf, output_pdf, data)
            webbrowser.open(f'file:///{os.path.abspath(output_pdf)}')
        else:
            print("No data found for the patient.")

    def fill_pdf_form(self, input_path, output_path, data_dict):
        if self.patient_id:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM PATIENT WHERE PAT_ID = %s AND PAT_ISDELETED = FALSE", (self.patient_id,))
            exists = cursor.fetchone()[0] > 0
            cursor.close()
            
            if not exists:
                raise ValueError("Patient does not exist or has been deleted")
        
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        if "/AcroForm" in reader.trailer["/Root"]:
            writer._root_object.update({
                NameObject("/AcroForm"): reader.trailer["/Root"]["/AcroForm"]
            })
            writer._root_object["/AcroForm"].update({
                NameObject("/NeedAppearances"): BooleanObject(True)
            })
        else:
            writer._root_object.update({
                NameObject("/AcroForm"): NameObject("/NeedAppearances")({
                    NameObject("/NeedAppearances"): BooleanObject(True)
                })
            })

        def safe_update_field(obj, field_name, value):
            if value is None:
                return

            if isinstance(value, str) and value in ["Yes", "No"]:
                checkbox_val = "/Yes" if value == "Yes" else "/Off"
                obj.update({
                    NameObject("/V"): NameObject(checkbox_val),
                    NameObject("/AS"): NameObject(checkbox_val),
                    NameObject("/Ff"): NumberObject(1)
                })

            else:
                try:
                    obj.update({
                        NameObject("/V"): TextStringObject(str(value)),
                        NameObject("/Ff"): NumberObject(1)
                    })
                except Exception as e:
                    print(f"Error setting field {field_name}: {e}")

        updated = False

        for i, page in enumerate(writer.pages):
            annots = page.get("/Annots")
            if annots:
                for annot in annots:
                    obj = annot.get_object()
                    if "/T" in obj:
                        field_name = obj["/T"]
                        if field_name in data_dict:
                            value = data_dict[field_name]
                            safe_update_field(obj, field_name, value)
                            updated = True
            else:
                print(f"Page {i + 1} has no annotations.")

        if not updated:
            print("No fields found to update in the PDF.")

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"PDF saved to: {output_path}")

    def debug_pdf_fields(self, pdf_path):
        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            annots = page.get("/Annots")
            if annots:
                print(f"Page {i + 1} Annotations:")
                for annot in annots:
                    obj = annot.get_object()
                    if "/T" in obj:
                        print(f"  Field: {obj['/T']}")
            else:
                print(f"Page {i + 1}: No annotations")