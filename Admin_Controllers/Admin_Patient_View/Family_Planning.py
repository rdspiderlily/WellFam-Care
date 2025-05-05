from PyQt5.QtWidgets import (
    QPushButton, QStackedWidget, QLineEdit,
    QCheckBox, QComboBox, QDateEdit, QTimeEdit
)
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from datetime import date

from PyQt5 import uic

from Database import connect_db
from Admin_Controllers.Admin_Patient_View.AutofillPersonalInfo import AutofillPersonalInfoController

class FamPlanController:
    def __init__(self, pageFPF, patient_id):
        self.conn = connect_db()
        self.pageFPF = pageFPF
        self.patient_id = patient_id
        self.autofill = AutofillPersonalInfoController(self.conn)
        
        self.stackWidFPF = self.pageFPF.findChild(QStackedWidget, "stackWidFPF")
        
        self.prev_btn = self.pageFPF.findChild(QPushButton, "pushBtnPrevFPF")
        self.next_btn = self.pageFPF.findChild(QPushButton, "pushBtnNextFPF")

        self.prev_btn.clicked.connect(self.go_prev)
        self.next_btn.clicked.connect(self.go_next)

        self.stackWidFPF.setCurrentIndex(0)  
        self.famplan_page0()
        self.update_nav_buttons()
    
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
        
    def famplan_page0(self):
        self.load_personalinfo_widgets()
        self.prefilled_pinfo()
        
    def load_personalinfo_widgets(self):
        self.clt_phNo = self.pageFPF.findChild(QLineEdit, "philHealthNo")
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
        self.clt_NHTSy = self.pageFPF.findChild(QLineEdit, "NHTSy")
        self.clt_NHTSn = self.pageFPF.findChild(QLineEdit, "NHTSn")
        self.clt_4PsY = self.pageFPF.findChild(QLineEdit, "fourPsY")
        self.clt_4PsN = self.pageFPF.findChild(QLineEdit, "fourPsN")
        self.clt_civilS = self.pageFPF.findChild(QComboBox, "clientFPCivilStat")
        self.clt_religion = self.pageFPF.findChild(QComboBox, "clientFPReligion")
        
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
            print("Error in prefilled_basic_pinfo:", e)




        