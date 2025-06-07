from PyQt5.QtWidgets import (
    QPushButton, QStackedWidget, QLineEdit,
    QDateEdit, QComboBox, QTimeEdit,
    QTextEdit, QMessageBox
)
from PyQt5.QtCore import QDate, QTime
from datetime import date
import os
import webbrowser
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, TextStringObject, NumberObject, BooleanObject

from Database import connect_db
from Admin_Controllers.Admin_Patient_View.AutofillPersonalInfo import AutofillPersonalInfoController

class AdmissionController:
    def __init__(self, pageWFAR, patient_id, user_id):
        self.conn = connect_db()
        self.pageWFAR = pageWFAR
        self.patient_id = patient_id
        self.user_id = user_id
        self.autofill = AutofillPersonalInfoController(self.conn)
        
        self.stackWidPDS = self.pageWFAR.findChild(QStackedWidget, "stackWidPDS")
        
        self.save_btn = self.pageWFAR.findChild(QPushButton, "btnSavePDS")
        self.edit_btn = self.pageWFAR.findChild(QPushButton, "btnEditPDS")
        self.cancel_btn = self.pageWFAR.findChild(QPushButton, "btnCancelPDS")
        self.viewPDF_btn = self.pageWFAR.findChild(QPushButton, "viewPdsPDF")
        
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.edit_btn.clicked.connect(self.enable_editing_mode)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        self.viewPDF_btn.clicked.connect(self.show_pdfPrint)

        self.set_all_fields_read_only()
        self.pat_ds()
    
    # View-only Maternal Dialog
    def set_all_fields_read_only(self):
        def disable_widgets(widget):
            if isinstance(widget, (QLineEdit, QTextEdit)):
                widget.setReadOnly(True)
            elif isinstance(widget, (QComboBox, QDateEdit, QTimeEdit)):
                widget.setEnabled(False)
            elif isinstance(widget, QStackedWidget):
                for i in range(widget.count()):
                    disable_widgets(widget.widget(i))
            elif hasattr(widget, "children"):
                for child in widget.children():
                    disable_widgets(child)

        disable_widgets(self.pageWFAR)
        self.cancel_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

    def enable_editing_mode(self):
        def enable_widgets(widget):
            if isinstance(widget, (QLineEdit, QTextEdit)):
                widget.setReadOnly(False)
            elif isinstance(widget, (QComboBox, QDateEdit, QTimeEdit)):
                widget.setEnabled(True)
                if isinstance(widget, QDateEdit) and widget.date() is None:
                    widget.setDate(QDate.currentDate())  
                if isinstance(widget, QTimeEdit) and widget.time() is None:
                    widget.setTime(QTime.currentTime())  
            elif isinstance(widget, QStackedWidget):
                for i in range(widget.count()):
                    enable_widgets(widget.widget(i))
            elif hasattr(widget, "children"):
                for child in widget.children():
                    enable_widgets(child)

        enable_widgets(self.pageWFAR)
        self.cancel_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

        self.pat_name.setReadOnly(True)
        self.pat_address.setReadOnly(True)
        self.pat_occu.setReadOnly(True)
        self.pat_dob.setEnabled(False)
        self.pat_age.setReadOnly(True)
        self.pat_contact.setReadOnly(True)
        self.spo_name.setReadOnly(True)
        self.spo_occu.setReadOnly(True)
        self.spo_age.setReadOnly(True)
        self.spo_contact.setReadOnly(True)
    
    def save_all_page(self):
        try:
            self.save_patientData()
            
            form_id = self.get_form_id('Well-Family Admission Form')
            if form_id is None:
                print("Form ID for Admission Form is not found.")
                return
            ps_id = None
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO PATIENT_FORM (PF_DATEFILLED, FORM_ID, PAT_ID, PS_ID, PF_FILLEDBY)
                VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s)
            """, (form_id, self.patient_id, ps_id, self.user_id))
            self.conn.commit()
            cursor.close()
            
            QMessageBox.information(self.pageWFAR, "Success", "Patient Data Sheet saved successfully.")
        except Exception as e:
            print("Error while saving:", e)
    
    def get_form_id(self, form_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT FORM_ID FROM FORM WHERE FORM_NAME = %s", (form_name,))
        form_id = cursor.fetchone()
        cursor.close()
        return form_id[0] if form_id else None
        
    def pat_ds(self):
        self.load_patientData_widgets()
        self.load_patientData()
        self.prefilled_patientData()
        
    def prefilled_patientData(self):
        try:
            self.load_patientData_widgets()

            if not all([
                self.pat_name, self.pat_address, self.pat_occu,
                self.pat_dob, self.pat_age, self.pat_contact
            ]):
                print("Some input fields are not initialized. Please check objectNames in the UI.")
                return

            info = self.autofill.get_basic_info(self.patient_id)
            if info:
                self.pat_name.setText(f"{info['fname']} {info['minit']} {info['lname']}")
                self.pat_address.setText(f"{info['add_ns']} {info['add_b']} {info['add_mc']} {info['lname']}")
                self.pat_occu.setText(info["occupation"])
                self.pat_dob.setDate(info["dob"])
                self.pat_age.setText(info["age"])
                self.pat_contact.setText(info["contact"])
                
            if not all([
                self.spo_name, self.spo_occu, self.spo_age, self.spo_contact
            ]):
                print("Some input fields are not initialized. Please check objectNames in the UI.")
                return
            
            info = self.autofill.spouse_basic_info(self.patient_id)
            if info:
                self.spo_name.setText(f"{info['spo_fname']} {info['spo_minit']} {info['spo_lname']}")
                self.spo_occu.setText(info["spo_occupation"])
                self.spo_age.setText(info["spo_age"])
                self.spo_contact.setText(info["spo_contact"])
            
        except Exception as e:
            self.conn.rollback()
            print("Error in prefilled_pinfo:", e)

    def load_patientData_widgets(self):
        self.pat_name = self.pageWFAR.findChild(QLineEdit, "patientPDSname")
        self.pat_address = self.pageWFAR.findChild(QLineEdit, "patientPDSaddress")
        self.pat_occu = self.pageWFAR.findChild(QLineEdit, "patientPDSoccupation")
        self.pat_dob = self.pageWFAR.findChild(QDateEdit, "patientPDSdob")
        self.pat_age = self.pageWFAR.findChild(QLineEdit, "patientPDSage")
        self.pat_contact = self.pageWFAR.findChild(QLineEdit, "patientPDScontact")
        
        self.spo_name = self.pageWFAR.findChild(QLineEdit, "spousePDSname")
        self.spo_occu = self.pageWFAR.findChild(QLineEdit, "spousePDSoccupation")
        self.spo_age = self.pageWFAR.findChild(QLineEdit, "spousePDSage")
        self.spo_contact = self.pageWFAR.findChild(QLineEdit, "spousePDScontact")
        
        self.pat_sex = self.pageWFAR.findChild(QComboBox, "patientPDSsex")
        self.pat_religion = self.pageWFAR.findChild(QComboBox, "patientPDSreligion")
        self.spo_religion = self.pageWFAR.findChild(QComboBox, "spousePDSreligion")
        
        self.chief_complaint = self.pageWFAR.findChild(QLineEdit, "PDSccomplaint")
        self.history_presentC = self.pageWFAR.findChild(QLineEdit, "PDShopcondition")
        self.admit_diagnosis = self.pageWFAR.findChild(QLineEdit, "PDSadiagnosis")
        
        self.admi_date = self.pageWFAR.findChild(QDateEdit, "PDSadD")
        self.admi_time = self.pageWFAR.findChild(QTimeEdit, "PDSadT")
        self.admi_by = self.pageWFAR.findChild(QLineEdit, "PDSadB")
        self.disc_date = self.pageWFAR.findChild(QDateEdit, "PDSdisD")
        self.disc_time = self.pageWFAR.findChild(QTimeEdit, "PDSdisT")
        self.disc_by = self.pageWFAR.findChild(QLineEdit, "PDSdisB")
        
        self.final_diagnosis = self.pageWFAR.findChild(QLineEdit, "PDSfdiagnosis")
        self.attending_midwife = self.pageWFAR.findChild(QLineEdit, "PDSamidwife")
    
    def load_patientData(self):
        try:
            cursor = self.conn.cursor()
            label_to_widget = {
                "PDS: Patient Sex": self.pat_sex,
                "PDS: Patient Religion": self.pat_religion,

                "PDS: Spouse Religion": self.spo_religion,
                
                "PDS: Chief Complaint": self.chief_complaint,
                "PDS: History of Present Condition": self.history_presentC,
                "PDS: Admitting Diagnosis": self.admit_diagnosis,
                
                "PDS: Admission Date": self.admi_date,
                "PDS: Admission Time": self.admi_time,
                "PDS: Admission By": self.admi_by,
                "PDS: Discharge Date": self.disc_date,
                "PDS: Discharge Time": self.disc_time,
                "PDS: Discharge By": self.disc_by,
                
                "PDS: Final Diagnosis": self.final_diagnosis,
                "PDS: Attending Midwife Name": self.attending_midwife
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
                    elif isinstance(widget, QDateEdit):
                        widget.setDate(QDate.fromString(value, "MM-dd-yyyy"))
                    elif isinstance(widget, QTimeEdit):
                        time = QTime.fromString(value, "hh:mm AP")
                        if time.isValid():
                            widget.setTime(time)
                            
        except Exception as e:
            print("Error loading basic personal info:", e)
    
    def save_patientData(self):
        try:
            cursor = self.conn.cursor()
            
            responses = {
                "PDS: Patient Sex": self.pat_sex.currentText(),
                "PDS: Patient Religion": self.pat_religion.currentText(),

                "PDS: Spouse Religion": self.spo_religion.currentText(),
                
                "PDS: Chief Complaint": self.chief_complaint.text(),
                "PDS: History of Present Condition": self.history_presentC.text(),
                "PDS: Admitting Diagnosis": self.admit_diagnosis.text(),
                
                "PDS: Admission Date": self.admi_date.date().toString("MM-dd-yyyy"),
                "PDS: Admission Time": self.admi_time.time().toString("hh:mm AP"),
                "PDS: Admission By": self.admi_by.text(),
                "PDS: Discharge Date": self.disc_date.date().toString("MM-dd-yyyy"),
                "PDS: Discharge Time": self.disc_time.time().toString("hh:mm AP"),
                "PDS: Discharge By": self.disc_by.text(),
                
                "PDS: Final Diagnosis": self.final_diagnosis.text(),
                "PDS: Attending Midwife Name": self.attending_midwife.text()
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
            print("Error saving admission data:", e)
            self.conn.rollback()
    
    def on_save_clicked(self):
        reply = QMessageBox.question(
            self.pageWFAR,
            "Confirm Save",
            "Are you sure you want to save the changes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.save_all_page()
            self.set_all_fields_read_only()

    def on_cancel_clicked(self):
        reply = QMessageBox.question(
            self.pageWFAR,
            "Confirm Cancel",
            "Are you sure you want to cancel? Unsaved changes will be lost.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.cancel_editing()

    def reset_fields(self):
        self.pat_sex.clear()
        self.pat_religion.setCurrentIndex(-1)
        self.spo_religion.setCurrentIndex(-1)
        self.chief_complaint.clear()
        self.history_presentC.clear()
        self.admit_diagnosis.clear()
        
        self.admi_date.setDate(date.today())
        self.admi_time.setTime(QTime(0, 0))
        self.admi_by.clear()
        self.disc_date.setDate(date.today())
        self.disc_time.setTime(QTime(0, 0))
        self.disc_by.clear()
        
        self.final_diagnosis.clear()
        self.attending_midwife.clear()
    
    def cancel_editing(self):
        self.reset_fields()
        self.set_all_fields_read_only()
        self.prefilled_patientData()
        self.load_patientData()
        
    def show_pdfPrint(self):
        self.view_filled_pdf()

    def fetch_patient_data(self):
        try:
            cursor = self.conn.cursor()
            
            data = {}
            
            cursor.execute("""
                SELECT
                    CONCAT(
                        PAT_FNAME, ' ',
                        CASE
                            WHEN PAT_MNAME IS NOT NULL AND PAT_MNAME != ''
                                THEN CONCAT(LEFT(PAT_MNAME, 1), '. ')
                            ELSE ''
                        END,
                        PAT_LNAME
                    ) AS PATIENT_NAME,
                    CONCAT (PAT_ADDNS, ', ', PAT_ADDB, ', ', PAT_ADDMC, ', ', PAT_ADDP) AS PATIENT_ADD,
                    PAT_OCCU, TO_CHAR(PAT_DOB, 'MM-DD-YYYY') AS dob, PAT_CNUM, PAT_AGE
                FROM PATIENT
                WHERE PAT_ID = %s
            """, (self.patient_id,))
            patient_data = cursor.fetchone()

            if patient_data:
                data["PatName"] = patient_data[0] or ""
                data["PatAddress"] = patient_data[1] or ""
                data["PatOccu"] = patient_data[2] or ""
                data["PatDOB"] = patient_data[3]
                data["PatCont"] = patient_data[4] or ""
                data["PatAge"] = patient_data[5] or ""
            else:
                print("No data found for the patient.")
            
            cursor.execute("""
                SELECT
                    CONCAT(
                        SP_FNAME, ' ',
                        CASE
                            WHEN SP_MNAME IS NOT NULL AND SP_MNAME != ''
                                THEN CONCAT(LEFT(SP_MNAME, 1), '. ')
                            ELSE ''
                        END,
                        SP_LNAME
                    ) AS SPOUSE_NAME,
                    SP_OCCU, SP_CNUM, SP_AGE
                FROM SPOUSE
                WHERE PAT_ID = %s
            """, (self.patient_id,))
            patient_data = cursor.fetchone()

            if patient_data:
                data["SpoName"] = patient_data[0] or ""
                data["SpoOccu"] = patient_data[1] or ""
                data["SpoCont"] = patient_data[2] or ""
                data["SpoAge"] = patient_data[3] or ""
            else:
                print("No data found for the spouse.")

            label_to_field = {
                "PDS: Patient Sex": "PatSex",   
                "PDS: Patient Religion": "PatReligion",
                "PDS: Spouse Religion": "SpoReligion",
                
                "PDS: Chief Complaint": "cComplaint",
                "PDS: History of Present Condition": "hopCondition",
                "PDS: Admitting Diagnosis": "aDiagnosis",
                
                "PDS: Admission Date": "aDate",
                "PDS: Admission Time": "aTime",
                "PDS: Admission By": "aBy",
                "PDS: Discharge Date": "dDate",
                "PDS: Discharge Time": "dTime",
                "PDS: Discharge By": "dBy",
                
                "PDS: Final Diagnosis": "fDiagnosis",
                "PDS: Attending Midwife Name": "amName",
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

                if field_name:
                    data[field_name] = value if value else ""
            
            return data

        except Exception as e:
            print("Error fetching patient data for Patient Data Sheet:", e)
            return {}

    def view_filled_pdf(self):
        data = self.fetch_patient_data()
        if data:
            input_pdf = "form_templates/AdmissionFormview.pdf"
            output_pdf = f"temp/PatientDataSheet_{self.patient_id}.pdf"
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
            writer._root_object["/AcroForm"].update({
                NameObject("/NeedAppearances"): BooleanObject(True)
            })
        else:
            writer._root_object.update({
                NameObject("/AcroForm"): NameObject("/NeedAppearances")({
                    NameObject("/NeedAppearances"): BooleanObject(True)
                })
            })

        def safe_update_field(obj, field_name, value):
            if value is None:
                return
            try:
                obj.update({
                    NameObject("/V"): TextStringObject(str(value)),
                    NameObject("/Ff"): NumberObject(1) 
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
