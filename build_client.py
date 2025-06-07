import PyInstaller.__main__
import shutil
import os

shutil.copyfile("config/client.env", ".env")

PyInstaller.__main__.run([
    "Login.py",  
    "--onefile",
    "--distpath=dist/client",
    "--name=WellFam-Care",  
    "--icon=favicon.ico",
    "--add-data=config/client.env;.",  # Include client config
    "--version-file=version_info.txt",
    "--windowed"  
])

# Clean up
os.remove(".env")