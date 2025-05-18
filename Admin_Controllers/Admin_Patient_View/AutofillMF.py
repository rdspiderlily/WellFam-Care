class AutofillMatFamController:
    def __init__(self, conn):
        self.conn = conn
    
    def matTOfam(self, patient_id):
        query = """
            SELECT fo.FORM_OPT_LABEL, fr.FORM_RES_VAL
            FROM FORM_RESPONSE fr
            JOIN FORM_OPTION fo ON fr.FORM_OPT_ID = fo.FORM_OPT_ID
            JOIN FORM_CATEGORY fc ON fo.FORM_CAT_ID = fc.FORM_CAT_ID
            JOIN FORM_PAGE fp ON fc.FORM_PAGE_ID = fp.FORM_PAGE_ID
            JOIN FORM f ON fp.FORM_ID = f.FORM_ID
            WHERE fr.PAT_ID = %s
            AND f.FORM_ID = 1
            AND fo.FORM_OPT_LABEL IN (
                'Client No.',
                'Educational Attainment',
                'Living children',
                'Plan to have more children?',
                'Severe Headache/Dizziness',
                'Yellowish discoloration',
                'Family history of CVA (strokes)',
                'Severe chest pain',
                'Smoking',
                'Full Term', 'Preterm', 'Abortion',
                'Date of last delivery', 'Type of Delivery', 'Past Menstrual Period',
                'Ectopic Pregnancy/H.mole',
                'Weight', 'Height', 'Blood Pressure: Systolic', 'Blood Pressure: Diastolic',
                'Pale', 'Yellowish',
                'Enlarged lymph nodes', 'Mass', 'Nipple discharge'
            )
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (patient_id,))
                result = cursor.fetchall()  

            if result:
                data = {label: value for label, value in result}  

                keys = {
                    "Client No.": "clientno",
                    "Educational Attainment": "educAtt",
                    "Living children": "nooflivkids",
                    "Plan to have more children?": "planmorekids",
                    #MedHistory
                    "Severe Headache/Dizziness": "svheadache",
                    "Yellowish discoloration": "yellow/jaundice",
                    "Family history of CVA (strokes)": "CVAhistory",
                    "Severe chest pain": "svchestpain",
                    "Smoking": "smoking",
                    #ObsHistory
                    "Full Term": "NOPfullterm", 
                    "Preterm": "NOPpreterm", 
                    "Abortion": "NOPabortion",
                    "Date of last delivery": "dateOLdelivery",
                    "Type of Delivery": "typeOLdelivery",
                    "Past Menstrual Period": "pmp",
                    "Ectopic Pregnancy/H.mole": "ectopicHmole",
                    #PhyExamination
                    "Weight": "PEweight",
                    "Height": "PEheight",
                    "Blood Pressure: Systolic": "bpS",
                    "Blood Pressure: Diastolic": "bpD",
                    "Pale": "conjuPale",
                    "Yellowish": "conjuYellowish",
                    "Enlarged lymph nodes": "neckEnNodes",
                    "Mass": "breastMass",
                    "Nipple discharge": "breastNipD",   
                }

                mapped_result = {keys[label]: data[label] for label in keys if label in data}

                return mapped_result

            return None

        except Exception as e:
            print("Error autofilling from Maternal:", e)
            return None
    
    def famTOmat(self, patient_id):
        query = """
            SELECT fo.FORM_OPT_LABEL, fr.FORM_RES_VAL
            FROM FORM_RESPONSE fr
            JOIN FORM_OPTION fo ON fr.FORM_OPT_ID = fo.FORM_OPT_ID
            JOIN FORM_CATEGORY fc ON fo.FORM_CAT_ID = fc.FORM_CAT_ID
            JOIN FORM_PAGE fp ON fc.FORM_PAGE_ID = fp.FORM_PAGE_ID
            JOIN FORM f ON fp.FORM_ID = f.FORM_ID
            WHERE fr.PAT_ID = %s
            AND f.FORM_ID = 2
            AND fo.FORM_OPT_LABEL IN (
                'FP: Client ID',
                'FP: Educational Attainment',
                'FP: No. of Living Children',
                'FP: Plan to have more children',
                'FP: severe headaches/migraine',
                'FP: jaundice',
                'FP: history of stroke/hypertension/heart attack',
                'FP: severe chest pain',
                'FP: Is the client a SMOKER?',
                'FP: Full Term', 'FP: Premature', 'FP: Abortion',
                'FP: Date of Last Delivery', 
                'FP: Type of Last Delivery - Vagina', 'FP: Type of Last Delivery - CSection'
                'FP: Previous Menstrual Period (PMP)',
                'FP: Weight', 'FP: Height', 'FP: Blood Pressure (S)', 'FP: Blood Pressure (D)',
                'FP: C - Pale', 'FP: C - Yellowish',
                'FP: N - Enlarged lymph nodes', 'FP: B - Mass', 'FP: B - Nipple discharge'
            )
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (patient_id,))
                result = cursor.fetchall()  

            if result:
                data = {label: value for label, value in result}  

                keys = {
                    "FP: Client ID": "clientno",
                    "FP: Educational Attainment": "educAtt",
                    "FP: No. of Living Children": "nooflivkids",
                    "FP: Plan to have more children": "planmorekids",
                    #MedHistory
                    "FP: severe headaches/migraine": "svheadache",
                    "FP: jaundice": "yellow/jaundice",
                    "FP: history of stroke/hypertension/heart attack": "CVAhistory",
                    "FP: severe chest pain": "svchestpain",
                    "FP: Is the client a SMOKER?": "smoking",
                    #ObsHistory
                    "FP: Full Term": "NOPfullterm", 
                    "FP: Premature": "NOPpreterm", 
                    "FP: Abortion": "NOPabortion",
                    "FP: Date of Last Delivery": "dateOLdelivery",
                    "FP: Type of Last Delivery - Vagina": "typeOLdelivery_vaginal",
                    "FP: Type of Last Delivery - CSection": "typeOLdelivery_csection",
                    "FP: Previous Menstrual Period (PMP)": "pmp",
                    #PhyExamination
                    "FP: Weight": "PEweight",
                    "FP: Height": "PEheight",
                    "FP: Blood Pressure (S)": "bpS",
                    "FP: Blood Pressure (D)": "bpD",
                    "FP: C - Pale": "conjuPale",
                    "FP: C - Yellowish": "conjuYellowish",
                    "FP: N - Enlarged lymph nodes": "neckEnNodes",
                    "FP: B - Mass": "breastMass",
                    "FP: B - Nipple discharge": "breastNipD",   
                }

                mapped_result = {keys[label]: data[label] for label in keys if label in data}

                return mapped_result

            return None

        except Exception as e:
            print("Error autofilling from Maternal:", e)
            return None
