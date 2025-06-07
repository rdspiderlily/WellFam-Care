from PyQt5.QtWidgets import (
    QPushButton, QStackedWidget, QLineEdit,
    QCheckBox, QComboBox, QDateEdit, QTimeEdit,
    QTextEdit, QSpinBox, QDoubleSpinBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog
)
from PyQt5 import uic
from PyQt5.QtCore import QDate, QTime
from PyQt5.QtGui import QIcon
from datetime import date, datetime
import os
import webbrowser
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, TextStringObject, NumberObject, BooleanObject

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
        self.viewPDF_btn = self.pageFPF.findChild(QPushButton, "viewFamPlanPDF")
        
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
        self.viewPDF_btn.clicked.connect(self.show_pdfPrint)
        
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
                self.obsH_dold, self.obsH_toldV, self.obsH_toldC, self.obsH_pmp,
                
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
                self.obsH_dold.setDate(QDate.fromString(info["dateOLdelivery"], "MM-dd-yyyy"))
                type_delivery = info.get("typeOLdelivery", "").strip()
                self.obsH_toldV.setChecked(type_delivery == "Vaginal")
                self.obsH_toldC.setChecked(type_delivery == "Cesarean section")

                self.obsH_pmp.setDate(QDate.fromString(info["pmp"], "MM-dd-yyyy"))
                
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
            
            safe_set_date = lambda widget, date: widget.setDate(date) if date else None

            info = self.autofill.get_basic_info(self.patient_id)
            if info:
                self.clt_phNo.setText(info["philno"])
                self.clt_lname.setText(info["lname"])
                self.clt_fname.setText(info["fname"])
                self.clt_minit.setText(info["minit"])
                safe_set_date(self.clt_dob, info.get("dob"))
                age = int(info["age"])
                self.clt_age.setText(str(age))
                self.clt_contact.setText(info["contact"])
                self.clt_occupation.setText(info["occupation"])
                self.clt_NSAdd.setText(info["add_ns"])
                self.clt_BarAdd.setText(info["add_b"])
                self.clt_MuniAdd.setText(info["add_mc"])
                self.clt_ProvAdd.setText(info["add_p"])
                
                safe_set_date(self.obsH_lmp, info.get("lmp")) 
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
                safe_set_date(self.ackN_methodDate, info.get("date_availed"))


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
                safe_set_date(self.spo_dob, spouse_info.get("spo_dob"))
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
                    if isinstance(widget, QCheckBox):  
                        widget.setChecked(value == "Yes")
                    elif isinstance(widget, QLineEdit): 
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
        self.obsH_toldV = self.pageFPF.findChild(QCheckBox, "FPtoldV")
        self.obsH_toldC = self.pageFPF.findChild(QCheckBox, "FPtoldC")
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

            obs_fields = {
                "FP: No. of Pregnancies (G)": self.obsH_nopG,
                "FP: No. of Deliveries (P)": self.obsH_nopP,
                "FP: Full Term": self.obsH_ft,
                "FP: Premature": self.obsH_premature,
                "FP: Abortion": self.obsH_abort,
                "FP: Living Children": self.obsH_livkids,
                "FP: Date of Last Delivery": self.obsH_dold,
                "FP: Type of Last Delivery - Vagina": self.obsH_toldV,
                "FP: Type of Last Delivery - CSection": self.obsH_toldC,
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
                    if isinstance(widget, QLineEdit): 
                        widget.setText(value)
                    elif isinstance(widget, QSpinBox):
                        widget.setValue(int(value))
                    elif isinstance(widget, QDateEdit):
                        widget.setDate(QDate.fromString(value, "MM-dd-yyyy"))
                    elif isinstance(widget, QComboBox):
                        index = widget.findText(value)
                        if index != -1:
                            widget.setCurrentIndex(index)
                    elif isinstance(widget, QCheckBox):  
                        widget.setChecked(value == "Yes")

        except Exception as e:
            print("Error loading FP obstretrical history:", e)
    
    def save_obsH(self):
        try:
            cursor = self.conn.cursor()
            
            responses = {
                "FP: No. of Pregnancies (G)": self.obsH_nopG.text(),
                "FP: No. of Deliveries (P)": self.obsH_nopP.text(),
                "FP: Full Term": str(self.obsH_ft.value()),
                "FP: Premature": str(self.obsH_premature.value()),
                "FP: Abortion": str(self.obsH_abort.value()),
                "FP: Living Children": str(self.obsH_livkids.value()),
                "FP: Date of Last Delivery": self.obsH_dold.date().toString("MM-dd-yyyy"),
                "FP: Type of Last Delivery - Vagina": "Yes" if self.obsH_toldV.isChecked() else "No",
                "FP: Type of Last Delivery - CSection": "Yes" if self.obsH_toldC.isChecked() else "No",
                "FP: Last Menstrual Period (LMP)": self.obsH_lmp.date().toString("MM-dd-yyyy"),
                "FP: Previous Menstrual Period (PMP)": self.obsH_pmp.date().toString("MM-dd-yyyy"),
                "FP: Scanty": "Yes" if self.obsH_scanty.isChecked() else "No",
                "FP: Moderate": "Yes" if self.obsH_moderate.isChecked() else "No",
                "FP: Heavy": "Yes" if self.obsH_heavy.isChecked() else "No",
                "FP: Dysmenorrhea": "Yes" if self.obsH_dysmen.isChecked() else "No",
                "FP: H. Mole": "Yes" if self.obsH_hmole.isChecked() else "No",
                "FP: Ectopic Pregnancy": "Yes" if self.obsH_ectopicp.isChecked() else "No",
            }

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
                    elif isinstance(widget, QLineEdit):
                        widget.setText(value)

        except Exception as e:
            print("Error loading FP risks for VAW:", e)
            
    def save_rfVAW(self):
        try:
            cursor = self.conn.cursor()
            
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
            print("Error saving FP pelvic examination:", e)
            self.conn.rollback()
            
    def famplan_page3(self):
        self.load_ackN_widgets()
        
    def load_ackN_widgets(self):
        self.ackN_method = self.pageFPF.findChild(QLineEdit, "FPaMethod")
        self.ackN_methodDate = self.pageFPF.findChild(QDateEdit, "FPaMethodDate")
        self.ackN_client = self.pageFPF.findChild(QLineEdit, "FPaClient")
            
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
                    
                    FAD.FAD_MEDFIND AS MEDICAL_FINDINGS,
                     
                    ST.SERV_TYPE_NAME AS APPOINTMENT_TYPE,  
                    CONCAT(U.STAFF_LNAME, ', ', U.STAFF_FNAME) AS ATTENDANT,
                    
                    FAD.FAD_FLWUPDATE AS FOLLOWUP_DATE

                FROM APPOINTMENT A
                JOIN PATIENT P ON A.PAT_ID = P.PAT_ID
                JOIN APPOINTMENT_SERVICE APS ON A.APP_ID = APS.APP_ID
                JOIN PATIENT_SERVICE PS ON APS.PS_ID = PS.PS_ID
                JOIN SERVICE S ON PS.SERV_ID = S.SERV_ID
                JOIN APPOINTMENT_SERVICE_TYPE AST ON APS.APS_ID = AST.APS_ID
                JOIN PATIENT_SERVICE_TYPE PST ON AST.PST_ID = PST.PST_ID
                JOIN SERVICE_TYPE ST ON PST.SERV_TYPE_ID = ST.SERV_TYPE_ID
                JOIN USER_STAFF U ON A.STAFF_ID = U.STAFF_ID
                LEFT JOIN FAMPLAN_APP_DETAILS FAD ON A.APP_ID = FAD.APP_ID
                WHERE P.PAT_ID = %s AND S.SERV_ID = 2
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
            # Get appointment basic info
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

            # Get appointment-specific follow-up and findings
            cursor.execute("""
                SELECT 
                    FAD_FLWUPDATE,
                    FAD_MEDFIND
                FROM FAMPLAN_APP_DETAILS
                WHERE APP_ID = %s
            """, (app_id,))
            app_details = cursor.fetchone()
            
            if app_data:
                methodUsed.setText(app_data[0])
                # Convert database date to QDate
                if isinstance(app_data[1], date):  # Python date object
                    qdate = QDate(app_data[1].year, app_data[1].month, app_data[1].day)
                    dateVisited.setDate(qdate)
                else:  # Handle string or other formats
                    dateVisited.setDate(QDate.fromString(str(app_data[1]), "yyyy-MM-dd"))
                staffName.setText(app_data[2])
        
            if app_details:
                if app_details[0]:  # Follow-up date
                    if isinstance(app_details[0], date):  # Python date object
                        qdate = QDate(app_details[0].year, app_details[0].month, app_details[0].day)
                        dateFvisit.setDate(qdate)
                    else:  # Handle string or other formats
                        dateFvisit.setDate(QDate.fromString(str(app_details[0]), "yyyy-MM-dd"))
                if app_details[1]:  # Medical findings
                    medFindings.setText(app_details[1])

        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Database error: {e}")
            return

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
            if app_details:
                if app_details[0]:
                    dateFvisit.setDate(QDate.fromString(app_details[0], "yyyy-MM-dd"))
                if app_details[1]:
                    medFindings.setPlainText(app_details[1])
            toggle_edit_mode(False)
            save_btn.setEnabled(False)
            cancel_btn.setEnabled(False)

        def save_changes():
            try:
                cursor = self.conn.cursor()
                follow_up_date = dateFvisit.date().toString("yyyy-MM-dd")
                findings = medFindings.toPlainText()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM FAMPLAN_APP_DETAILS 
                    WHERE APP_ID = %s
                """, (app_id,))
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    # Update existing record
                    cursor.execute("""
                            UPDATE FAMPLAN_APP_DETAILS
                            SET FAD_FLWUPDATE = %s,
                                FAD_MEDFIND = %s
                            WHERE APP_ID = %s
                        """, (follow_up_date, findings, app_id))
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO FAMPLAN_APP_DETAILS 
                        (FAD_FLWUPDATE, FAD_MEDFIND, APP_ID)
                        VALUES (%s, %s, %s)
                    """, (follow_up_date, findings, app_id))
                    
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
            
            responses = {
                "FP: Baby less than 6 months ago": "Yes" if self.cnp_b6Y.isChecked() else "No",
                "FP: Abstained intercourse since lmp": "Yes" if self.cnp_asiY.isChecked() else "No",
                "FP: Baby in the last 4 weeks": "Yes" if self.cnp_b4wY.isChecked() else "No",
                "FP: LMP within the past 7 days": "Yes" if self.cnp_mensY.isChecked() else "No",
                "FP: Miscarriage or abortion in last 7 days": "Yes" if self.cnp_miscY.isChecked() else "No",
                "FP: Using reliable contraceptive consistently": "Yes" if self.cnp_rConY.isChecked() else "No",
            }

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
        self.obsH_lmp.setDate(date.today())
        self.obsH_pmp.setDate(date.today())
        
        for obs_chk in [
            self.obsH_scanty, self.obsH_moderate, self.obsH_heavy, 
            self.obsH_dysmen, self.obsH_hmole, self.obsH_ectopicp,
            self.obsH_toldV, self.obsH_toldC
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
        self.load_cltNpreg()
    
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
                    PAT_LNAME || ',' as LAST_NAME, PAT_FNAME, LEFT(PAT_MNAME, 1) || '.' AS MIDDLE_INITIAL,
                    TO_CHAR(PAT_DOB, 'MM') AS patDm, TO_CHAR(PAT_DOB, 'DD') AS patDd, TO_CHAR(PAT_DOB, 'YYYY') AS patDy,
                    PAT_AGE, PAT_OCCU,
                    CONCAT (PAT_ADDNS, ', ', PAT_ADDB, ', ', PAT_ADDMC, ', ', PAT_ADDP) AS PATIENT_ADD,
                    PAT_CNUM, PAT_PHNUM,
                    CASE
                        WHEN CAST(PAT_AGE AS INTEGER) <= 18 THEN
                            PAT_FNAME || ' ' || LEFT(PAT_MNAME, 1) || '.' || ' ' || PAT_LNAME
                        ELSE NULL
                    END AS minor_name
                FROM PATIENT
                WHERE PAT_ID = %s
            """, (self.patient_id,))
            patient_data = cursor.fetchone()

            if patient_data:
                data["patLname"] = (patient_data[0] or "").upper()
                data["patFname"] = (patient_data[1] or "").upper()
                data["patMname"] = (patient_data[2] or "").upper()
                data["patDOBm"] = patient_data[3]
                data["patDOBd"] = patient_data[4]
                data["patDOBy"] = patient_data[5]
                data["patAge"] = patient_data[6]
                data["patOccu"] = (patient_data[7] or "").upper()
                data["patAddress"] = (patient_data[8] or "").upper()
                data["patContact"] = patient_data[9]
                data["patPhilNum"] = patient_data[10]
                data["ackClient"] = (patient_data[11] or "").upper()
            else:
                print("No data found for the patient for Family Planning.")
            
            cursor.execute("""
                SELECT
                    SP_LNAME || ',' as LAST_NAME, SP_FNAME, LEFT(SP_MNAME, 1) || '.' AS MIDDLE_INITIAL,
                    TO_CHAR(SP_DOB, 'MM') AS spoDm, TO_CHAR(SP_DOB, 'DD') AS spoDd, TO_CHAR(SP_DOB, 'YYYY') AS spoDy,
                    SP_AGE, SP_OCCU
                FROM SPOUSE
                WHERE PAT_ID = %s
            """, (self.patient_id,))
            patient_data = cursor.fetchone()

            if patient_data:
                data["spoLname"] = (patient_data[0] or "").upper()
                data["spoFname"] = (patient_data[1] or "").upper()
                data["spoMname"] = (patient_data[2] or "").upper()
                data["spoDOBm"] = patient_data[3]
                data["spoDOBd"] = patient_data[4]
                data["spoDOBy"] = patient_data[5]
                data["spoAge"] = patient_data[6]
                data["spoOccu"] = (patient_data[7] or "").upper()
            else:
                print("No data found for the patient's spouse for Family Planning.")
            
            cursor.execute("""
                SELECT
                    CONCAT(
                        COALESCE(
                            (SELECT FR.FORM_RES_VAL FROM FORM_RESPONSE FR
                            JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                            WHERE FO.FORM_OPT_LABEL = 'FP: Blood Pressure (S)' AND FR.PAT_ID = P.PAT_ID
                            ), ''
                        ),
                        '/',
                        COALESCE(
                            (SELECT FR.FORM_RES_VAL FROM FORM_RESPONSE FR
                            JOIN FORM_OPTION FO ON FR.FORM_OPT_ID = FO.FORM_OPT_ID
                            WHERE FO.FORM_OPT_LABEL = 'FP: Blood Pressure (D)' AND FR.PAT_ID = P.PAT_ID
                            ), ''
                        )
                    ) AS CONCATENATED_FORM_RESPONSES
                FROM PATIENT P
                WHERE P.PAT_ID = %s
            """, (self.patient_id,))
            patient_data = cursor.fetchone()

            if patient_data:
                data["phyBP"] = patient_data[0] or ""
            else:
                print("No data found for the patient for famplan.")
                
            cursor.execute("""
                SELECT
                    SERVICE_TYPE.SERV_TYPE_NAME,
                    PATIENT_SERVICE.PS_DATEAVAILED
                FROM PATIENT_SERVICE
                JOIN PATIENT_SERVICE_TYPE ON PATIENT_SERVICE.PS_ID = PATIENT_SERVICE_TYPE.PS_ID
                JOIN SERVICE_TYPE ON PATIENT_SERVICE_TYPE.SERV_TYPE_ID = SERVICE_TYPE.SERV_TYPE_ID
                JOIN SERVICE ON PATIENT_SERVICE.SERV_ID = SERVICE.SERV_ID
                WHERE PATIENT_SERVICE.PAT_ID = %s
                AND SERVICE.SERV_NAME = 'Family Planning'
                AND PATIENT_SERVICE.PS_DATEAVAILED = (
                    SELECT MAX(PS2.PS_DATEAVAILED)
                    FROM PATIENT_SERVICE PS2
                    WHERE PS2.PAT_ID = %s
                        AND PS2.SERV_ID = SERVICE.SERV_ID
                )
            """, (self.patient_id, self.patient_id))

            patient_data = cursor.fetchall()

            if patient_data:
                methods = [row[0] for row in patient_data]
                latest_date = patient_data[0][1]

                data["ackMethod"] = ", ".join(methods)
                data["ackMdate"] = latest_date
            else:
                print("No data found for the patient availed methods for Family Planning.")
                
            cursor.execute("""
                SELECT 
                    A.APP_ID, 
                    A.APP_DATE,
                    
                    FAD.FAD_MEDFIND AS MEDICAL_FINDINGS,
                     
                    ST.SERV_TYPE_NAME AS APPOINTMENT_TYPE,  
                    CONCAT(U.STAFF_LNAME, ', ', U.STAFF_FNAME) AS ATTENDANT,
                    
                    FAD.FAD_FLWUPDATE AS FOLLOWUP_DATE

                FROM APPOINTMENT A
                JOIN PATIENT P ON A.PAT_ID = P.PAT_ID
                JOIN APPOINTMENT_SERVICE APS ON A.APP_ID = APS.APP_ID
                JOIN PATIENT_SERVICE PS ON APS.PS_ID = PS.PS_ID
                JOIN SERVICE S ON PS.SERV_ID = S.SERV_ID
                JOIN APPOINTMENT_SERVICE_TYPE AST ON APS.APS_ID = AST.APS_ID
                JOIN PATIENT_SERVICE_TYPE PST ON AST.PST_ID = PST.PST_ID
                JOIN SERVICE_TYPE ST ON PST.SERV_TYPE_ID = ST.SERV_TYPE_ID
                JOIN USER_STAFF U ON A.STAFF_ID = U.STAFF_ID
                LEFT JOIN FAMPLAN_APP_DETAILS FAD ON A.APP_ID = FAD.APP_ID
                WHERE P.PAT_ID = %s
                ORDER BY A.APP_DATE ASC
            """, (self.patient_id,))

            patient_data = cursor.fetchall()
            
            if patient_data:
                app_dates = [str(row[1]) for row in patient_data]
                medical_findings = [row[2] or '' for row in patient_data]
                appointment_types = [row[3] or '' for row in patient_data]
                attendants = [row[4] or '' for row in patient_data]
                followup_dates = [str(row[5]) or '' for row in patient_data]

                data["appDates"] = "\n\n\n".join(app_dates)
                data["medicalFindings"] = "\n\n\n".join(medical_findings)
                data["appointmentTypes"] = "\n\n\n".join(appointment_types)
                data["attendants"] = "\n\n\n".join(attendants)
                data["followUpDates"] = "\n\n\n".join(followup_dates)
                
            else:
                print("No data found for appointment history for Family Planning.")
                
            label_to_field = {
                "FP: Client ID": "patClientID",
                "FP: NHTS": ("nhtsY", "nhtsN"),
                "FP: Pantawid 4Ps": ("4psY", "4psN"),
                "FP: Educational Attainment": "patEducA",
                "FP: Civil Status": "patCstatus",
                "FP: Religion": "patReligion",
                "FP: No. of Living Children": "noLKids",
                "FP: Plan to have more children": ("planKidY", "planKidN"),
                "FP: Average monthly income": "AVGmonIncome",
                
                "FP: New Acceptor": "nAcceptor",
                "FP: N - Spacing": "spacing",
                "FP: N - Limiting": "limiting",
                "FP: N - Others": "cOthers",
                "FP: Current User": "cUser",
                "FP: C - Changing Methods": "cMethod",
                "FP: C - CM - Med Condition": "mCondition",
                "FP: C - CM - Side Effects": "sEffects",
                "FP: Changing Clinic": "cClinic",
                "FP: Dropout/Restart": "dRestart",
                
                "FP: MetUsed - COC": "mCOC",
                "FP: MetUsed - POP": "mPOP",
                "FP: MetUsed - Injectible": "mInjectible",
                "FP: MetUsed - Implant": "mImplant",
                "FP: MetUsed - IUD": "mIUD",
                "FP: MetUsed - IUD Interval": "mInterval",
                "FP: MetUsed - IUD Postpartum": "mPostpartum",
                "FP: MetUsed - Condom": "mCondom",
                "FP: MetUsed - BOM/CMM": "mBOM",
                "FP: MetUsed - BBT": "mBBT",
                "FP: MetUsed - STM": "mSTM",
                "FP: MetUsed - SDM": "mSDM",
                "FP: MetUsed - LAM": "mLAM",
                "FP: MetUsed - Others": "mOthers",
                
                "FP: severe headaches/migraine": ("medSHMy", "medSHMn"),
                "FP: history of stroke/hypertension/heart attack": ("medHOSHAHy", "medHOSHAHn"),
                "FP: non-traumatic hematoma/frequent bruising/ gum bleeding": ("medNTHFBGBy", "medNTHFBGBn"),
                "FP: current or history of breast cancer/breast mass": ("medCHBCBMy", "medCHBCBMn"),
                "FP: severe chest pain": ("medSCPy", "medSCPn"),
                "FP: cough for more than 14 days": ("medC14Dy", "medC14Dn"),
                "FP: jaundice": ("medJy", "medJn"),
                "FP: unexplained vaginal bleeding": ("medUVBy", "medUVBn"),
                "FP: abnormal vaginal discharge": ("medAVDy", "medAVDn"),
                "FP: intake of (anti-seizure) or (anti-TB)": ("medIPRy", "medIPRn"),
                "FP: Is the client a SMOKER?": ("medSMKRy", "medSMKRn"),
                "FP: with disability?": "medWDisability",
                
                "FP: No. of Pregnancies (G)": "obsG",
                "FP: No. of Deliveries (P)": "obsP",
                "FP: Full Term": "obsFT",
                "FP: Premature": "obsPREM",
                "FP: Abortion": "obsABORTION",
                "FP: Living Children": "obsLC",
                "FP: Date of Last Delivery": ("obsDOLDm", "obsDOLDd", "obsDOLDy"),
                "FP: Type of Last Delivery - Vagina": "obsV",
                "FP: Type of Last Delivery - CSection": "obsCS",
                "FP: Last Menstrual Period (LMP)": ("obsLMPm", "obsLMPd", "obsLMPy"),
                "FP: Previous Menstrual Period (PMP)": ("obsPMPm", "obsPMPd", "obsPMPy"),
                "FP: Scanty": "obsSCANTY",
                "FP: Moderate": "obsMOD",
                "FP: Heavy": "obsHEAVY",
                "FP: Dysmenorrhea": "obsDYS",
                "FP: H. Mole": "obsHMOLE",
                "FP: Ectopic Pregnancy": "obsEPREG",
                
                "FP: abnormal discharge from the genital area": ("stiADGAy", "stiADGAn"),
                "FP: abnormal discharge from the genital area (V)": "stiVAGINA",
                "FP: abnormal discharge from the genital area (P)": "stiPENIS",
                "FP: sores or ulcers in genital area": ("stiSUGAy", "stiSUGAn"),
                "FP: pain or burning sensation in the genital area": ("stiPBSGAy", "stiPBSGAn"),
                "FP: history of treatment for STI": ("stiHTSTIy", "stiHTSTIn"),
                "FP: HIV/ AIDS/ PI Disease": ("stiHIVy", "stiHIVn"),
                
                "FP: unpleasant relationship with the partner": ("vawURPy", "vawURPn"),
                "FP: partner do not approve to visit FP Clinic": ("vawPDFPy", "vawPDFPn"),
                "FP: history of VAW": ("vawHDVy", "vawHDVn"),
                "FP: DSWD": "vawDSWD",
                "FP: WCPU": "vawWCPU",
                "FP: NGOs": "vawNGO",
                "FP: VAW Others": "vawOTHERS",
                
                "FP: Weight": "phyWeight",
                "FP: Height": "phyHeight",
                "FP: Pulse Rate": "phyPulseRate",
                "FP: S - Normal": "phySKINnorm",
                "FP: S - Pale": "phySKINpale",
                "FP: S - Yellowish": "phySKINyell",
                "FP: S - Hematoma": "phySKINhema",
                "FP: C - Normal": "phyCONJnorm",
                "FP: C - Pale": "phyCONJpale",
                "FP: C - Yellowish": "phyCONJyello",
                "FP: N - Normal": "phyNECKnorm",
                "FP: N - Neck mass": "phyNECKmass",
                "FP: N - Enlarged lymph nodes": "phyNECKlnodes",
                "FP: B - Normal": "phyBREASTnorm",
                "FP: B - Mass": "phyBREASTmass",
                "FP: B - Nipple discharge": "phyBREASTnipdis",
                "FP: A - Normal": "phyABDnorm",
                "FP: A - Abdominal Mass": "phyABDmass",
                "FP: A - Varicosities": "phyABDvaric",
                "FP: E - Normal": "phyEXTnorm",
                "FP: E - Edema": "phyEXTedema",
                "FP: E - Varicosities": "phyEXTvaric",
                
                "FP: Normal Pelvic": "pelvNormal",
                "FP: Mass Pelvic": "pelvMass",
                "FP: Abdominal Discharge Pelvic": "pelvAdischarge",
                "FP: Cervical Tenderness Pelvic": "pelvCtender",
                "FP: Adnexal Mass/ Tender Pelvic": "pelvAmass",
                
                "FP: Cervical Abnormalities": "pelvCabnormal",
                "FP: CA - warts": "pelvWarts",
                "FP: CA - cyst": "pelvPcyst",
                "FP: CA - inflammation": "pelvIerosion",
                "FP: CA - bloody discharge": "pelvBdisharge",
                
                "FP: Cervical Consistency": "pelvCconsistency",
                "FP: CC - firm": "pelvFirm",
                "FP: CC - soft": "pelvSoft",
                
                "FP: Uterine position": "pelvUposition",
                "FP: UP - mid": "pelvMid",
                "FP: UP - anteflexed": "pelvAnte",
                "FP: UP - retroflexed": "pelvRetro",
                
                "FP: Uterine depth": "pelvUdepth",
                "FP: Uterine depth: depth": "pelvUdepthCM",
                
                "FP: Baby less than 6 months ago": ("b6Y", "b6N"),
                "FP: Abstained intercourse since lmp": ("almpY", "almpN"),
                "FP: Baby in the last 4 weeks": ("b4Y", "b4N"),
                "FP: LMP within the past 7 days": ("lmp7Y", "lmp7N"),
                "FP: Miscarriage or abortion in last 7 days": ("mis7Y", "mis7N"),
                "FP: Using reliable contraceptive consistently": ("contraY", "contraN"),
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

                if isinstance(field_name, tuple) and len(field_name) == 3:
                    month_field, day_field, year_field = field_name
                    try:
                        parsed_date = None
                        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
                            try:
                                parsed_date = datetime.strptime(value, fmt)
                                break
                            except ValueError:
                                continue

                        if parsed_date:
                            data[month_field] = parsed_date.strftime("%m")
                            data[day_field] = parsed_date.strftime("%d")
                            data[year_field] = parsed_date.strftime("%Y")
                        else:
                            data[month_field] = ""
                            data[day_field] = ""
                            data[year_field] = ""
                    except Exception:
                        data[month_field] = ""
                        data[day_field] = ""
                        data[year_field] = ""
                elif isinstance(field_name, tuple):
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
                    if value == "Yes":
                        data[field_name] = "Yes"
                    elif value == "No":
                        data[field_name] = "No"
                    else:
                        data[field_name] = value.upper() if value else ""

            return data

        except Exception as e:
            print("Error fetching patient data for Family Planning Form:", e)
            return {}

    def view_filled_pdf(self):
        data = self.fetch_patient_data()
        if data:
            input_pdf = "form_templates/FamilyPlanningFormview.pdf"
            output_pdf = f"temp/FamilyPlanning_{self.patient_id}.pdf"
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
            acroform = writer._root_object["/AcroForm"]
            # Set NeedAppearances to True
            acroform.update({
                NameObject("/NeedAppearances"): BooleanObject(True)
            })

            # Set /DA to use Helvetica 12pt black text
            # You can replace "/Helv" with the font name your PDF uses for Unicode
            acroform.update({
                NameObject("/DA"): TextStringObject("/Helv 12 Tf 0 g")
            })
        else:
            # If no AcroForm, create minimal with NeedAppearances True and DA string
            writer._root_object.update({
                NameObject("/AcroForm"): writer._add_object({
                    NameObject("/NeedAppearances"): BooleanObject(True),
                    NameObject("/DA"): TextStringObject("/Helv 12 Tf 0 g")
                })
            })

        READONLY_FLAG = 1
        MULTILINE_FLAG = 4096
        
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
                    # Enable multiline flag for text fields
                    current_ff = obj.get("/Ff", NumberObject(0))
                    new_ff = NumberObject(int(current_ff) | MULTILINE_FLAG | READONLY_FLAG)
                    obj.update({
                        NameObject("/V"): TextStringObject(str(value)),
                        NameObject("/Ff"): new_ff
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