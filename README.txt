-- WellFam Care - File, Appointment and Patient Record Management System --

A local desktop-based clinic management application built with **Python**, **PyQt5**, and **PostgreSQL**.  
Supports login system, patient records, appointments, document uploads and service tracking.

#

# Requirements
- Python 3.12.5
- PostgreSQL 17.2
- pip packages:
    - `psycopg2`
    - `bcrypt`
    - `PyQt5`
    - `PyPDF2`
    - `PyQtChart`
You can install the required packages via: pip install -r requirements.txt

#

# Setup Instructions
1. Create a `.env` file with your database credentials:
    ```
    DB_NAME=clinic_testing  
    DB_USER=postgres  
    DB_PASSWORD=your_password  
    DB_HOST=192.168.x.x  # To know your IP: run `ipconfig` in Command Prompt
    DB_PORT=5432
    ```
2. Install dependencies:
    ```
    pip install -r requirements.txt
    ```
3. Setup your PostgreSQL database and restore a backup if needed.
4. Run the application:
    ```
    python login.py
    ```

#

The system is designed for offline local network use (e.g., with switches).
