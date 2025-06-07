from dotenv import load_dotenv
import os
import socket

load_dotenv()  

def resolve_host():
    """Smart resolver that works across networks"""
    hostname = os.getenv("DB_HOST")
    
    # If host is explicitly set to 'auto', use smart detection
    if hostname == "auto":
        try:
            # 1. Try getting local IP first
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                return local_ip
        except:
            # 2. Fallback to localhost
            return "127.0.0.1"
    else:
        # For explicit hostnames/IPs
        try:
            info = socket.getaddrinfo(hostname, None, socket.AF_INET)
            return info[0][4][0]
        except (socket.gaierror, IndexError):
            return "127.0.0.1"

DB_SETTINGS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": resolve_host(),
    "port": os.getenv("DB_PORT")
}
