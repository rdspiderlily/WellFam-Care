class AutofillPersonalInfoController:
    def __init__(self, conn):
        self.conn = conn

    def get_basic_info(self, patient_id):
        query = """
            SELECT 
                PAT_LNAME, PAT_FNAME, LEFT(PAT_MNAME, 1) || '.' AS MIDDLE_INITIAL, 
                PAT_DOB, PAT_AGE, PAT_CNUM, PAT_OCCU, PAT_PHNUM, 
                PAT_LMP, PAT_EDC, PAT_AOG,
                PAT_ADDNS, PAT_ADDB, PAT_ADDMC, PAT_ADDP 
            FROM PATIENT
            WHERE PAT_ID = %s
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (patient_id,))
                result = cursor.fetchone()

            if result:
                keys = [
                    "lname", "fname", "minit", "dob", "age", "contact", "occupation", "philno",
                    "lmp", "edc", "aog", "add_ns", "add_b", "add_mc", "add_p"
                ]
                return dict(zip(keys, result))

            return None

        except Exception as e:
            print("Error fetching patient info:", e)
            return None

    def spouse_basic_info(self, patient_id):
        query = """
            SELECT 
                SP_LNAME, SP_FNAME, LEFT(SP_MNAME, 1) || '.' AS SMIDDLE_INITIAL, 
                SP_DOB, SP_AGE, SP_CNUM, SP_OCCU 
            FROM SPOUSE
            WHERE PAT_ID = %s
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (patient_id,))
                result = cursor.fetchone()

            if result:
                keys = [
                    "spo_lname", "spo_fname", "spo_minit", "spo_dob", 
                    "spo_age", "spo_contact", "spo_occupation"
                ]
                return dict(zip(keys, result))

            return None

        except Exception as e:
            print("Error fetching spouse info:", e)
            return None
        
    def famplan_availed(self, patient_id):
        query = """
            SELECT 
                ps.ps_dateavailed,
                st.serv_type_id,
                st.serv_type_name
            FROM PATIENT_SERVICE ps
            JOIN PATIENT_SERVICE_TYPE pst ON ps.ps_id = pst.ps_id
            JOIN SERVICE_TYPE st ON pst.serv_type_id = st.serv_type_id
            WHERE ps.pat_id = %s AND ps.serv_id = 2  -- 2 = Family Planning
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (patient_id,))
                rows = cursor.fetchall()

            if rows:
                date_availed = rows[0][0]
                subtypes = [row[2] for row in rows]  # serv_type_name
                return {
                    "date_availed": date_availed,
                    "subtypes": subtypes
                }

            return None

        except Exception as e:
            print("Error fetching family planning services:", e)
            return None

    def close(self):
        pass


        