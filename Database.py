import psycopg2
import bcrypt
from db_config import DB_SETTINGS
import socket
from datetime import datetime, timedelta
import csv
import os

def connect_db():
    try:
        return psycopg2.connect(**DB_SETTINGS)
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def check_user_credentials(username, password):
    conn = connect_db()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT STAFF_PASS FROM USER_STAFF WHERE STAFF_USN = %s", (username,))
        result = cursor.fetchone()

        if result:
            stored_password = result[0]
            return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
        return False
    except Exception as e:
        print(f"Login error: {e}")
        return False
    finally:
        conn.close()

def get_user_role(username):
    conn = connect_db()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.ROLE_NAME
            FROM USER_STAFF s
            JOIN USER_ROLE r ON s.ROLE_ID = r.ROLE_ID
            WHERE s.STAFF_USN = %s
        """, (username,))
        result = cursor.fetchone()
        
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting role: {e}")
        return None
    finally:
        conn.close()
        
def get_user_id(username):
    conn = connect_db()
    if not conn:
        return None
    
    try:
        username = str(username)
        
        cursor = conn.cursor()
        cursor.execute("SELECT STAFF_ID FROM USER_STAFF WHERE STAFF_USN = %s AND STAFF_ISDELETED = FALSE", (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting User ID: {e}")
        return None
    finally:
        conn.close()
        
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Error getting IP: {e}")
        return "127.0.0.1"  
        
def log_user_action(staff_id, action_type, ip_address=None):
    conn = connect_db()
    if not conn:
        return False
    
    if ip_address is None:
        ip_address = get_local_ip()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO USER_LOG (STAFF_ID, LOG_ACTNTYPE, LOG_IPADDRESS)
            VALUES (%s, %s, %s)
        """, (staff_id, action_type, ip_address))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error logging user action: {e}")
        return False
    finally:
        conn.close()
        
