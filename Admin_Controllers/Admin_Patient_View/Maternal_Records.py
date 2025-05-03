from PyQt5.QtWidgets import (
    QPushButton, QStackedWidget, QLineEdit,
    QDateEdit, QComboBox, QTimeEdit, QCheckBox,
    QTextEdit, QSpinBox, QDoubleSpinBox, QMessageBox
)
from PyQt5 import uic
from PyQt5.QtCore import Qt, QDate, QTime
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
        
        self.save_btn = self.pageMSR.findChild(QPushButton, "btnSaveMSR")
        self.save_btn.clicked.connect(self.on_save_clicked)
        
        self.edit_btn = self.pageMSR.findChild(QPushButton, "btnEditMSR")
        self.edit_btn.clicked.connect(self.enable_editing_mode)
        
        self.cancel_btn = self.pageMSR.findChild(QPushButton, "btnCancelMSR")
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)

        self.set_all_fields_read_only()
        
        self.prev_btn.clicked.connect(self.go_prev)
        self.next_btn.clicked.connect(self.go_next)

        self.update_nav_buttons()  # Disable prev if on first page, etc.
        self.personal_info()
        self.medicalH_info()
        self.physicalE_info()
        self.birthEPlan_info()
    
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

        # Keep prefilled fields disabled
        self.clt_lname.setReadOnly(True)
        self.clt_fname.setReadOnly(True)
        self.clt_minit.setReadOnly(True)
        self.clt_dob.setEnabled(False)
    
    def save_all_page(self):
        try:
            self.save_basic_pinfo()
            self.save_other_pinfo()
            self.save_medical()
            self.save_obstetrical()
            self.save_physicalE()
            self.save_pelvicE()
            self.save_birthEPlan()
            print("Saved successfully.")
        except Exception as e:
            print("Error while saving:", e)
        
    def personal_info(self):
        self.stackWidMSR.setCurrentIndex(0)
        self.load_basic_pinfo_widgets()
        self.load_other_pinfo_widgets()
        self.load_basic_pinfo()
        self.load_other_pinfo()
        self.prefilled_basic_pinfo()
        
    def prefilled_basic_pinfo(self):
        try:
            self.load_basic_pinfo_widgets()

            if not all([self.clt_lname, self.clt_fname, self.clt_minit, self.clt_dob]):
                print("Some input fields are not initialized. Please check objectNames in the UI.")
                return

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

        except Exception as e:
            self.conn.rollback()
            print("Error in prefilled_basic_pinfo:", e)

    def load_basic_pinfo_widgets(self):
        self.clt_lname = self.pageMSR.findChild(QLineEdit, "clientLName")
        self.clt_fname = self.pageMSR.findChild(QLineEdit, "clientFname")
        self.clt_minit = self.pageMSR.findChild(QLineEdit, "clientMidI")
        self.clt_dob = self.pageMSR.findChild(QDateEdit, "clientDOB")
        
        self.clt_no = self.pageMSR.findChild(QLineEdit, "clientNoMSR")
        self.clt_eduA = self.pageMSR.findChild(QComboBox, "clientEduAtt")
        self.clt_NSAdd = self.pageMSR.findChild(QLineEdit, "clientNSAdd")
        self.clt_BarAdd = self.pageMSR.findChild(QLineEdit, "clientBarAdd")
        self.clt_MuniAdd = self.pageMSR.findChild(QLineEdit, "clientMuniAdd")
        self.clt_ProvAdd = self.pageMSR.findChild(QLineEdit, "clientProvAdd")
        self.clt_PNEName = self.pageMSR.findChild(QLineEdit, "PNEName")
        self.clt_PNEContact = self.pageMSR.findChild(QLineEdit, "PNEContact")
        self.clt_PNEAdd = self.pageMSR.findChild(QLineEdit, "PNEAdd")
    
    def load_basic_pinfo(self):
        try:
            cursor = self.conn.cursor()
            label_to_widget = {
                "Client No.": self.clt_no,
                "Educational Attainment": self.clt_eduA,
                "No/Street": self.clt_NSAdd,
                "Barangay": self.clt_BarAdd,
                "Municipality": self.clt_MuniAdd,
                "Province": self.clt_ProvAdd,
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

    def save_basic_pinfo(self):
        try:
            cursor = self.conn.cursor()
            
            # Create a mapping of widget values to FORM_OPT_LABEL (you must make sure labels match)
            responses = {
                "Client No.": self.clt_no.text(),
                "Educational Attainment": self.clt_eduA.currentText(),
                "No/Street": self.clt_NSAdd.text(),
                "Barangay": self.clt_BarAdd.text(),
                "Municipality": self.clt_MuniAdd.text(),
                "Province": self.clt_ProvAdd.text(),
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
        self.stackWidMSR.setCurrentIndex(1)
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

            if not all([self.obs_lmp, self.obs_aog, self.obs_edc]):
                print("Some obstetrical input fields are not initialized. Please check objectNames in the UI.")
                return

            query = """
                SELECT PAT_LMP, PAT_AOG, PAT_EDC
                FROM PATIENT
                WHERE PAT_ID = %s
            """
            cursor = self.conn.cursor()
            cursor.execute(query, (self.patient_id,))
            result = cursor.fetchone()

            if result:
                self.obs_lmp.setDate(result[0])
                self.obs_aog.setValue(result[1])
                self.obs_edc.setDate(result[2])
            else:
                print("No patient found for PAT_ID:", self.patient_id)

            cursor.close()

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
                        widget.setDate(QDate.fromString(value, "yyyy-MM-dd"))
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
                "Date of last delivery": self.obs_dold.date().toString("yyyy-MM-dd"),
                "Type of Delivery": self.obs_tod.currentText(), 
                "Past Menstrual Period": self.obs_pmp.date().toString("yyyy-MM-dd"),
                
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
        self.stackWidMSR.setCurrentIndex(2)
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
        self.stackWidMSR.setCurrentIndex(3)
        self.load_birthEPlan_widgets()
        self.load_birthEPlan()
        self.prefilled_birthEPlan()
    
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
            QMessageBox.information(self.pageMSR, "Success", "Information saved successfully.")
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
        self.clt_no.clear()
        self.clt_eduA.setCurrentIndex(-1)
        self.clt_NSAdd.clear()
        self.clt_BarAdd.clear()
        self.clt_MuniAdd.clear()
        self.clt_ProvAdd.clear()
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
        self.prefilled_basic_pinfo()
        self.prefilled_obstetrical()
        self.load_basic_pinfo()
        self.load_other_pinfo()
        self.load_medical()
        self.load_obstetrical()
        self.load_physicalE()
        self.load_pelvicE()
        self.load_birthEPlan()
    
