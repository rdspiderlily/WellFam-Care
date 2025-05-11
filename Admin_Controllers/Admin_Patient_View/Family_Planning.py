from PyQt5.QtWidgets import (
    QPushButton, QStackedWidget, QLineEdit,
    QCheckBox, QComboBox, QDateEdit, QTimeEdit,
    QTextEdit, QSpinBox, QDoubleSpinBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QWidget
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
    def __init__(self, pageFPF, patient_id, user_id):
        self.conn = connect_db()
        self.pageFPF = pageFPF
        self.patient_id = patient_id
        self.user_id = user_id
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
        self.famplan_page2()
        self.famplan_page3()
        self.famplan_page4()
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
            self.save_obsH()
            self.save_rfSTI()
            self.save_rfVAW()
            self.save_phyE()
            self.save_pelvicE()
            self.save_ackN()
            self.save_cltNpreg()
            
            form_id = self.get_form_id('Family Planning Form (FP) 1')
            if form_id is None:
                print("Form ID for Family Planning Form is not found.")
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
            
            QMessageBox.information(self.pageFPF, "Success", "Family Planning form saved successfully.")
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
            WHERE PAT_ID = %s AND SERV_ID = 2
        """, (self.patient_id,))  # Ensure the service ID for Family Planning (3)
        ps_id = cursor.fetchone()
        cursor.close()
        if ps_id:
            return ps_id[0]  # Return the PS_ID
        else:
            print(f"No patient service found for PAT_ID {self.patient_id} and SERV_ID 2.")
            return None 
        
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
            self.load_obsH_widgets()
            self.load_phyE_widgets()
            self.enable_editing_mode()
            
            if not all([
                #Addons personal info
                self.clt_no, self.clt_educA, self.clt_noLivKids, 
                self.clt_pMoreKidY, self.clt_pMoreKidN,
                
                #Medical History
                self.medH_svhaY, self.medH_hoshhaY, self.medH_chpainY, self.medH_jaundiceY, self.medH_smokerY,
                self.medH_svhaN, self.medH_hoshhaN, self.medH_chpainN, self.medH_jaundiceN, self.medH_smokerN,
                
                #Obstetrical History
                self.obsH_ft, self.obsH_premature, self.obsH_abort, self.obsH_livkids,
                self.obsH_dold, self.obsH_told, self.obsH_pmp,
                
                #Physical Examination
                self.phyE_weight, self.phyE_height,  self.phyE_bpS, self.phyE_bpD,
                self.phyE_Cpale, self.phyE_Cyellow,
                self.phyE_Neln, self.phyE_Bmass, self.phyE_Bnip
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
                fields = [
                    ("svheadache", self.medH_svhaY, self.medH_svhaN),
                    ("CVAhistory", self.medH_hoshhaY, self.medH_hoshhaN),
                    ("svchestpain", self.medH_chpainY, self.medH_chpainN),
                    ("yellow/jaundice", self.medH_jaundiceY, self.medH_jaundiceN),
                    ("smoking", self.medH_smokerY, self.medH_smokerN),
                ]

                for key, radio_yes, radio_no in fields:
                    value = info.get(key, "").lower()
                    if value == "yes":
                        radio_yes.setChecked(True)
                    elif value == "no":
                        radio_no.setChecked(True)
                
                #Obstetrical History
                self.obsH_ft.setValue(int(info["NOPfullterm"]))
                self.obsH_premature.setValue(int(info["NOPpreterm"]))
                self.obsH_abort.setValue(int(info["NOPabortion"]))
                self.obsH_livkids.setValue(int(info["nooflivkids"]))
                self.obsH_dold.setDate(QDate.fromString(info["dateOLdelivery"], "yyyy-MM-dd"))
                self.obsH_told.setCurrentText(info["typeOLdelivery"])
                self.obsH_pmp.setDate(QDate.fromString(info["pmp"], "yyyy-MM-dd"))
                
                #Physical Examination
                self.phyE_weight.setValue(float(info["PEweight"]))
                self.phyE_height.setValue(float(info["PEheight"]))
                self.phyE_bpS.setValue(int(info["bpS"]))
                self.phyE_bpD.setValue(int(info["bpD"]))
                self.phyE_Cpale.setChecked(info["conjuPale"] in ["Yes", "1", 1, True])
                self.phyE_Cyellow.setChecked(info["conjuYellowish"] in ["Yes", "1", 1, True])
                self.phyE_Neln.setChecked(info["neckEnNodes"] in ["Yes", "1", 1, True])
                self.phyE_Bmass.setChecked(info["breastMass"] in ["Yes", "1", 1, True])
                self.phyE_Bnip.setChecked(info["breastNipD"] in ["Yes", "1", 1, True])
                
            else:
                print("No data returned for autofill.")
    
        except Exception as e:
            print("Error in autofill:", e)
            self.conn.rollback()
        
    def famplan_page0(self):
        self.load_personalinfo_widgets()
        self.load_fpmetUsed_widgets()
        self.load_pinfo()
        self.load_fpmetUsed()
        self.prefilled_pinfo()
    
    def prefilled_pinfo(self):
        try:
            self.load_personalinfo_widgets()
            self.load_obsH_widgets()
            self.load_ackN_widgets()
            
            if not all([
                self.clt_phNo, self.clt_lname, self.clt_fname, self.clt_minit,
                self.clt_dob, self.clt_age, self.clt_contact, self.clt_occupation,
                self.clt_NSAdd, self.clt_BarAdd, self.clt_MuniAdd, self.clt_ProvAdd,
                
                self.obsH_lmp, 
                
                self.ackN_method, self.ackN_methodDate, self.ackN_client
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
                age = int(info["age"])
                self.clt_age.setText(str(age))
                self.clt_contact.setText(info["contact"])
                self.clt_occupation.setText(info["occupation"])
                self.clt_NSAdd.setText(info["add_ns"])
                self.clt_BarAdd.setText(info["add_b"])
                self.clt_MuniAdd.setText(info["add_mc"])
                self.clt_ProvAdd.setText(info["add_p"])
                
                self.obsH_lmp.setDate(info["lmp"])
                
                if age <= 18:
                    self.ackN_client.setText(f"{info['fname']} {info['minit']} {info['lname']}")
                    
                    
            if not all([
                self.ackN_method, self.ackN_methodDate
            ]):
                print("Some client input fields are not initialized. Please check objectNames in the UI.")
                return

            info = self.autofill.famplan_availed(self.patient_id)
            if info:
                subtypes_str = ", ".join(info["subtypes"])
                self.ackN_method.setText(subtypes_str)
                self.ackN_methodDate.setDate(info["date_availed"])


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
            print("Error saving FP personal info:", e)
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
                    if isinstance(widget, QCheckBox):  # It's a QCheckBox
                        widget.setChecked(value == "Yes")
                    elif isinstance(widget, QLineEdit):  # It's a QLineEdit
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
        self.load_obsH_widgets()
        self.load_medH()
        self.load_obsH()
    
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
            
    def load_obsH_widgets(self):
        self.obsH_nopG = self.pageFPF.findChild(QLineEdit, "FPnopG")
        self.obsH_nopP = self.pageFPF.findChild(QLineEdit, "FPnopP")
        self.obsH_ft = self.pageFPF.findChild(QSpinBox, "FPft")
        self.obsH_premature = self.pageFPF.findChild(QSpinBox, "FPpremature")
        self.obsH_abort = self.pageFPF.findChild(QSpinBox, "FPabort")
        self.obsH_livkids = self.pageFPF.findChild(QSpinBox, "FPlivkids")
        
        self.obsH_dold = self.pageFPF.findChild(QDateEdit, "FPdold")
        self.obsH_told = self.pageFPF.findChild(QComboBox, "FPtold")
        self.obsH_lmp = self.pageFPF.findChild(QDateEdit, "FPlmp")
        self.obsH_pmp = self.pageFPF.findChild(QDateEdit, "FPpmp")
        
        self.obsH_scanty = self.pageFPF.findChild(QCheckBox, "FPscanty")
        self.obsH_moderate = self.pageFPF.findChild(QCheckBox, "FPmoderate")
        self.obsH_heavy = self.pageFPF.findChild(QCheckBox, "FPheavy")
        
        self.obsH_dysmen = self.pageFPF.findChild(QCheckBox, "FPdysmen")
        self.obsH_hmole = self.pageFPF.findChild(QCheckBox, "FPhmole")
        self.obsH_ectopicp = self.pageFPF.findChild(QCheckBox, "FPectopicp")
    
    def load_obsH(self):
        try:
            cursor = self.conn.cursor()

            # Map form labels to widgets
            obs_fields = {
                "FP: No. of Pregnancies (G)": self.obsH_nopG,
                "FP: No. of Deliveries (P)": self.obsH_nopP,
                "FP: Full Term": self.obsH_ft,
                "FP: Premature": self.obsH_premature,
                "FP: Abortion": self.obsH_abort,
                "FP: Living Children": self.obsH_livkids,
                "FP: Date of Last Delivery": self.obsH_dold,
                "FP: Type of Last Delivery": self.obsH_told,
                "FP: Last Menstrual Period (LMP)": self.obsH_lmp,
                "FP: Previous Menstrual Period (PMP)": self.obsH_pmp,
                "FP: Scanty": self.obsH_scanty,
                "FP: Moderate": self.obsH_moderate,
                "FP: Heavy": self.obsH_heavy,
                "FP: Dysmenorrhea": self.obsH_dysmen,
                "FP: H. Mole": self.obsH_hmole,
                "FP: Ectopic Pregnancy": self.obsH_ectopicp
            }
            
            for label, widget in obs_fields.items():
                cursor.execute("""
                    SELECT FR.FORM_RES_VAL
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FO.FORM_OPT_LABEL = %s AND FR.PAT_ID = %s
                """, (label, self.patient_id))
                result = cursor.fetchone()
                if result:
                    value = result[0]
                    if isinstance(widget, QLineEdit):  # It's a QLineEdit
                        widget.setText(value)
                    elif isinstance(widget, QSpinBox):
                        widget.setValue(int(value))
                    elif isinstance(widget, QDateEdit):
                        widget.setDate(QDate.fromString(value, "yyyy-MM-dd"))
                    elif isinstance(widget, QComboBox):
                        index = widget.findText(value)
                        if index != -1:
                            widget.setCurrentIndex(index)
                    elif isinstance(widget, QCheckBox):  # It's a QCheckBox
                        widget.setChecked(value == "Yes")

        except Exception as e:
            print("Error loading FP obstretrical history:", e)
    
    def save_obsH(self):
        try:
            cursor = self.conn.cursor()
            
            # Create a mapping of widget values to FORM_OPT_LABEL (you must make sure labels match)
            responses = {
                "FP: No. of Pregnancies (G)": self.obsH_nopG.text(),
                "FP: No. of Deliveries (P)": self.obsH_nopP.text(),
                "FP: Full Term": str(self.obsH_ft.value()),
                "FP: Premature": str(self.obsH_premature.value()),
                "FP: Abortion": str(self.obsH_abort.value()),
                "FP: Living Children": str(self.obsH_livkids.value()),
                "FP: Date of Last Delivery": self.obsH_dold.date().toString("yyyy-MM-dd"),
                "FP: Type of Last Delivery": self.obsH_told.currentText(),
                "FP: Last Menstrual Period (LMP)": self.obsH_lmp.date().toString("yyyy-MM-dd"),
                "FP: Previous Menstrual Period (PMP)": self.obsH_pmp.date().toString("yyyy-MM-dd"),
                "FP: Scanty": "Yes" if self.obsH_scanty.isChecked() else "No",
                "FP: Moderate": "Yes" if self.obsH_moderate.isChecked() else "No",
                "FP: Heavy": "Yes" if self.obsH_heavy.isChecked() else "No",
                "FP: Dysmenorrhea": "Yes" if self.obsH_dysmen.isChecked() else "No",
                "FP: H. Mole": "Yes" if self.obsH_hmole.isChecked() else "No",
                "FP: Ectopic Pregnancy": "Yes" if self.obsH_ectopicp.isChecked() else "No",
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
            print("Error saving FP obstetrical history:", e)
            self.conn.rollback()
    
    def famplan_page2(self):
        self.load_rfSTI_widgets()
        self.load_rfVAW_widget()
        self.load_phyE_widgets()
        self.load_pelvicE_widgets()
        self.load_rfSTI()
        self.load_rfVAW()
        self.load_phyE()
        self.load_pelvicE()
    
    def load_rfSTI_widgets(self):
        self.rfSTI_adgaY = self.pageFPF.findChild(QCheckBox, "FPadgaY")
        self.rfSTI_adgaN = self.pageFPF.findChild(QCheckBox, "FPadgaN")
        self.rfSTI_adgaVag = self.pageFPF.findChild(QCheckBox, "FPadgaVag")
        self.rfSTI_adgaYPen = self.pageFPF.findChild(QCheckBox, "FPadgaPen")
        self.rfSTI_sugaY = self.pageFPF.findChild(QCheckBox, "FPsugaY")
        self.rfSTI_sugaN = self.pageFPF.findChild(QCheckBox, "FPsugaN")
        self.rfSTI_pbgaY = self.pageFPF.findChild(QCheckBox, "FPpbgaY")
        self.rfSTI_pbgaN = self.pageFPF.findChild(QCheckBox, "FPpbgaN")
        self.rfSTI_htstiY = self.pageFPF.findChild(QCheckBox, "FPhtstiY")
        self.rfSTI_htstiN = self.pageFPF.findChild(QCheckBox, "FPhtstiN")
        self.rfSTI_hivetcY = self.pageFPF.findChild(QCheckBox, "FPhivetcY")
        self.rfSTI_hivetcN = self.pageFPF.findChild(QCheckBox, "FPhivetcN")
    
    def load_rfSTI(self):
        try:
            cursor = self.conn.cursor()

            # Map form labels to widgets
            obs_fields = {
                "FP: abnormal discharge from the genital area": (self.rfSTI_adgaY, self.rfSTI_adgaN),
                "FP: abnormal discharge from the genital area (V)": self.rfSTI_adgaVag,
                "FP: abnormal discharge from the genital area (P)": self.rfSTI_adgaYPen,
                "FP: sores or ulcers in genital area": (self.rfSTI_sugaY, self.rfSTI_sugaN),
                "FP: pain or burning sensation in the genital area": (self.rfSTI_pbgaY, self.rfSTI_pbgaN),
                "FP: history of treatment for STI": (self.rfSTI_htstiY, self.rfSTI_htstiN),
                "FP: HIV/ AIDS/ PI Disease": (self.rfSTI_hivetcY, self.rfSTI_hivetcN)
            }       
            
            for label, widget in obs_fields.items():
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
                    elif isinstance(widget, QCheckBox):
                        widget.setChecked(value == "Yes")

        except Exception as e:
            print("Error loading FP risks for STI:", e)
            
    def save_rfSTI(self):
        try:
            cursor = self.conn.cursor()
            
            # Create a mapping of widget values to FORM_OPT_LABEL (you must make sure labels match)
            responses = {
                "FP: abnormal discharge from the genital area": "Yes" if self.rfSTI_adgaY.isChecked() else "No",
                "FP: abnormal discharge from the genital area (V)": "Yes" if self.rfSTI_adgaVag.isChecked() else "No",
                "FP: abnormal discharge from the genital area (P)": "Yes" if self.rfSTI_adgaYPen.isChecked() else "No",
                "FP: sores or ulcers in genital area": "Yes" if self.rfSTI_sugaY.isChecked() else "No",
                "FP: pain or burning sensation in the genital area": "Yes" if self.rfSTI_pbgaY.isChecked() else "No",
                "FP: history of treatment for STI": "Yes" if self.rfSTI_htstiY.isChecked() else "No",
                "FP: HIV/ AIDS/ PI Disease": "Yes" if self.rfSTI_hivetcY.isChecked() else "No",
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
            print("Error saving FP risks for STI:", e)
            self.conn.rollback()
            
    def load_rfVAW_widget(self):
        self.rfVAW_urpY = self.pageFPF.findChild(QCheckBox, "FPurpY")
        self.rfVAW_urpN = self.pageFPF.findChild(QCheckBox, "FPurpN")
        self.rfVAW_pdfpcY = self.pageFPF.findChild(QCheckBox, "FPpdfpcY")
        self.rfVAW_pdfpcN = self.pageFPF.findChild(QCheckBox, "FPpdfpcN")
        self.rfVAW_hdvY = self.pageFPF.findChild(QCheckBox, "FPhdvY")
        self.rfVAW_hdvN = self.pageFPF.findChild(QCheckBox, "FPhdvN")
        self.rfVAW_dswd = self.pageFPF.findChild(QCheckBox, "FPdswd")
        self.rfVAW_wcpu = self.pageFPF.findChild(QCheckBox, "FPwcpu")
        self.rfVAW_ngos = self.pageFPF.findChild(QCheckBox, "FPngos")
        self.rfVAW_others = self.pageFPF.findChild(QLineEdit, "FPvawOthers")
        
    def load_rfVAW(self):
        try:
            cursor = self.conn.cursor()

            # Map form labels to widgets
            obs_fields = {
                "FP: unpleasant relationship with the partner": (self.rfVAW_urpY, self.rfVAW_urpN),
                "FP: partner do not approve to visit FP Clinic": (self.rfVAW_pdfpcY, self.rfVAW_pdfpcN),
                "FP: history of VAW": (self.rfVAW_hdvY, self.rfVAW_hdvN),
                "FP: DSWD": self.rfVAW_dswd,
                "FP: WCPU": self.rfVAW_wcpu,
                "FP: NGOs": self.rfVAW_ngos,
                "FP: VAW Others": self.rfVAW_others,
            }       
            
            for label, widget in obs_fields.items():
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
                    elif isinstance(widget, QCheckBox):
                        widget.setChecked(value == "Yes")
                    elif isinstance(widget, QLineEdit):  # It's a QLineEdit
                        widget.setText(value)

        except Exception as e:
            print("Error loading FP risks for VAW:", e)
            
    def save_rfVAW(self):
        try:
            cursor = self.conn.cursor()
            
            # Create a mapping of widget values to FORM_OPT_LABEL (you must make sure labels match)
            responses = {
                "FP: unpleasant relationship with the partner": "Yes" if self.rfVAW_urpY.isChecked() else "No",
                "FP: partner do not approve to visit FP Clinic": "Yes" if self.rfVAW_pdfpcY.isChecked() else "No",
                "FP: history of VAW": "Yes" if self.rfVAW_hdvY.isChecked() else "No",
                "FP: DSWD": "Yes" if self.rfVAW_dswd.isChecked() else "No",
                "FP: WCPU": "Yes" if self.rfVAW_wcpu.isChecked() else "No",
                "FP: NGOs": "Yes" if self.rfVAW_ngos.isChecked() else "No",
                "FP: VAW Others": self.rfVAW_others.text()
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
            print("Error saving FP risks for VAW:", e)
            self.conn.rollback()
            
    def load_phyE_widgets(self):
        self.phyE_weight = self.pageFPF.findChild(QDoubleSpinBox, "FPweight")
        self.phyE_height = self.pageFPF.findChild(QDoubleSpinBox, "FPheight")
        self.phyE_bpS = self.pageFPF.findChild(QSpinBox, "FPbpS")
        self.phyE_bpD = self.pageFPF.findChild(QSpinBox, "FPbpD")
        self.phyE_pulseRate = self.pageFPF.findChild(QSpinBox, "FPpulse")
        
        self.phyE_Snormal = self.pageFPF.findChild(QCheckBox, "FPSnormal")
        self.phyE_Spale = self.pageFPF.findChild(QCheckBox, "FPSpale")
        self.phyE_Syellowish = self.pageFPF.findChild(QCheckBox, "FPSyellowish")
        self.phyE_Shematoma = self.pageFPF.findChild(QCheckBox, "FPShematoma")
        
        self.phyE_Cnormal = self.pageFPF.findChild(QCheckBox, "FPCnormal")
        self.phyE_Cpale = self.pageFPF.findChild(QCheckBox, "FPCpale")
        self.phyE_Cyellow = self.pageFPF.findChild(QCheckBox, "FPCyellowish")
        
        self.phyE_Nnormal = self.pageFPF.findChild(QCheckBox, "FPNnormal")
        self.phyE_Nneckmass = self.pageFPF.findChild(QCheckBox, "FPNneckmass")
        self.phyE_Neln = self.pageFPF.findChild(QCheckBox, "FPNeln")
        
        self.phyE_Bnormal = self.pageFPF.findChild(QCheckBox, "FPBnormal")
        self.phyE_Bmass = self.pageFPF.findChild(QCheckBox, "FPBmass")
        self.phyE_Bnip = self.pageFPF.findChild(QCheckBox, "FPBnip")
        
        self.phyE_Anormal = self.pageFPF.findChild(QCheckBox, "FPAnormal")
        self.phyE_Amass = self.pageFPF.findChild(QCheckBox, "FPAabmass")
        self.phyE_Avaric = self.pageFPF.findChild(QCheckBox, "FPAvaric")
        
        self.phyE_Enormal = self.pageFPF.findChild(QCheckBox, "FPEnormal")
        self.phyE_Eedema = self.pageFPF.findChild(QCheckBox, "FPEedema")
        self.phyE_Evaric = self.pageFPF.findChild(QCheckBox, "FPEvaric")
    
    def load_phyE(self):
        try:
            cursor = self.conn.cursor()
            field_to_widget = {
                "FP: Weight": self.phyE_weight,
                "FP: Height": self.phyE_height,
                "FP: Blood Pressure (S)": self.phyE_bpS,
                "FP: Blood Pressure (D)": self.phyE_bpD,
                "FP: Pulse Rate": self.phyE_pulseRate,
                
                "FP: S - Normal": self.phyE_Snormal,
                "FP: S - Pale": self.phyE_Snormal,
                "FP: S - Yellowish": self.phyE_Snormal,
                "FP: S - Hematoma": self.phyE_Shematoma,
                
                "FP: C - Normal": self.phyE_Cnormal,
                "FP: C - Pale": self.phyE_Cpale,
                "FP: C - Yellowish": self.phyE_Cyellow,
                
                "FP: N - Normal": self.phyE_Nnormal,
                "FP: N - Neck mass": self.phyE_Nneckmass,
                "FP: N - Enlarged lymph nodes": self.phyE_Neln,
                
                "FP: B - Normal": self.phyE_Bnormal,
                "FP: B - Mass": self.phyE_Bmass,
                "FP: B - Nipple discharge": self.phyE_Bnip,
                
                "FP: A - Normal": self.phyE_Anormal,
                "FP: A - Abdominal Mass": self.phyE_Amass,
                "FP: A - Varicosities": self.phyE_Avaric,
                
                "FP: E - Normal": self.phyE_Enormal,
                "FP: E - Edema": self.phyE_Eedema,
                "FP: E - Varicosities": self.phyE_Evaric
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
                    if isinstance(widget, QDoubleSpinBox):
                        widget.setValue(float(value))
                    elif isinstance(widget, QSpinBox):
                        widget.setValue(int(value))
                    elif isinstance(widget, QCheckBox):
                        widget.setChecked(value == "Yes")
            
        except Exception as e:
            print("Error loading FP physical examination:", e)
            
    def save_phyE(self):
        try:
            cursor = self.conn.cursor()
            
            # Create a mapping of widget values to FORM_OPT_LABEL (you must make sure labels match)
            responses = {
                "FP: Weight": str(self.phyE_weight.value()),
                "FP: Height": str(self.phyE_height.value()),
                "FP: Blood Pressure (S)": str(self.phyE_bpS.value()),
                "FP: Blood Pressure (D)": str(self.phyE_bpD.value()),
                "FP: Pulse Rate": str(self.phyE_pulseRate.value()),
                
                "FP: S - Normal": "Yes" if self.phyE_Snormal.isChecked() else "No",
                "FP: S - Pale": "Yes" if self.phyE_Spale.isChecked() else "No",
                "FP: S - Yellowish": "Yes" if self.phyE_Syellowish.isChecked() else "No",
                "FP: S - Hematoma": "Yes" if self.phyE_Shematoma.isChecked() else "No",
                
                "FP: C - Normal": "Yes" if self.phyE_Cnormal.isChecked() else "No",
                "FP: C - Pale": "Yes" if self.phyE_Cpale.isChecked() else "No",
                "FP: C - Yellowish": "Yes" if self.phyE_Cyellow.isChecked() else "No",
                
                "FP: N - Normal": "Yes" if self.phyE_Nnormal.isChecked() else "No",
                "FP: N - Neck mass": "Yes" if self.phyE_Nneckmass.isChecked() else "No",
                "FP: N - Enlarged lymph nodes": "Yes" if self.phyE_Neln.isChecked() else "No",
                
                "FP: B - Normal": "Yes" if self.phyE_Bnormal.isChecked() else "No",
                "FP: B - Mass": "Yes" if self.phyE_Bmass.isChecked() else "No",
                "FP: B - Nipple discharge": "Yes" if self.phyE_Bnip.isChecked() else "No",
                
                "FP: A - Normal": "Yes" if self.phyE_Anormal.isChecked() else "No",
                "FP: A - Abdominal Mass": "Yes" if self.phyE_Amass.isChecked() else "No",
                "FP: A - Varicosities": "Yes" if self.phyE_Avaric.isChecked() else "No",
                
                "FP: E - Normal": "Yes" if self.phyE_Enormal.isChecked() else "No",
                "FP: E - Edema": "Yes" if self.phyE_Eedema.isChecked() else "No",
                "FP: E - Varicosities": "Yes" if self.phyE_Evaric.isChecked() else "No"
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
            print("Error saving FP physical examination:", e)
            self.conn.rollback()
            
    def load_pelvicE_widgets(self):
        self.pelvicE_normal = self.pageFPF.findChild(QCheckBox, "FPpnormal")
        self.pelvicE_mass = self.pageFPF.findChild(QCheckBox, "FPpmass")
        self.pelvicE_ad = self.pageFPF.findChild(QCheckBox, "FPpad")
        self.pelvicE_pct = self.pageFPF.findChild(QCheckBox, "FPpct")
        self.pelvicE_pamt = self.pageFPF.findChild(QCheckBox, "FPpamt")
        
        self.pelvicE_CA = self.pageFPF.findChild(QCheckBox, "FPpCA")
        self.pelvicE_CAwarts = self.pageFPF.findChild(QCheckBox, "FPpCAwarts")
        self.pelvicE_CAcyst = self.pageFPF.findChild(QCheckBox, "FPpCAcyst")
        self.pelvicE_CAinflam = self.pageFPF.findChild(QCheckBox, "FPpCAinflam")
        self.pelvicE_CAbd = self.pageFPF.findChild(QCheckBox, "FPpCAbd")
        
        self.pelvicE_CC = self.pageFPF.findChild(QCheckBox, "FPpCC")
        self.pelvicE_CCfirm = self.pageFPF.findChild(QCheckBox, "FPpCCfirm")
        self.pelvicE_CCsoft = self.pageFPF.findChild(QCheckBox, "FPpCCsoft")
        
        self.pelvicE_UP = self.pageFPF.findChild(QCheckBox, "FPpUP")
        self.pelvicE_UPmid = self.pageFPF.findChild(QCheckBox, "FPpUPmid")
        self.pelvicE_UPante = self.pageFPF.findChild(QCheckBox, "FPpUPante")
        self.pelvicE_UPretro = self.pageFPF.findChild(QCheckBox, "FPpUPretro")
        
        self.pelvicE_UD = self.pageFPF.findChild(QCheckBox, "FPpUD")
        self.pelvicE_UDdepth = self.pageFPF.findChild(QSpinBox, "FPpUDdepth")
    
    def load_pelvicE(self):
        try:
            cursor = self.conn.cursor()
            field_to_widget = {
                "FP: Normal Pelvic": self.pelvicE_normal,
                "FP: Mass Pelvic": self.pelvicE_mass,
                "FP: Abdominal Discharge Pelvic": self.pelvicE_ad,
                "FP: Cervical Tenderness Pelvic": self.pelvicE_pct,
                "FP: Adnexal Mass/ Tender Pelvic": self.pelvicE_pamt,
                
                "FP: Cervical Abnormalities": self.pelvicE_CA,
                "FP: CA - warts": self.pelvicE_CAwarts,
                "FP: CA - cyst": self.pelvicE_CAcyst,
                "FP: CA - inflammation": self.pelvicE_CAinflam,
                "FP: CA - bloody discharge": self.pelvicE_CAbd,
                
                "FP: Cervical Consistency": self.pelvicE_CC,
                "FP: CC - firm": self.pelvicE_CCfirm,
                "FP: CC - soft": self.pelvicE_CCsoft,
                
                "FP: Uterine position": self.pelvicE_UP,
                "FP: UP - mid": self.pelvicE_UPmid,
                "FP: UP - anteflexed": self.pelvicE_UPante,
                "FP: UP - retroflexed": self.pelvicE_UPretro,
                
                "FP: Uterine depth": self.pelvicE_UD,
                "FP: Uterine depth: depth": self.pelvicE_UDdepth
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
                    if isinstance(widget, QCheckBox):
                        widget.setChecked(value == "Yes")
                    elif isinstance(widget, QSpinBox):
                        widget.setValue(int(value))
            
        except Exception as e:
            print("Error loading FP pelvic examination:", e)
    
    def save_pelvicE(self):
        try:
            cursor = self.conn.cursor()
            
            # Create a mapping of widget values to FORM_OPT_LABEL (you must make sure labels match)
            responses = {
                "FP: Normal Pelvic": "Yes" if self.pelvicE_normal.isChecked() else "No",
                "FP: Mass Pelvic": "Yes" if self.pelvicE_mass.isChecked() else "No",
                "FP: Abdominal Discharge Pelvic": "Yes" if self.pelvicE_ad.isChecked() else "No",
                "FP: Cervical Tenderness Pelvic": "Yes" if self.pelvicE_pct.isChecked() else "No",
                "FP: Adnexal Mass/ Tender Pelvic": "Yes" if self.pelvicE_pamt.isChecked() else "No",
                
                "FP: Cervical Abnormalities": "Yes" if self.pelvicE_CA.isChecked() else "No",
                "FP: CA - warts": "Yes" if self.pelvicE_CAwarts.isChecked() else "No",
                "FP: CA - cyst": "Yes" if self.pelvicE_CAcyst.isChecked() else "No",
                "FP: CA - inflammation": "Yes" if self.pelvicE_CAinflam.isChecked() else "No",
                "FP: CA - bloody discharge": "Yes" if self.pelvicE_CAbd.isChecked() else "No",
                
                "FP: Cervical Consistency": "Yes" if self.pelvicE_CC.isChecked() else "No",
                "FP: CC - firm": "Yes" if self.pelvicE_CCfirm.isChecked() else "No",
                "FP: CC - soft": "Yes" if self.pelvicE_CCsoft.isChecked() else "No",
                
                "FP: Uterine position": "Yes" if self.pelvicE_UP.isChecked() else "No",
                "FP: UP - mid": "Yes" if self.pelvicE_UPmid.isChecked() else "No",
                "FP: UP - anteflexed": "Yes" if self.pelvicE_UPante.isChecked() else "No",
                "FP: UP - retroflexed": "Yes" if self.pelvicE_UPretro.isChecked() else "No",
                
                "FP: Uterine depth": "Yes" if self.pelvicE_UD.isChecked() else "No",
                "FP: Uterine depth: depth": str(self.pelvicE_UDdepth.value())
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
            print("Error saving FP pelvic examination:", e)
            self.conn.rollback()
            
    def famplan_page3(self):
        self.load_ackN_widgets()
        self.load_ackN()
        
    def load_ackN_widgets(self):
        self.ackN_method = self.pageFPF.findChild(QLineEdit, "FPaMethod")
        self.ackN_methodDate = self.pageFPF.findChild(QDateEdit, "FPaMethodDate")
        self.ackN_client = self.pageFPF.findChild(QLineEdit, "FPaClient")
        self.ackN_clientDate = self.pageFPF.findChild(QDateEdit, "FPaDate")
    
    def load_ackN(self):
        try:
            cursor = self.conn.cursor()

            # Map form labels to widgets
            obs_fields = {
                "FP: Client Date": self.ackN_clientDate
            }
            
            for label, widget in obs_fields.items():
                cursor.execute("""
                    SELECT FR.FORM_RES_VAL
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FO.FORM_OPT_LABEL = %s AND FR.PAT_ID = %s
                """, (label, self.patient_id))
                result = cursor.fetchone()
                if result:
                    value = result[0]
                    if isinstance(widget, QLineEdit):  # It's a QLineEdit
                        widget.setText(value)
                    elif isinstance(widget, QDateEdit):
                        widget.setDate(QDate.fromString(value, "yyyy-MM-dd"))

        except Exception as e:
            print("Error loading FP acknowledgement:", e)
    
    def save_ackN(self):
        try:
            cursor = self.conn.cursor()
            
            # Create a mapping of widget values to FORM_OPT_LABEL (you must make sure labels match)
            responses = {
                "FP: Client Date": self.ackN_clientDate.date().toString("yyyy-MM-dd")
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
            print("Error saving FP acknowledgement:", e)
            self.conn.rollback()
            
    def famplan_page4(self):
        self.ARtable = self.pageFPF.findChild(QTableWidget, "tableWidFamPlanAR")
        self.load_cltNpreg_widgets()
        self.load_table()
        self.ARtable.cellClicked.connect(self.view_ARdetails)
        self.load_cltNpreg()
        
    def load_table(self):
        self.ARtable.setRowCount(0)
        
        header = self.ARtable.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        column_sizes = [0, 100, 230, 250, 250, 168]
        for i, size in enumerate(column_sizes):
            header.resizeSection(i, size)

        self.ARtable.setColumnHidden(0, True)
        self.ARtable.verticalHeader().setVisible(False)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    A.APP_ID, 
                    A.APP_DATE,
                    
                    -- Subquery: Medical Findings
                    (SELECT FR.FORM_RES_VAL 
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FR.PAT_ID = P.PAT_ID AND FO.FORM_OPT_LABEL = 'FP: Medical Findings'
                    LIMIT 1) AS MEDICAL_FINDINGS,
                     
                    ST.SERV_TYPE_NAME AS APPOINTMENT_TYPE,  
                    CONCAT(U.STAFF_LNAME, ', ', U.STAFF_FNAME) AS ATTENDANT,
                    
                    -- Subquery: Date of Follow-up Visit
                    (SELECT FR.FORM_RES_VAL 
                    FROM FORM_RESPONSE FR
                    JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                    WHERE FR.PAT_ID = P.PAT_ID AND FO.FORM_OPT_LABEL = 'FP: Date of Follow up Visit'
                    LIMIT 1) AS FOLLOWUP_DATE

                FROM APPOINTMENT A
                JOIN PATIENT P ON A.PAT_ID = P.PAT_ID
                JOIN APPOINTMENT_SERVICE APS ON A.APP_ID = APS.APP_ID
                JOIN PATIENT_SERVICE PS ON APS.PS_ID = PS.PS_ID
                JOIN SERVICE S ON PS.SERV_ID = S.SERV_ID
                JOIN APPOINTMENT_SERVICE_TYPE AST ON APS.APS_ID = AST.APS_ID
                JOIN PATIENT_SERVICE_TYPE PST ON AST.PST_ID = PST.PST_ID
                JOIN SERVICE_TYPE ST ON PST.SERV_TYPE_ID = ST.SERV_TYPE_ID
                JOIN USER_STAFF U ON A.STAFF_ID = U.STAFF_ID
                WHERE P.PAT_ID = %s
                ORDER BY A.APP_DATE ASC
            """, (self.patient_id,))
            
            rows = cursor.fetchall()
            for row in rows:
                row_position = self.ARtable.rowCount()
                self.ARtable.insertRow(row_position)
                for column, data in enumerate(row):
                    self.ARtable.setItem(row_position, column, QTableWidgetItem(str(data)))
        except Exception as e:
            QMessageBox.critical(self.ARtable, "Database Error", f"Error fetching updated data: {e}")

    def view_ARdetails(self, row, column):
        if column != 1:
            return
        
        app_id = self.ARtable.item(row, 0).text()

        dialog = QDialog()
        uic.loadUi("wfui/famplan_ARdetails.ui", dialog)
        dialog.setWindowTitle("View Assessment Record Details")
        dialog.setWindowIcon(QIcon("wfpics/logo1.jpg"))

        methodUsed = dialog.findChild(QLineEdit, "ARdMethodAccepted")
        dateVisited = dialog.findChild(QDateEdit, "ARdDateVisited")
        dateFvisit = dialog.findChild(QDateEdit, "ARdDateFVisit")
        staffName = dialog.findChild(QLineEdit, "ARdStaffName")
        medFindings = dialog.findChild(QTextEdit, "ARdMedFindings")

        edit_btn = dialog.findChild(QPushButton, "ARdEditBtn")
        save_btn = dialog.findChild(QPushButton, "ARdSaveBtn")
        cancel_btn = dialog.findChild(QPushButton, "ARdCancelBtn")

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    ST.SERV_TYPE_NAME,
                    A.APP_DATE,
                    CONCAT(U.STAFF_LNAME, ', ', U.STAFF_FNAME)
                FROM APPOINTMENT A
                JOIN APPOINTMENT_SERVICE APS ON A.APP_ID = APS.APP_ID
                JOIN APPOINTMENT_SERVICE_TYPE AST ON APS.APS_ID = AST.APS_ID
                JOIN PATIENT_SERVICE_TYPE PST ON AST.PST_ID = PST.PST_ID
                JOIN SERVICE_TYPE ST ON PST.SERV_TYPE_ID = ST.SERV_TYPE_ID
                JOIN USER_STAFF U ON A.STAFF_ID = U.STAFF_ID
                WHERE A.APP_ID = %s
            """, (app_id,))
            app_data = cursor.fetchone()

            cursor.execute("""
                SELECT FORM_RES_VAL FROM FORM_RESPONSE FR
                JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                WHERE FR.PAT_ID = %s AND FO.FORM_OPT_LABEL = %s
            """, (self.patient_id, "FP: Date of Follow up Visit"))
            date_fup = cursor.fetchone()

            cursor.execute("""
                SELECT FORM_RES_VAL FROM FORM_RESPONSE FR
                JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                WHERE FR.PAT_ID = %s AND FO.FORM_OPT_LABEL = %s
            """, (self.patient_id, "FP: Medical Findings"))
            med_find = cursor.fetchone()

            if app_data:
                methodUsed.setText(app_data[0])
                dateVisited.setDate(app_data[1])
                staffName.setText(app_data[2])
            if date_fup:
                dateFvisit.setDate(QDate.fromString(date_fup[0], "yyyy-MM-dd"))
            if med_find:
                medFindings.setText(med_find[0])

        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Database error: {e}")
            return

        # Disable fields initially
        for w in [methodUsed, dateVisited, staffName, dateFvisit, medFindings]:
            w.setEnabled(False)
        save_btn.setEnabled(False)
        cancel_btn.setEnabled(False)

        def toggle_edit_mode(enabled):
            dateFvisit.setEnabled(enabled)
            medFindings.setEnabled(enabled)
            save_btn.setEnabled(enabled)
            cancel_btn.setEnabled(enabled)

        def cancel_changes():
            dateFvisit.setEnabled(False)
            medFindings.setEnabled(False)
            save_btn.setEnabled(False)
            cancel_btn.setEnabled(False)

        def save_changes():
            try:
                cursor = self.conn.cursor()
                responses = {
                    "FP: Date of Follow up Visit": dateFvisit.date().toString("yyyy-MM-dd"),
                    "FP: Medical Findings": medFindings.toPlainText()
                }

                for label, value in responses.items():
                    cursor.execute("SELECT FORM_OPT_ID FROM FORM_OPTION WHERE FORM_OPT_LABEL = %s", (label,))
                    opt = cursor.fetchone()
                    if opt:
                        form_opt_id = opt[0]
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
                self.conn.commit()
                QMessageBox.information(dialog, "Success", "Follow-up information updated successfully.")
                self.load_table()
                toggle_edit_mode(False)
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Error", f"Failed to save changes: {e}")

        edit_btn.clicked.connect(lambda: toggle_edit_mode(True))
        cancel_btn.clicked.connect(cancel_changes)
        save_btn.clicked.connect(save_changes)
        dialog.exec_()
        
    def load_cltNpreg_widgets(self):
        self.cnp_b6Y = self.pageFPF.findChild(QCheckBox, "FPcnpB6Y")
        self.cnp_b6N = self.pageFPF.findChild(QCheckBox, "FPcnpB6N")
        self.cnp_asiY = self.pageFPF.findChild(QCheckBox, "FPcnpAsiY")
        self.cnp_asiN = self.pageFPF.findChild(QCheckBox, "FPcnpAsiN")
        self.cnp_b4wY = self.pageFPF.findChild(QCheckBox, "FPcnpB4wY")
        self.cnp_b4wN = self.pageFPF.findChild(QCheckBox, "FPcnpB4wN")
        self.cnp_mensY = self.pageFPF.findChild(QCheckBox, "FPcnpMensY")
        self.cnp_mensN = self.pageFPF.findChild(QCheckBox, "FPcnpMensN")
        self.cnp_miscY = self.pageFPF.findChild(QCheckBox, "FPcnpMiscY")
        self.cnp_miscN = self.pageFPF.findChild(QCheckBox, "FPcnpMiscN")
        self.cnp_rConY = self.pageFPF.findChild(QCheckBox, "FPcnpRconY")
        self.cnp_rConN = self.pageFPF.findChild(QCheckBox, "FPcnpRconN")
    
    def load_cltNpreg(self):
        try:
            cursor = self.conn.cursor()
            field_to_widget = {
                "FP: Baby less than 6 months ago": (self.cnp_b6Y, self.cnp_b6N),
                "FP: Abstained intercourse since lmp": (self.cnp_asiY, self.cnp_asiN),
                "FP: Baby in the last 4 weeks": (self.cnp_b4wY, self.cnp_b4wN),
                "FP: LMP within the past 7 days": (self.cnp_mensY, self.cnp_mensN),
                "FP: Miscarriage or abortion in last 7 days": (self.cnp_miscY, self.cnp_miscN),
                "FP: Using reliable contraceptive consistently": (self.cnp_rConY, self.cnp_rConN)
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
                    if isinstance(widget, tuple):  # radio button pairs
                        yes_widget, no_widget = widget
                        yes_widget.setChecked(value == "Yes")
                        no_widget.setChecked(value == "No")
            
        except Exception as e:
            print("Error loading FP how to determine client is not preg:", e)
    
    def save_cltNpreg(self):
        try:
            cursor = self.conn.cursor()
            
            # Create a mapping of widget values to FORM_OPT_LABEL (you must make sure labels match)
            responses = {
                "FP: Baby less than 6 months ago": "Yes" if self.cnp_b6Y.isChecked() else "No",
                "FP: Abstained intercourse since lmp": "Yes" if self.cnp_asiY.isChecked() else "No",
                "FP: Baby in the last 4 weeks": "Yes" if self.cnp_b4wY.isChecked() else "No",
                "FP: LMP within the past 7 days": "Yes" if self.cnp_mensY.isChecked() else "No",
                "FP: Miscarriage or abortion in last 7 days": "Yes" if self.cnp_miscY.isChecked() else "No",
                "FP: Using reliable contraceptive consistently": "Yes" if self.cnp_rConY.isChecked() else "No",
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
            print("Error saving FP how to determine client is not preg:", e)
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
        
        #FamPlan: Obstetrical History
        self.obsH_nopG.clear()
        self.obsH_nopP.clear()
        self.obsH_ft.setValue(0)
        self.obsH_premature.setValue(0)
        self.obsH_abort.setValue(0)
        self.obsH_livkids.setValue(0)
        
        self.obsH_dold.setDate(date.today())
        self.obsH_told.setCurrentIndex(0)
        self.obsH_lmp.setDate(date.today())
        self.obsH_pmp.setDate(date.today())
        
        for obs_chk in [
            self.obsH_scanty, self.obsH_moderate, self.obsH_heavy, 
            self.obsH_dysmen, self.obsH_hmole, self.obsH_ectopicp
        ]:
            obs_chk.setChecked(False)
            
        #FamPlan: Risks For STI
        for sti_chk in [
            self.rfSTI_adgaY, self.rfSTI_adgaVag, self.rfSTI_sugaY, self.rfSTI_pbgaY, self.rfSTI_htstiY, self.rfSTI_hivetcY,
            self.rfSTI_adgaN, self.rfSTI_adgaYPen, self.rfSTI_sugaN, self.rfSTI_pbgaN, self.rfSTI_htstiN, self.rfSTI_hivetcN
        ]:
            sti_chk.setChecked(False)
        
        #FamPlan: Risks For VAW
        for vaw_chk in [
            self.rfVAW_urpY, self.rfVAW_pdfpcY, self.rfVAW_hdvY, 
            self.rfVAW_urpN, self.rfVAW_pdfpcN, self.rfVAW_hdvN,
            
            self.rfVAW_dswd, self.rfVAW_wcpu, self.rfVAW_ngos,
        ]:
            vaw_chk.setChecked(False)
        
        self.rfVAW_others.clear()
        
        #FamPlan: Physical Examination
        self.phyE_weight.setValue(0)
        self.phyE_height.setValue(0)
        self.phyE_bpS.setValue(0)
        self.phyE_bpD.setValue(0)
        self.phyE_pulseRate.setValue(0)
        
        for phyE_chk in [
            self.phyE_Snormal, self.phyE_Spale, self.phyE_Syellowish, self.phyE_Shematoma,
            self.phyE_Cnormal, self.phyE_Cpale, self.phyE_Cyellow,
            self.phyE_Nnormal, self.phyE_Nneckmass, self.phyE_Neln,
            self.phyE_Bnormal, self.phyE_Bmass, self.phyE_Bnip,
            self.phyE_Anormal, self.phyE_Amass, self.phyE_Avaric,
            self.phyE_Enormal, self.phyE_Eedema, self.phyE_Evaric
        ]:
            phyE_chk.setChecked(False)
        
        #FamPlan: Physical Examination
        for pelvicE_chk in [
            self.pelvicE_normal, self.pelvicE_mass, self.pelvicE_ad, self.pelvicE_pct, self.pelvicE_pamt,
            self.pelvicE_CA, self.pelvicE_CAwarts, self.pelvicE_CAcyst, self.pelvicE_CAinflam, self.pelvicE_CAbd,
            self.pelvicE_CC, self.pelvicE_CCfirm, self.pelvicE_CCsoft,
            self.pelvicE_UP, self.pelvicE_UPmid, self.pelvicE_UPante, self.pelvicE_UPretro,
            self.pelvicE_UD
        ]:
            pelvicE_chk.setChecked(False)
            
        self.pelvicE_UDdepth.setValue(0)
        
        #FamPlan: Acknowledgement
        self.ackN_method.clear()
        self.ackN_methodDate.setDate(date.today())
        self.ackN_clientDate.setDate(date.today())
        
        #FamPlan: How to make sure client is not pregnant
        for cltNpreg_chk in [
            self.cnp_b6Y, self.cnp_asiY, self.cnp_b4wY, self.cnp_mensY, self.cnp_miscY, self.cnp_rConY,
            self.cnp_b6N, self.cnp_asiN, self.cnp_b4wN, self.cnp_mensN, self.cnp_miscN, self.cnp_rConN
        ]:
            cltNpreg_chk.setChecked(False)
    
    def cancel_editing(self):
        self.reset_fields()
        self.set_all_fields_read_only()
        self.prefilled_pinfo()
        self.load_pinfo()  
        self.load_fpmetUsed()
        self.load_medH()
        self.load_obsH()
        self.load_rfSTI()
        self.load_rfVAW()
        self.load_phyE()
        self.load_pelvicE()
        self.load_ackN()
        self.load_cltNpreg()