def check_login_attempts(username):
    conn = connect_db()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ATTEMPTS, LOCK_UNTIL 
            FROM USER_LOGIN_ATTEMPT 
            WHERE USERNAME = %s
        """, (username,))
        result = cursor.fetchone()
        
        if result:
            attempts, lock_until = result
            if attempts >= 5 and lock_until and datetime.now() < lock_until:
                remaining = (lock_until - datetime.now()).seconds // 60
                return f"Account locked. Try again in {remaining} minutes."
        return None
    except Exception as e:
        print(f"Error checking login attempts: {e}")
        return None
    finally:
        conn.close()

def record_failed_attempt(username):
    conn = connect_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO USER_LOGIN_ATTEMPT (USERNAME, ATTEMPTS, LAST_ATTEMPT)
            VALUES (%s, 1, NOW())
            ON CONFLICT (USERNAME) 
            DO UPDATE SET 
                ATTEMPTS = USER_LOGIN_ATTEMPT.ATTEMPTS + 1,
                LAST_ATTEMPT = NOW(),
                lock_until = CASE 
                    WHEN USER_LOGIN_ATTEMPT.ATTEMPTS + 1 >= 5 
                    THEN NOW() + INTERVAL '10 minutes' 
                    ELSE NULL 
                END
        """, (username,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error recording failed attempt: {e}")
        return False
    finally:
        conn.close()

def reset_attempts(username):
    conn = connect_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM USER_LOGIN_ATTEMPT 
            WHERE USERNAME = %s
        """, (username,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error resetting attempts: {e}")
        return False
    finally:
        conn.close()
        
def purge_old_logs(retention_days=90, archive_dir="logs", csv_retention_years=2):
    conn = connect_db()
    if not conn:
        return False, [], "Database connection failed"
    
    archived_files = []
    archived_audit_files = []
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    csv_cutoff_date = datetime.now() - timedelta(days=csv_retention_years * 365)
    
    try:
        os.makedirs(archive_dir, exist_ok=True)
        cursor = conn.cursor()

        # ===== 1. Process USER_LOG (login logs) =====
        cursor.execute("""
            SELECT
                LOG_ID, STAFF_ID, LOG_ACTNTYPE, 
                LOG_IPADDRESS, LOG_ACTNTIMESTMP
            FROM USER_LOG
            WHERE LOG_ACTNTIMESTMP < %s
            ORDER BY LOG_ACTNTIMESTMP
        """, (cutoff_date,))
        
        login_logs = cursor.fetchall()
        if login_logs:
            current_month = None
            current_file = None
            writer = None
            
            for log in login_logs:
                log_date = log[4]
                month_key = log_date.strftime("%Y%m")
                
                if month_key != current_month:
                    if writer:
                        current_file.close()
                    
                    filename = f"login_log_{log_date.strftime('%Y%m')}.csv"
                    filepath = os.path.join(archive_dir, filename)
                    current_file = open(filepath, 'a', newline='')
                    writer = csv.writer(current_file)
                    
                    if os.stat(filepath).st_size == 0:
                        writer.writerow([desc[0] for desc in cursor.description])
                    
                    current_month = month_key
                    archived_files.append(filepath)
                
                writer.writerow(log)
        
        # ===== 2. Process AUDIT_LOG =====
        cursor.execute("""
            SELECT
                AUDT_ID, STAFF_ID, AUDT_ACTIONTYPE,
                AUDT_TABLE, AUDT_RECORDID, LOG_ACTNTIMESTMP
            FROM AUDIT_LOG
            WHERE LOG_ACTNTIMESTMP < %s
            ORDER BY LOG_ACTNTIMESTMP
        """, (cutoff_date,))
        
        audit_logs = cursor.fetchall()
        if audit_logs:
            current_month = None
            current_file = None
            writer = None
            
            for log in audit_logs:
                log_date = log[5]
                month_key = log_date.strftime("%Y%m")
                
                if month_key != current_month:
                    if writer:
                        current_file.close()
                    
                    filename = f"audit_log_{log_date.strftime('%Y%m')}.csv"
                    filepath = os.path.join(archive_dir, filename)
                    current_file = open(filepath, 'a', newline='')
                    writer = csv.writer(current_file)
                    
                    if os.stat(filepath).st_size == 0:
                        writer.writerow([desc[0] for desc in cursor.description])
                    
                    current_month = month_key
                    archived_audit_files.append(filepath)
                
                writer.writerow(log) 
        
        # ===== 3. Delete old records from both tables =====
        cursor.execute("""
            DELETE FROM USER_LOG 
            WHERE LOG_ACTNTIMESTMP < %s
        """, (cutoff_date,))
        conn.commit()
        
        cursor.execute("""
            DELETE FROM AUDIT_LOG 
            WHERE LOG_ACTNTIMESTMP < %s
        """, (cutoff_date,))
        
        # ===== 4. Clean up old CSV files =====
        deleted_files = []
        for filename in os.listdir(archive_dir):
            if (filename.startswith("login_log_") or filename.startswith("audit_log_")) and filename.endswith(".csv"):
                filepath = os.path.join(archive_dir, filename)
                try:
                    date_str = filename.split('_')[2].split('.')[0]
                    file_date = datetime.strptime(date_str, "%Y%m")
                    if file_date < csv_cutoff_date:
                        os.remove(filepath)
                        deleted_files.append(filepath)
                        print(f"Deleted old CSV: {filename}")
                except (ValueError, IndexError):
                    continue
        
        return True, archived_files, deleted_files, None
    except Exception as e:
        conn.rollback()
        error_msg = f"Log purge failed {str(e)}"
        print(error_msg)
        return False, archived_files, error_msg
    finally:
        if conn:
            conn.close()
        if 'current_file' in locals() and current_file:
            current_file.close()
            
def log_audit(user_id, action, table_name, record_id):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO AUDIT_LOG (STAFF_ID, AUDT_ACTIONTYPE, AUDT_TABLE, AUDT_RECORDID)
            VALUES (%s, %s, %s, %s)
        """, (user_id, action, table_name, record_id))
        conn.commit()
    except Exception as e:
        print(f"Failed to log audit: {e}")
    finally:
        cursor.close()