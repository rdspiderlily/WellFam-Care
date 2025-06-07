from PyQt5.QtWidgets import QDialog, QLineEdit, QPushButton, QStackedWidget, QLabel, QTableWidget
from PyQt5 import uic
from PyQt5.QtGui import QIcon

from MidwifeAide_Controllers.MA_Patient_View.MA_PersonalInfo import MAPersonalInfoController
from MidwifeAide_Controllers.MA_Patient_View.MA_MaternalRecords import MAMaternalRecordsController
from MidwifeAide_Controllers.MA_Patient_View.MA_FamPlan import MAFamPlanController
from MidwifeAide_Controllers.MA_Patient_View.MA_Admission import MAAdmissionController
from MidwifeAide_Controllers.MA_Patient_View.MA_AppointmentH import MAAppointmentHistoryController

from PyQt5.QtCore import pyqtSignal

class MAViewPatientDialog(QDialog):
    def __init__(self,patient_id, user_id, parent=None):
        super().__init__(parent)
        uic.loadUi("wfui/view_patient_information.ui", self)
        self.setWindowTitle("Patient Details")
        self.setWindowIcon(QIcon("wfpics/logo1.jpg"))
        
        self.patient_id = patient_id
        self.user_id = user_id
        
        self.stackedWidget = self.findChild(QStackedWidget, "sWidgetviewPat")
        self.info_btn = self.findChild(QPushButton, "pushBtnPatInfo")
        self.msr_btn = self.findChild(QPushButton, "pushBtnMSR")
        self.fpf_btn = self.findChild(QPushButton, "pushBtnFPF")
        self.wfar_btn = self.findChild(QPushButton, "pushBtnAR")
        self.ah_btn = self.findChild(QPushButton, "pushBtnAH")

        
        self.info_btn.clicked.connect(self.pat_info)
        self.msr_btn.clicked.connect(self.msr)
        self.fpf_btn.clicked.connect(self.fpf)
        self.wfar_btn.clicked.connect(self.wfar)
        self.ah_btn.clicked.connect(self.ah)
        
        self.pat_info()
        
    def pat_info(self):
        self.stackedWidget.setCurrentIndex(0)
        self.set_active_button(self.info_btn)
        page = self.stackedWidget.widget(0)
        self.personal_info_widget = MAPersonalInfoController(page, self.patient_id)
        
    def msr(self):
        self.stackedWidget.setCurrentIndex(1)
        self.set_active_button(self.msr_btn)
        pageMSR = self.stackedWidget.widget(1)
        self.maternal_records_widget = MAMaternalRecordsController(pageMSR, self.patient_id, self.user_id)
        
    def fpf(self):
        self.stackedWidget.setCurrentIndex(2)
        self.set_active_button(self.fpf_btn)
        pageFPF = self.stackedWidget.widget(2)
        self.famplan_widget = MAFamPlanController(pageFPF, self.patient_id, self.user_id)
        
    def wfar(self):
        self.stackedWidget.setCurrentIndex(3)
        self.set_active_button(self.wfar_btn)
        pageWFAR = self.stackedWidget.widget(3)
        self.admission_widget = MAAdmissionController(pageWFAR, self.patient_id, self.user_id)

    def ah(self):
        self.stackedWidget.setCurrentIndex(4)
        self.set_active_button(self.ah_btn)
        appHpage = self.stackedWidget.widget(4)
        self.app_history_widget = MAAppointmentHistoryController(appHpage, self.patient_id)
    
    def set_active_button(self, active_button):
        for btn in [self.info_btn, self.msr_btn, self.fpf_btn, self.wfar_btn, self.ah_btn]:
            btn.setProperty("active", btn == active_button)
            btn.style().unpolish(btn)
            btn.style().polish(btn)