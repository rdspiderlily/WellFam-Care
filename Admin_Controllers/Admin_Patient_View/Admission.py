from PyQt5.QtWidgets import (
    QPushButton, QStackedWidget, QLineEdit,
    QCheckBox, QComboBox, QDateEdit, QTimeEdit
)
from datetime import date
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from datetime import date

from PyQt5 import uic

from Database import connect_db

class AdmissionController:
    def __init__(self, pageWFAR, patient_id):
        self.conn = connect_db()
        self.pageWFAR = pageWFAR
        self.patient_id = patient_id
        
        self.stackWidPDS = self.pageWFAR.findChild(QStackedWidget, "stackWidPDS")
        
        # self.prev_btn = self.pageWFAR.findChild(QPushButton, "pushBtnPrevFPF")
        # self.next_btn = self.pageWFAR.findChild(QPushButton, "pushBtnNextFPF")

        # self.prev_btn.clicked.connect(self.go_prev)
        # self.next_btn.clicked.connect(self.go_next)

        # self.update_nav_buttons()  
        self.personal_info()
    
    # def go_prev(self):
    #     current_index = self.stackWidPDS.currentIndex()
    #     if current_index > 0:
    #         self.stackWidPDS.setCurrentIndex(current_index - 1)
    #     self.update_nav_buttons()

    # def go_next(self):
    #     current_index = self.stackWidPDS.currentIndex()
    #     if current_index < self.stackWidPDS.count() - 1:
    #         self.stackWidPDS.setCurrentIndex(current_index + 1)
    #     self.update_nav_buttons()

    # def update_nav_buttons(self):
    #     current_index = self.stackWidPDS.currentIndex()
    #     self.prev_btn.setEnabled(current_index > 0)
    #     self.next_btn.setEnabled(current_index < self.stackWidPDS.count() - 1)
        
    def personal_info(self):
        self.stackWidPDS.setCurrentIndex(0)
        self.pat_sex = self.pageWFAR.findChild(QComboBox, "patientPDSsex")
        self.pat_address = self.pageWFAR.findChild(QLineEdit, "patientPDSaddress")
        self.pat_religion = self.pageWFAR.findChild(QComboBox, "patientPDSreligion")
        self.spouse_religion = self.pageWFAR.findChild(QComboBox, "spousePDSreligion")

        self.prefilled_pinfo()
        
    def prefilled_pinfo(self):
        personal_info_page = self.stackWidPDS.currentWidget()  
        
        self.pat_name = personal_info_page.findChild(QLineEdit, "patientPDSname")
        self.pat_contact = personal_info_page.findChild(QLineEdit, "patientPDScontact")
        self.pat_occupation = personal_info_page.findChild(QLineEdit, "patientPDSoccupation")
        self.pat_dob = personal_info_page.findChild(QDateEdit, "patientPDSdob")
        self.pat_age = personal_info_page.findChild(QLineEdit, "patientPDSage")


        query = """
            SELECT PAT_FNAME || ' ' || LEFT(PAT_MNAME, 1) || '. ' || PAT_LNAME AS FULL_NAME, 
                PAT_CNUM, PAT_OCCU, PAT_DOB, PAT_AGE 
            FROM PATIENT
            WHERE PAT_ID = %s
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (self.patient_id,))
        result = cursor.fetchone()

        if result:
            self.pat_name.setText(result[0]) 
            self.pat_contact.setText(result[1])  
            self.pat_occupation.setText(result[2])  
            self.pat_dob.setDate(result[3])    
            self.pat_age.setText(result[4])
            
        else:
            print("No patient found for PAT_ID:", self.patient_id)
        
        self.spouse_name = personal_info_page.findChild(QLineEdit, "spousePDSname")
        self.spouse_occupation = personal_info_page.findChild(QLineEdit, "spousePDSoccupation")
        self.spouse_age = personal_info_page.findChild(QLineEdit, "spousePDSage")
        self.spouse_contact = personal_info_page.findChild(QLineEdit, "spousePDScontact")
     
        query = """
            SELECT SP_FNAME || ' ' || LEFT(SP_MNAME, 1) || '. ' || SP_LNAME AS FULL_NAME, 
                SP_OCCU, SP_CNUM, SP_DOB
            FROM SPOUSE
            WHERE PAT_ID = %s
        """
        cursor.execute(query, (self.patient_id,))
        spouse_result = cursor.fetchone()

        if spouse_result:
            self.spouse_name.setText(spouse_result[0])
            self.spouse_occupation.setText(spouse_result[1])
            self.spouse_contact.setText(spouse_result[2])
            
            from datetime import date
            dob = spouse_result[3]
            if dob:
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                self.spouse_age.setText(str(age))
            else:
                self.spouse_age.setText("")
                    
        else:
            print("No spouse info found for PAT_ID:", self.patient_id)

        cursor.close()