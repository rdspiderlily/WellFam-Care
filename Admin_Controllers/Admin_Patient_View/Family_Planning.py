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

class FamPlanController:
    def __init__(self, pageFPF, patient_id):
        self.conn = connect_db()
        self.pageFPF = pageFPF
        self.patient_id = patient_id
        
        self.stackWidFPF = self.pageFPF.findChild(QStackedWidget, "stackWidFPF")
        
        self.prev_btn = self.pageFPF.findChild(QPushButton, "pushBtnPrevFPF")
        self.next_btn = self.pageFPF.findChild(QPushButton, "pushBtnNextFPF")

        self.prev_btn.clicked.connect(self.go_prev)
        self.next_btn.clicked.connect(self.go_next)

        self.update_nav_buttons()  
        self.personal_info()
    
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
        
    def personal_info(self):
        self.stackWidFPF.setCurrentIndex(0)
        self.clt_no = self.pageFPF.findChild(QLineEdit, "clientID")
        self.clt_NHTSy = self.pageFPF.findChild(QLineEdit, "NHTSy")
        self.clt_NHTSn = self.pageFPF.findChild(QLineEdit, "NHTSn")
        self.clt_4PsY = self.pageFPF.findChild(QLineEdit, "fourPsY")
        self.clt_4PsN = self.pageFPF.findChild(QLineEdit, "fourPsN")
        self.clt_NSAdd = self.pageFPF.findChild(QLineEdit, "clientFP_NSAdd")
        self.clt_BarAdd = self.pageFPF.findChild(QLineEdit, "clientFP_BarAdd")
        self.clt_MuniAdd = self.pageFPF.findChild(QLineEdit, "clientFP_MuniAdd")
        self.clt_ProvAdd = self.pageFPF.findChild(QLineEdit, "clientFP_ProvAdd")
        self.clt_civilS = self.pageFPF.findChild(QComboBox, "clientFPCivilStat")
        self.clt_religion = self.pageFPF.findChild(QComboBox, "clientFPReligion")
        
        self.prefilled_pinfo()
        
    def prefilled_pinfo(self):
        personal_info_page = self.stackWidFPF.currentWidget()  
        
        self.clt_phNo = personal_info_page.findChild(QLineEdit, "philHealthNo")
        self.clt_lname = personal_info_page.findChild(QLineEdit, "clientFPLname")
        self.clt_fname = personal_info_page.findChild(QLineEdit, "clientFPFname")
        self.clt_minit = personal_info_page.findChild(QLineEdit, "clientFPMidI")
        self.clt_dob = personal_info_page.findChild(QDateEdit, "clientFPDOB")
        self.clt_age = personal_info_page.findChild(QLineEdit, "clientFPAge")
        self.clt_occupation = personal_info_page.findChild(QLineEdit, "clientFPOccu")
        self.clt_contact = personal_info_page.findChild(QLineEdit, "clientFPCont")
        
        query = """
            SELECT PAT_PHNUM, PAT_LNAME, PAT_FNAME, LEFT(PAT_MNAME, 1) || '.' AS MIDDLE_INITIAL, 
                PAT_DOB, PAT_AGE, PAT_OCCU, PAT_CNUM
            FROM PATIENT
            WHERE PAT_ID = %s
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (self.patient_id,))
        result = cursor.fetchone()

        if result:
            self.clt_phNo.setText(result[0]) 
            self.clt_lname.setText(result[1])  
            self.clt_fname.setText(result[2])  
            self.clt_minit.setText(result[3])  
            self.clt_dob.setDate(result[4])    
            self.clt_age.setText(result[5])
            self.clt_occupation.setText(result[6])
            self.clt_contact.setText(result[7])
            
        else:
            print("No patient found for PAT_ID:", self.patient_id)
        
        self.spo_lname = personal_info_page.findChild(QLineEdit, "spouseFPLname")
        self.spo_fname = personal_info_page.findChild(QLineEdit, "spouseFPFname")
        self.spo_minit = personal_info_page.findChild(QLineEdit, "spouseFPMidI")
        self.spo_dob = personal_info_page.findChild(QDateEdit, "spouseFPDOB")
        self.spo_age = personal_info_page.findChild(QLineEdit, "spouseFPAge")
        self.spo_occupation = personal_info_page.findChild(QLineEdit, "spouseFPOccu")
        
        query = """
            SELECT SP_LNAME, SP_FNAME, LEFT(SP_MNAME, 1) || '.' AS MIDDLE_INITIAL, 
                SP_DOB, SP_OCCU
            FROM SPOUSE
            WHERE PAT_ID = %s
        """
        cursor.execute(query, (self.patient_id,))
        spouse_result = cursor.fetchone()

        if spouse_result:
            self.spo_lname.setText(spouse_result[0])
            self.spo_fname.setText(spouse_result[1])
            self.spo_minit.setText(spouse_result[2])
            self.spo_dob.setDate(spouse_result[3])
            self.spo_occupation.setText(spouse_result[4])
        else:
            print("No spouse info found for PAT_ID:", self.patient_id)

        
        cursor.close()



        