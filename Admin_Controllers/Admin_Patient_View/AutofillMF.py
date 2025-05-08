# from Database import connect_db

# class AutofillPersonalInfoController:
#     def __init__(self):
#         self.conn = connect_db()
    
#     def autofill_from_maternal(self, pat_id):
#         query = """
#             SELECT fo.FORM_OPT_LABEL, fr.FORM_RES_VAL
#             FROM FORM_RESPONSE fr
#             JOIN FORM_OPTION fo ON fr.FORM_OPT_ID = fo.FORM_OPT_ID
#             JOIN FORM_CATEGORY fc ON fo.FORM_CAT_ID = fc.FORM_CAT_ID
#             JOIN FORM_PAGE fp ON fc.FORM_PAGE_ID = fp.FORM_PAGE_ID
#             JOIN FORM f ON fp.FORM_ID = f.FORM_ID
#             WHERE fr.PAT_ID = %s
#             AND f.FORM_NAME = 'Maternal'
#             AND fo.FORM_OPT_LABEL IN (
#                 'Client No.',
#                 'Educational Attainment',
#                 'No. of Living Kids',
#                 'Plan to have more children?'
#             )
#         """

#         try:
#             self.cursor.execute(query, (pat_id,))
#             results = self.cursor.fetchall()

#             for label, value in results:
#                 if label == "Client No.":
#                     self.clt_no.setText(value)
#                 elif label == "Educational Attainment":
#                     index = self.clt_educA.findText(value)
#                     if index != -1:
#                         self.clt_educA.setCurrentIndex(index)
#                 elif label == "No. of Living Kids":
#                     self.clt_noLivKids.setText(value)
#                 elif label == "Plan to have more children?":
#                     if value.strip().lower() == "yes":
#                         self.clt_pMoreKidY.setChecked(True)
#                         self.clt_pMoreKidN.setChecked(False)
#                     elif value.strip().lower() == "no":
#                         self.clt_pMoreKidN.setChecked(True)
#                         self.clt_pMoreKidY.setChecked(False)

#         except Exception as e:
#             print("Error autofilling from Maternal:", e)



#     def get_family_planning_info(self, patient_id):
#         try:
#             query = '''
#                 SELECT client_number, education, num_living_children, plan_more_children
#                 FROM FAM_PLAN_RECORD
#                 WHERE patient_id = ?
#                 ORDER BY date_created DESC LIMIT 1
#             '''
#             self.db.execute(query, (patient_id,))
#             row = self.db.fetchone()
#             if row:
#                 return {
#                     "client_number": row[0],
#                     "education": row[1],
#                     "num_living_children": row[2],
#                     "plan_more_children": row[3],  # Could be 'Y', 'N', or None
#                 }
#         except Exception as e:
#             print("Error getting family planning info:", e)
#         return {}

