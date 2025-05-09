from PyQt5.QtWidgets import (
    QPushButton, QStackedWidget, QLineEdit,
    QCheckBox, QComboBox, QDateEdit, QTimeEdit,
    QTextEdit, QSpinBox, QDoubleSpinBox,
    QMessageBox
)
from PyQt5 import uic
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QIcon
from datetime import date

from PyQt5 import uic

from Database import connect_db
from Admin_Controllers.Admin_Patient_View.AutofillPersonalInfo import AutofillPersonalInfoController
from Admin_Controllers.Admin_Patient_View.AutofillMF import AutofillMatFamController

class FamPlanController:
    def __init__(self, pageFPF, patient_id):
        self.conn = connect_db()
        self.pageFPF = pageFPF
        self.patient_id = patient_id
        self.autofill = AutofillPersonalInfoController(self.conn)
        self.autofillFP = AutofillMatFamController(self.conn)
        
        self.stackWidFPF = self.pageFPF.findChild(QStackedWidget, "stackWidFPF")
        
        self.save_btn = self.pageFPF.findChild(QPushButton, "btnSaveFP")
        self.edit_btn = self.pageFPF.findChild(QPushButton, "btnEditFP")
        self.cancel_btn = self.pageFPF.findChild(QPushButton, "btnCancelFP")
        self.autofill_btn = self.pageFPF.findChild(QPushButton, "btnLoadFromMaternal")
        
        if not self.has_family_planning_service():
            self.edit_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            QMessageBox.information(self.pageFPF, "Information Forms", "This patient did not avail Family Planning service. Form is view-only.")

        self.prev_btn = self.pageFPF.findChild(QPushButton, "pushBtnPrevFPF")
        self.next_btn = self.pageFPF.findChild(QPushButton, "pushBtnNextFPF")
        
        self.autofill_btn.clicked.connect(self.on_autofill_clicked)
        
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.edit_btn.clicked.connect(self.enable_editing_mode)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        
        self.set_all_fields_read_only()

        self.prev_btn.clicked.connect(self.go_prev)
        self.next_btn.clicked.connect(self.go_next)

        self.stackWidFPF.setCurrentIndex(0)  
        self.famplan_page0()
        self.famplan_page1()
        self.update_nav_buttons()
    
    def has_family_planning_service(self):
        query = """
            SELECT 1 FROM PATIENT_SERVICE ps
            JOIN SERVICE s ON ps.SERV_ID = s.SERV_ID
            WHERE ps.PAT_ID = %s AND s.SERV_NAME = 'Family Planning'
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (self.patient_id,))
        result = cursor.fetchone()
        cursor.close()
        return bool(result)
    
    def go_prev(self):
        current_index = self.stackWidFPF.currentIndex()
        if current_index > 0:
            self.stackWidFPF.setCurrentIndex(current_index - 1)
        self.update_nav_buttons()

    def go_next(self):
        current_index = self.stackWidFPF.currentIndex()
        if current_index < self.stackWidFPF.count() - 1:
            self.stackWidFPF.setCurrentIndex(current_index + 1)
        self.update_nav_buttons()

    def update_nav_buttons(self):
        current_index = self.stackWidFPF.currentIndex()
        self.prev_btn.setEnabled(current_index > 0)
        self.next_btn.setEnabled(current_index < self.stackWidFPF.count() - 1)
        
    # View-only Family Planning Dialog
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

        disable_widgets(self.pageFPF)
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

        enable_widgets(self.pageFPF)
        self.cancel_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

        # Keep prefilled fields disabled
        self.clt_phNo.setReadOnly(True)
        self.clt_lname.setReadOnly(True)
        self.clt_fname.setReadOnly(True)
        self.clt_minit.setReadOnly(True)
        self.clt_dob.setEnabled(False)
        self.clt_age.setReadOnly(True)
        self.clt_occupation.setReadOnly(True)
        self.clt_contact.setReadOnly(True)
        self.clt_NSAdd.setReadOnly(True)
        self.clt_BarAdd.setReadOnly(True)
        self.clt_MuniAdd.setReadOnly(True)
        self.clt_ProvAdd.setReadOnly(True)   
        
        self.spo_lname.setReadOnly(True)
        self.spo_fname.setReadOnly(True)
        self.spo_minit.setReadOnly(True)
        self.spo_dob.setEnabled(False)
        self.spo_age.setReadOnly(True)
        self.spo_occupation.setReadOnly(True) 
        
    def saveall_famplanPage(self):
        try:
            self.save_pinfo()
            self.save_fpmetUsed()
            self.save_medH()
            QMessageBox.information(self.pageFPF, "Success", "Maternal record saved successfully.")
            print("Saved successfully.")
        except Exception as e:
            print("Error while saving", e)
        
    def on_autofill_clicked(self):
        reply = QMessageBox.question(
            self.pageFPF,
            "Autofill Form",
            "Are you sure you want to autofill some fields from Maternal Service Record?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.autofill_matTOfam()
            QMessageBox.information(self.pageFPF, "Success Autofill", "Some family planning data has been autofilled from maternal form.")
            self.set_all_fields_read_only()
            
    def autofill_matTOfam(self):
        try:
            self.load_personalinfo_widgets()
            self.load_medH_widgets()
            self.enable_editing_mode()
            
            if not all([
                #Addons personal info
                self.clt_no, self.clt_educA, self.clt_noLivKids, 
                self.clt_pMoreKidY, self.clt_pMoreKidN,
                
                #Medical History
                # self.medH_svhaY, self.medH_svhaN,
                
            ]):
                print("Some client input fields are not initialized. Please check objectNames in the UI.")
                return

            info = self.autofillFP.matTOfam(self.patient_id)
            if info:
                self.clt_no.setText(info["clientno"])
                self.clt_educA.setCurrentText(info["educAtt"])
                self.clt_noLivKids.setText(info["nooflivkids"])
                
                plan_moreKids = info.get("planmorekids", "").lower()
                if plan_moreKids == "yes":
                    self.clt_pMoreKidY.setChecked(True)
                elif plan_moreKids == "no":
                    self.clt_pMoreKidN.setChecked(True)
                
                #Medical History
                svHeadache = info.get("svheadache", "").lower()
                if svHeadache == "yes":
                    self.medH_svhaY.setChecked(True)
                elif svHeadache == "no":
                    self.medH_svhaN.setChecked(True)
                hoStroke = info.get("CVAhistory", "").lower()
                if hoStroke == "yes":
                    self.medH_hoshhaY.setChecked(True)
                elif hoStroke == "no":
                    self.medH_hoshhaN.setChecked(True)
                svcPain = info.get("svchestpain", "").lower()
                if svcPain == "yes":
                    self.medH_chpainY.setChecked(True)
                elif svcPain == "no":
                    self.medH_chpainN.setChecked(True)
                jaundice = info.get("yellow/jaundice", "").lower()
                if jaundice == "yes":
                    self.medH_jaundiceY.setChecked(True)
                elif jaundice == "no":
                    self.medH_jaundiceN.setChecked(True)
                smoker = info.get("smoking", "").lower()
                if smoker == "yes":
                    self.medH_smokerY.setChecked(True)
                elif smoker == "no":
                    self.medH_smokerN.setChecked(True)
                
            else:
                print("No data returned for autofill.")
    
        except Exception as e:
            print("Error in autofill:", e)
            self.conn.rollback()
        
    def famplan_page0(self):
        self.load_personalinfo_widgets()
        self.load_fpmetUsed_widgets()
        self.load_fpmetUsed()
        self.load_pinfo()
        self.prefilled_pinfo()
    
    def prefilled_pinfo(self):
        try:
            self.load_personalinfo_widgets()
            
            if not all([
                self.clt_phNo, self.clt_lname, self.clt_fname, self.clt_minit,
                self.clt_dob, self.clt_age, self.clt_contact, self.clt_occupation,
                self.clt_NSAdd, self.clt_BarAdd, self.clt_MuniAdd, self.clt_ProvAdd,
            ]):
                print("Some client input fields are not initialized. Please check objectNames in the UI.")
                return

            info = self.autofill.get_basic_info(self.patient_id)
            if info:
                self.clt_phNo.setText(info["philno"])
                self.clt_lname.setText(info["lname"])
                self.clt_fname.setText(info["fname"])
                self.clt_minit.setText(info["minit"])
                self.clt_dob.setDate(info["dob"])
                self.clt_age.setText(info["age"])
                self.clt_contact.setText(info["contact"])
                self.clt_occupation.setText(info["occupation"])
                self.clt_NSAdd.setText(info["add_ns"])
                self.clt_BarAdd.setText(info["add_b"])
                self.clt_MuniAdd.setText(info["add_mc"])
                self.clt_ProvAdd.setText(info["add_p"])

            if not all([
                self.spo_lname, self.spo_fname, self.spo_minit,
                self.spo_dob, self.spo_age, self.spo_occupation
            ]):
                print("Some spouse input fields are not initialized. Please check objectNames in the UI.")
                return

            spouse_info = self.autofill.spouse_basic_info(self.patient_id)
            if spouse_info:
                self.spo_lname.setText(spouse_info["spo_lname"])
                self.spo_fname.setText(spouse_info["spo_fname"])
                self.spo_minit.setText(spouse_info["spo_minit"])
                self.spo_dob.setDate(spouse_info["spo_dob"])
                self.spo_age.setText(spouse_info["spo_age"])
                self.spo_occupation.setText(spouse_info["spo_occupation"])

        except Exception as e:
            self.conn.rollback()
            print("Error in FP prefilled_pinfo:", e)
        
    def load_personalinfo_widgets(self):
        self.clt_phNo = self.pageFPF.findChild(QLineEdit, "FPphilHealthNo")
        self.clt_lname = self.pageFPF.findChild(QLineEdit, "clientFPLname")
        self.clt_fname = self.pageFPF.findChild(QLineEdit, "clientFPFname")
        self.clt_minit = self.pageFPF.findChild(QLineEdit, "clientFPMidI")
        self.clt_dob = self.pageFPF.findChild(QDateEdit, "clientFPDOB")
        self.clt_age = self.pageFPF.findChild(QLineEdit, "clientFPAge")
        self.clt_occupation = self.pageFPF.findChild(QLineEdit, "clientFPOccu")
        self.clt_contact = self.pageFPF.findChild(QLineEdit, "clientFPCont")
        self.clt_NSAdd = self.pageFPF.findChild(QLineEdit, "clientFP_NSAdd")
        self.clt_BarAdd = self.pageFPF.findChild(QLineEdit, "clientFP_BarAdd")
        self.clt_MuniAdd = self.pageFPF.findChild(QLineEdit, "clientFP_MuniAdd")
        self.clt_ProvAdd = self.pageFPF.findChild(QLineEdit, "clientFP_ProvAdd")
        
        self.spo_lname = self.pageFPF.findChild(QLineEdit, "spouseFPLname")
        self.spo_fname = self.pageFPF.findChild(QLineEdit, "spouseFPFname")
        self.spo_minit = self.pageFPF.findChild(QLineEdit, "spouseFPMidI")
        self.spo_dob = self.pageFPF.findChild(QDateEdit, "spouseFPDOB")
        self.spo_age = self.pageFPF.findChild(QLineEdit, "spouseFPAge")
        self.spo_occupation = self.pageFPF.findChild(QLineEdit, "spouseFPOccu")
        
        self.clt_no = self.pageFPF.findChild(QLineEdit, "clientID")
        self.clt_educA = self.pageFPF.findChild(QComboBox, "clientFPEduAtt")
        self.clt_noLivKids = self.pageFPF.findChild(QLineEdit, "noLivingKids")
        self.clt_pMoreKidY = self.pageFPF.findChild(QCheckBox, "planMoreKidY")
        self.clt_pMoreKidN = self.pageFPF.findChild(QCheckBox, "planMoreKidN")
        
        self.clt_NHTSy = self.pageFPF.findChild(QCheckBox, "NHTSy")
        self.clt_NHTSn = self.pageFPF.findChild(QCheckBox, "NHTSn")
        self.clt_4PsY = self.pageFPF.findChild(QCheckBox, "fourPsY")
        self.clt_4PsN = self.pageFPF.findChild(QCheckBox, "fourPsN")
        self.clt_civilS = self.pageFPF.findChild(QComboBox, "clientFPCivilStat")
        self.clt_religion = self.pageFPF.findChild(QComboBox, "clientFPReligion")
        self.clt_amonincome = self.pageFPF.findChild(QLineEdit, "FPmonthlyIncome")
            
    def load_pinfo(self):
        try:
            cursor = self.conn.cursor()
            label_to_widget = {
                "FP: Client ID": self.clt_no,
                "FP: NHTS": (self.clt_NHTSy, self.clt_NHTSn),
                "FP: Pantawid 4Ps": (self.clt_4PsY, self.clt_4PsN),
                "FP: Educational Attainment": self.clt_educA,
                "FP: Civil Status": self.clt_civilS,
                "FP: Religion": self.clt_religion,
                "FP: No. of Living Children": self.clt_noLivKids,
                "FP: Plan to have more children": (self.clt_pMoreKidY, self.clt_pMoreKidN),
                "FP: Average monthly income": self.clt_amonincome
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
                    elif isinstance(widget, tuple):  # radio button pairs
                        yes_widget, no_widget = widget
                        yes_widget.setChecked(value == "Yes")
                        no_widget.setChecked(value == "No")
                            
        except Exception as e:
            print("Error loading FP personal info:", e)
    
    def save_pinfo(self):
        try:
            cursor = self.conn.cursor()
            
            # Create a mapping of widget values to FORM_OPT_LABEL (you must make sure labels match)
            responses = {
                    "FP: Client ID": self.clt_no.text(),
                    "FP: NHTS": "Yes" if self.clt_NHTSy.isChecked() else "No",
                    "FP: Pantawid 4Ps": "Yes" if self.clt_4PsY.isChecked() else "No",
                    "FP: Educational Attainment": self.clt_educA.currentText(),
                    "FP: Civil Status": self.clt_civilS.currentText(),
                    "FP: Religion": self.clt_religion.currentText(),
                    "FP: No. of Living Children": self.clt_noLivKids.text(),
                    "FP: Plan to have more children": "Yes" if self.clt_pMoreKidY.isChecked() else "No",
                    "FP: Average monthly income": self.clt_amonincome.text()
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
            print("Error saving FP personal and fp used info:", e)
            self.conn.rollback()
    
    def load_fpmetUsed_widgets(self):
        self.FPNA = self.pageFPF.findChild(QCheckBox, "FPNA")
        self.FPNAspacing = self.pageFPF.findChild(QCheckBox, "FPNAspacing")
        self.FPNAlimiting = self.pageFPF.findChild(QCheckBox, "FPNAlimiting")
        self.FPNAothers = self.pageFPF.findChild(QLineEdit, "FPNAothers")
        
        self.FPCU = self.pageFPF.findChild(QCheckBox, "FPCU")
        self.FPCUchmet = self.pageFPF.findChild(QCheckBox, "FPCUchmet")
        self.FPCUchmetMed = self.pageFPF.findChild(QCheckBox, "FPCUchmetMed")
        self.FPCUchmetSideE = self.pageFPF.findChild(QLineEdit, "FPCUchmetSideE")
        self.FPCUchclinic = self.pageFPF.findChild(QCheckBox, "FPCUchclinic")
        self.FPCUdropres = self.pageFPF.findChild(QCheckBox, "FPCUdropres")
        
        self.FPMCUcoc = self.pageFPF.findChild(QCheckBox, "FPMCUcoc")
        self.FPMCUpop = self.pageFPF.findChild(QCheckBox, "FPMCUpop")
        self.FPMCUinj = self.pageFPF.findChild(QCheckBox, "FPMCUinj")
        self.FPMCUimp = self.pageFPF.findChild(QCheckBox, "FPMCUimp")
        self.FPMCUiud = self.pageFPF.findChild(QCheckBox, "FPMCUiud")
        self.FPMCUiudI = self.pageFPF.findChild(QCheckBox, "FPMCUiudI")
        self.FPMCUiudP = self.pageFPF.findChild(QCheckBox, "FPMCUiudP")
        self.FPMCUcon = self.pageFPF.findChild(QCheckBox, "FPMCUcon")
        self.FPMCUbom = self.pageFPF.findChild(QCheckBox, "FPMCUbom")
        self.FPMCUbbt = self.pageFPF.findChild(QCheckBox, "FPMCUbbt")
        self.FPMCUstm = self.pageFPF.findChild(QCheckBox, "FPMCUstm")
        self.FPMCUsdm = self.pageFPF.findChild(QCheckBox, "FPMCUsdm")
        self.FPMCUlam = self.pageFPF.findChild(QCheckBox, "FPMCUlam")
        self.FPMCUothers = self.pageFPF.findChild(QLineEdit, "FPMCUothers")
    
    def load_fpmetUsed(self):
        try:
            cursor = self.conn.cursor()

            # Load FP Methods Used (multiple checkboxes)
            multi_fp_methods = {
                "FP: New Acceptor": self.FPNA,
                "FP: N - Spacing": self.FPNAspacing,
                "FP: N - Limiting": self.FPNAlimiting,
                "FP: N - Others": self.FPNAothers,
                "FP: Current User": self.FPCU,
                "FP: C - Changing Methods": self.FPCUchmet,
                "FP: C - CM - Med Condition": self.FPCUchmetMed,
                "FP: C - CM - Side Effects": self.FPCUchmetSideE,
                "FP: Changing Clinic": self.FPCUchclinic,
                "FP: Dropout/Restart": self.FPCUdropres,
                
                "FP: MetUsed - COC": self.FPMCUcoc,
                "FP: MetUsed - POP": self.FPMCUpop,
                "FP: MetUsed - Injectible": self.FPMCUinj,
                "FP: MetUsed - Implant": self.FPMCUimp,
                "FP: MetUsed - IUD": self.FPMCUiud,
                "FP: MetUsed - IUD Interval": self.FPMCUiudI,
                "FP: MetUsed - IUD Postpartum": self.FPMCUiudP,
                "FP: MetUsed - Condom": self.FPMCUcon,
                "FP: MetUsed - BOM/CMM": self.FPMCUbom,
                "FP: MetUsed - BBT": self.FPMCUbbt,
                "FP: MetUsed - STM": self.FPMCUstm,
                "FP: MetUsed - SDM": self.FPMCUsdm,
                "FP: MetUsed - LAM": self.FPMCUlam,
                "FP: MetUsed - Others": self.FPMCUothers
            }

            for label, widget in multi_fp_methods.items():
                cursor.execute("""
                    SELECT FR.FORM_RES_VAL
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FO.FORM_OPT_LABEL = %s AND FR.PAT_ID = %s
                """, (label, self.patient_id))
                result = cursor.fetchone()
                if result:
                    value = result[0]
                    if hasattr(widget, 'setChecked'):  # It's a QCheckBox
                        widget.setChecked(value == "Yes")
                    elif hasattr(widget, 'setText'):  # It's a QLineEdit
                        widget.setText(value)

        except Exception as e:
            print("Error loading FP methods used:", e)
    
    def save_fpmetUsed(self):
        try:
            cursor = self.conn.cursor()

            multi_fp_methods = {
                "FP: New Acceptor": self.FPNA,
                "FP: N - Spacing": self.FPNAspacing,
                "FP: N - Limiting": self.FPNAlimiting,
                "FP: N - Others": self.FPNAothers,
                "FP: Current User": self.FPCU,
                "FP: C - Changing Methods": self.FPCUchmet,
                "FP: C - CM - Med Condition": self.FPCUchmetMed,
                "FP: C - CM - Side Effects": self.FPCUchmetSideE,
                "FP: Changing Clinic": self.FPCUchclinic,
                "FP: Dropout/Restart": self.FPCUdropres,
                
                "FP: MetUsed - COC": self.FPMCUcoc,
                "FP: MetUsed - POP": self.FPMCUpop,
                "FP: MetUsed - Injectible": self.FPMCUinj,
                "FP: MetUsed - Implant": self.FPMCUimp,
                "FP: MetUsed - IUD": self.FPMCUiud,
                "FP: MetUsed - IUD Interval": self.FPMCUiudI,
                "FP: MetUsed - IUD Postpartum": self.FPMCUiudP,
                "FP: MetUsed - Condom": self.FPMCUcon,
                "FP: MetUsed - BOM/CMM": self.FPMCUbom,
                "FP: MetUsed - BBT": self.FPMCUbbt,
                "FP: MetUsed - STM": self.FPMCUstm,
                "FP: MetUsed - SDM": self.FPMCUsdm,
                "FP: MetUsed - LAM": self.FPMCUlam,
                "FP: MetUsed - Others": self.FPMCUothers
            }

            for label, widget in multi_fp_methods.items():
                if isinstance(widget, QCheckBox):
                    value = "Yes" if widget.isChecked() else "No"
                elif isinstance(widget, QLineEdit):
                    value = widget.text().strip()
                else:
                    continue
                
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
                        """, (value, form_opt_id, self.patient_id))
                    else:
                        cursor.execute("""
                            INSERT INTO FORM_RESPONSE (FORM_RES_VAL, FORM_OPT_ID, PAT_ID)
                            VALUES (%s, %s, %s)
                        """, (value, form_opt_id, self.patient_id))
                else:
                    print(f"[Warning] FORM_OPTION not found for checkbox: {label}")

            self.conn.commit()

        except Exception as e:
            print("Error saving FP methods used:", e)
            
    def famplan_page1(self):
        self.load_medH_widgets()
        # self.load_fpmetUsed_widgets()
        self.load_medH()
        # self.load_fpmetUsed()
    
    def load_medH_widgets(self):
        self.medH_svhaY = self.pageFPF.findChild(QCheckBox, "FPMed_svhmY")
        self.medH_svhaN = self.pageFPF.findChild(QCheckBox, "FPMed_svhmN")
        self.medH_hoshhaY = self.pageFPF.findChild(QCheckBox, "FPhoshhaY")
        self.medH_hoshhaN = self.pageFPF.findChild(QCheckBox, "FPhoshhaN")
        self.medH_chpainY = self.pageFPF.findChild(QCheckBox, "FPchpainY")
        self.medH_chpainN = self.pageFPF.findChild(QCheckBox, "FPchpainN")
        self.medH_jaundiceY = self.pageFPF.findChild(QCheckBox, "FPjaundiceY")
        self.medH_jaundiceN = self.pageFPF.findChild(QCheckBox, "FPjaundiceN")
        self.medH_smokerY = self.pageFPF.findChild(QCheckBox, "FPsmokerY")
        self.medH_smokerN = self.pageFPF.findChild(QCheckBox, "FPsmokerN")
        
        self.medH_nthY = self.pageFPF.findChild(QCheckBox, "FPnthY")
        self.medH_nthN = self.pageFPF.findChild(QCheckBox, "FPnthN")
        self.medH_hisbcY = self.pageFPF.findChild(QCheckBox, "FPhisbcY")
        self.medH_hisbcN = self.pageFPF.findChild(QCheckBox, "FPhisbcN")
        self.medH_coughY = self.pageFPF.findChild(QCheckBox, "FPcoughY")
        self.medH_coughN = self.pageFPF.findChild(QCheckBox, "FPcoughN")
        self.medH_uvbY = self.pageFPF.findChild(QCheckBox, "FPuvbY")
        self.medH_uvbN = self.pageFPF.findChild(QCheckBox, "FPuvbN")
        self.medH_avdY = self.pageFPF.findChild(QCheckBox, "FPavdY")
        self.medH_avdN = self.pageFPF.findChild(QCheckBox, "FPavdN")
        self.medH_intakeY = self.pageFPF.findChild(QCheckBox, "FPintakeY")
        self.medH_intakeN = self.pageFPF.findChild(QCheckBox, "FPintakeN")
        self.medH_wdisability = self.pageFPF.findChild(QLineEdit, "FPwdisability")
    
    def load_medH(self):
        try:
            cursor = self.conn.cursor()
            label_to_widget = {
                "FP: severe headaches/migraine": (self.medH_svhaY, self.medH_svhaN),
                "FP: history of stroke/hypertension/heart attack": (self.medH_hoshhaY, self.medH_hoshhaN),
                "FP: non-traumatic hematoma/frequent bruising/ gum bleeding": (self.medH_nthY, self.medH_nthN),
                "FP: current or history of breast cancer/breast mass": (self.medH_hisbcY, self.medH_hisbcN),
                "FP: severe chest pain": (self.medH_chpainY, self.medH_chpainN),
                "FP: cough for more than 14 days": (self.medH_coughY, self.medH_coughN),
                "FP: jaundice": (self.medH_jaundiceY, self.medH_jaundiceN),
                "FP: unexplained vaginal bleeding": (self.medH_uvbY, self.medH_uvbN),
                "FP: abnormal vaginal discharge": (self.medH_avdY, self.medH_avdN),
                "FP: intake of (anti-seizure) or (anti-TB)": (self.medH_intakeY, self.medH_intakeN),
                "FP: Is the client a SMOKER?": (self.medH_smokerY, self.medH_smokerN),
                "FP: with disability?": self.medH_wdisability
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
                    elif isinstance(widget, QLineEdit):
                        widget.setText(value)
                            
        except Exception as e:
            print("Error loading FP medical history:", e)
    
    def save_medH(self):
        try:
            cursor = self.conn.cursor()
            
            # Create a mapping of widget values to FORM_OPT_LABEL (you must make sure labels match)
            responses = {
                "FP: severe headaches/migraine": "Yes" if self.medH_svhaY.isChecked() else "No",
                "FP: history of stroke/hypertension/heart attack": "Yes" if self.medH_hoshhaY.isChecked() else "No",
                "FP: non-traumatic hematoma/frequent bruising/ gum bleeding": "Yes" if self.medH_nthY.isChecked() else "No",
                "FP: current or history of breast cancer/breast mass": "Yes" if self.medH_hisbcY.isChecked() else "No",
                "FP: severe chest pain": "Yes" if self.medH_chpainY.isChecked() else "No",
                "FP: cough for more than 14 days": "Yes" if self.medH_coughY.isChecked() else "No",
                "FP: jaundice": "Yes" if self.medH_jaundiceY.isChecked() else "No",
                "FP: unexplained vaginal bleeding": "Yes" if self.medH_uvbY.isChecked() else "No",
                "FP: abnormal vaginal discharge": "Yes" if self.medH_avdY.isChecked() else "No",
                "FP: intake of (anti-seizure) or (anti-TB)": "Yes" if self.medH_intakeY.isChecked() else "No",
                "FP: Is the client a SMOKER?": "Yes" if self.medH_smokerY.isChecked() else "No",
                "FP: with disability?": self.medH_wdisability.text()
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
            print("Error saving FP medical history:", e)
            self.conn.rollback()
            
    def on_save_clicked(self):
        reply = QMessageBox.question(
            self.pageFPF,
            "Confirm Save",
            "Are you sure you want to save the changes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.saveall_famplanPage()
            self.set_all_fields_read_only()

    def on_cancel_clicked(self):
        reply = QMessageBox.question(
            self.pageFPF,
            "Confirm Cancel",
            "Are you sure you want to cancel? Unsaved changes will be lost.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.cancel_editing()
            
    def reset_fields(self):
        #FamPlan: Personal Info Category
        self.clt_no.clear()
        self.clt_educA.setCurrentIndex(-1)
        self.clt_noLivKids.clear()
        
        for pi_chk in [
            self.clt_pMoreKidY, self.clt_pMoreKidN,
            self.clt_NHTSy, self.clt_NHTSn,
            self.clt_4PsY, self.clt_4PsN
        ]:
            pi_chk.setChecked(False)
        
        self.clt_civilS.setCurrentIndex(-1)
        self.clt_religion.setCurrentIndex(-1)
        self.clt_amonincome.clear()
        
        #FamPlan: Type of Client
        for toc_chk in [
            self.FPNA, self.FPNAspacing, self.FPNAlimiting,
            self.FPCU, self.FPCUchmet, self.FPCUchmetMed, self.FPCUchclinic, self.FPCUdropres,
            
            self.FPMCUcoc, self.FPMCUpop, self.FPMCUinj, self.FPMCUimp, self.FPMCUiud, self.FPMCUiudI, self.FPMCUiudP,
            self.FPMCUcon, self.FPMCUbom, self.FPMCUbbt, self.FPMCUstm, self.FPMCUsdm, self.FPMCUlam
        ]:
            toc_chk.setChecked(False)
        
        self.FPNAothers.clear()
        self.FPCUchmetSideE.clear()
        self.FPMCUothers.clear()
        
        #FamPlan: Medical History
        for medH_chk in [
            self.medH_svhaY, self.medH_hoshhaY, self.medH_chpainY, self.medH_jaundiceY, self.medH_smokerY,
            self.medH_svhaN, self.medH_hoshhaN, self.medH_chpainN, self.medH_jaundiceN, self.medH_smokerN,
            
            self.medH_nthY, self.medH_hisbcY, self.medH_coughY, self.medH_uvbY, self.medH_avdY, self.medH_intakeY,
            self.medH_nthN, self.medH_hisbcN, self.medH_coughN, self.medH_uvbN, self.medH_avdN, self.medH_intakeN
        ]:
            medH_chk.setChecked(False)
        
        self.medH_wdisability.clear()
    
    def cancel_editing(self):
        self.reset_fields()
        self.set_all_fields_read_only()
        self.prefilled_pinfo()
        self.load_pinfo()  
        self.load_fpmetUsed()
        self.load_medH()