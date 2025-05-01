from PyQt5.QtWidgets import (
    QPushButton, QStackedWidget, QLineEdit,
    QDateEdit, QComboBox, QTimeEdit, QCheckBox,
    QTextEdit
)
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from datetime import date

from PyQt5 import uic

from Database import connect_db

class MaternalRecordsController:
    def __init__(self, pageMSR, patient_id):
        self.conn = connect_db()
        self.pageMSR = pageMSR
        self.patient_id = patient_id
        
        self.stackWidMSR = self.pageMSR.findChild(QStackedWidget, "stackWidMSR")
        
        self.prev_btn = self.pageMSR.findChild(QPushButton, "pushBtnPrev")
        self.next_btn = self.pageMSR.findChild(QPushButton, "pushBtnNext")

        self.prev_btn.clicked.connect(self.go_prev)
        self.next_btn.clicked.connect(self.go_next)

        self.update_nav_buttons()  # Disable prev if on first page, etc.
        self.personal_info()
    
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
        
    def personal_info(self):
        self.stackWidMSR.setCurrentIndex(0)
        self.clt_no = self.pageMSR.findChild(QLineEdit, "clientNoMSR")
        self.clt_eduA = self.pageMSR.findChild(QComboBox, "clientEduAtt")
        self.clt_NSAdd = self.pageMSR.findChild(QLineEdit, "clientNSAdd")
        self.clt_BarAdd = self.pageMSR.findChild(QLineEdit, "clientBarAdd")
        self.clt_MuniAdd = self.pageMSR.findChild(QLineEdit, "clientMuniAdd")
        self.clt_ProvAdd = self.pageMSR.findChild(QLineEdit, "clientProvAdd")
        self.clt_PNEName = self.pageMSR.findChild(QLineEdit, "PNEName")
        self.clt_PNEContact = self.pageMSR.findChild(QLineEdit, "PNEContact")
        self.clt_PNEAdd = self.pageMSR.findChild(QLineEdit, "PNEAdd")
        
        self.clt_dateArrival = self.pageMSR.findChild(QDateEdit, "dateArrival")
        self.clt_timeArrival = self.pageMSR.findChild(QTimeEdit, "timeArrival")
        self.clt_timeDisposition = self.pageMSR.findChild(QTimeEdit, "timeDisposition")
        self.clt_planMKidsY = self.pageMSR.findChild(QCheckBox, "planMoreKidYes")
        self.clt_planMKidsN = self.pageMSR.findChild(QCheckBox, "planMoreKidNo")
        self.clt_FPMCurY = self.pageMSR.findChild(QCheckBox, "FPMetCurrYes")
        self.clt_FPMCurN = self.pageMSR.findChild(QCheckBox, "FPMetCurrNo")
        self.clt_FPMPrevY = self.pageMSR.findChild(QCheckBox, "FPMetPrevYes")
        self.clt_FPMPrevN = self.pageMSR.findChild(QCheckBox, "FPMetPrevNo")
        
        self.clt_FPUv= self.pageMSR.findChild(QCheckBox, "FPMETUvss")
        self.clt_FPUi = self.pageMSR.findChild(QCheckBox, "FPMETUiud")
        self.clt_FPUp = self.pageMSR.findChild(QCheckBox, "FPMETUpill")
        self.clt_FPUd = self.pageMSR.findChild(QCheckBox, "FPMETUdmpa")
        self.clt_FPUn = self.pageMSR.findChild(QCheckBox, "FPMETUnfp")
        self.clt_FPUl = self.pageMSR.findChild(QCheckBox, "FPMETUlam")
        self.clt_FPUc = self.pageMSR.findChild(QCheckBox, "FPMETUcondom")
        self.clt_FPUothers = self.pageMSR.findChild(QDateEdit, "FPMETUothers")
        self.clt_PLANS = self.pageMSR.findChild(QTextEdit, "textEditPLANS")
        
        self.prefilled_pinfo()
        
    def prefilled_pinfo(self):
        personal_info_page = self.stackWidMSR.currentWidget()  
        
        self.clt_lname = personal_info_page.findChild(QLineEdit, "clientLName")
        self.clt_fname = personal_info_page.findChild(QLineEdit, "clientFname")
        self.clt_minit = personal_info_page.findChild(QLineEdit, "clientMidI")
        self.clt_dob = personal_info_page.findChild(QDateEdit, "clientDOB")
        
        query = """
            SELECT PAT_LNAME, PAT_FNAME, LEFT(PAT_MNAME, 1) || '.' AS MIDDLE_INITIAL, PAT_DOB
            FROM PATIENT
            WHERE PAT_ID = %s
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (self.patient_id,))
        result = cursor.fetchone()

        if result:
            self.clt_lname.setText(result[0])  
            self.clt_fname.setText(result[1])  
            self.clt_minit.setText(result[2])  
            self.clt_dob.setDate(result[3])    
        else:
            print("No patient found for PAT_ID:", self.patient_id)

        cursor.close()
        