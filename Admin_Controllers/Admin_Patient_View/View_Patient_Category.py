from PyQt5.QtWidgets import QDialog, QLineEdit, QPushButton, QStackedWidget, QLabel, QTableWidget
from PyQt5 import uic
from PyQt5.QtGui import QIcon

from Admin_Controllers.Admin_Patient_View.Personal_Info import PersonalInfoController
from Admin_Controllers.Admin_Patient_View.Appointment_History import AppointmentHistoryController

class ViewPatientDialog(QDialog):
    def __init__(self,patient_id, parent=None):
        super().__init__(parent)
        uic.loadUi("wfui/view_patient_information.ui", self)
        self.setWindowTitle("Patient Details")
        self.setWindowIcon(QIcon("wfpics/logo1.jpg"))
        
        self.patient_id = patient_id
        
        self.stackedWidget = self.findChild(QStackedWidget, "sWidgetviewPat")
        self.info_btn = self.findChild(QPushButton, "pushBtnPatInfo")
        self.msr_btn = self.findChild(QPushButton, "pushBtnMSR")
        self.fpf_btn = self.findChild(QPushButton, "pushBtnFPF")
        self.ph_btn = self.findChild(QPushButton, "pushBtnPH")
        self.wfar_btn = self.findChild(QPushButton, "pushBtnAR")
        self.ah_btn = self.findChild(QPushButton, "pushBtnAH")

        
        self.info_btn.clicked.connect(self.pat_info)
        self.msr_btn.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.fpf_btn.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.ph_btn.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        self.wfar_btn.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(4))
        self.ah_btn.clicked.connect(self.ah)
        
        self.pat_info()
        self.ah()
        
    def pat_info(self):
        self.stackedWidget.setCurrentIndex(0)
        page = self.stackedWidget.widget(0)
        self.personal_info_widget = PersonalInfoController(page, self.patient_id)
        
    def msr(self):
        self.stackedWidget.setCurrentIndex(1)
        
    def fpf(self):
        self.stackedWidget.setCurrentIndex(2)
        
    def ph(self):
        self.stackedWidget.setCurrentIndex(3)
        
    def wfar(self):
        self.stackedWidget.setCurrentIndex(4)

    def ah(self):
        self.stackedWidget.setCurrentIndex(5)
        appHpage = self.stackedWidget.widget(5)
        self.app_history_widget = AppointmentHistoryController(appHpage, self.patient_id)