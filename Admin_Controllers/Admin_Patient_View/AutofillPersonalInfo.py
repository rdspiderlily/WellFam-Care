class AutofillPersonalInfoController:
    def __init__(self, conn):
        self.conn = conn

    def get_basic_info(self, patient_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    PAT_LNAME, PAT_FNAME, LEFT(PAT_MNAME, 1) || '.' AS MIDDLE_INITIAL, 
                    PAT_DOB, PAT_AGE, PAT_CNUM, PAT_OCCU, PAT_PHNUM, 
                    PAT_LMP, PAT_EDC, PAT_AOG,
                    PAT_ADDNS, PAT_ADDB, PAT_ADDMC, PAT_ADDP 
                FROM PATIENT
                WHERE PAT_ID = %s
            """, (patient_id,))
            result = cursor.fetchone()
            cursor.close()

            if result:
                return {
                    "lname": result[0],
                    "fname": result[1],
                    "minit": result[2],
                    "dob": result[3],
                    "age": result[4],
                    "contact": result[5],
                    "occupation": result[6],
                    "philno": result[7],
                    "lmp": result[8],
                    "edc": result[9],
                    "aog": result[10],
                    "add_ns": result[11],
                    "add_b": result[12],
                    "add_mc": result[13],
                    "add_p": result[14]
                }
            return None

        except Exception as e:
            print("Error fetching basic info:", e)
            return None
        
    def close(self):
        pass

        