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
                'Smoking'
            )
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (patient_id,))
                result = cursor.fetchall()  # Fetch all matching rows

            if result:
                data = {label: value for label, value in result}  # Create a dictionary of labels to values

                # Map the labels to the required keys
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
                    "Smoking": "smoking"
                    #ObsHistory
                    
                }

                # Prepare the final result by mapping labels to keys
                mapped_result = {keys[label]: data[label] for label in keys if label in data}

                return mapped_result

            return None

        except Exception as e:
            print("Error autofilling from Maternal:", e)
            return None
