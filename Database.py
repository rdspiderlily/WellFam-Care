import psycopg2
import bcrypt

def connect_db():
    try:
        return psycopg2.connect(
            dbname="clinic_testing",
            user="postgres",             
            password="btsjk17!",     
            host="192.168.1.2",          
            port="5432"
        )
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