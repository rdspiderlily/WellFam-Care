import PyInstaller.__main__
import os

PyInstaller.__main__.run([
    "Login.py",  
    "--onefile",
    "--distpath=dist/host",
    "--name=WellFam-Care-Host",  
    "--icon=favicon.ico",
    "--add-data=.env;.",  # Include host config
    "--add-data=wfui/login.ui;wfui",  # Include UI file
    "--add-data=wfpics/logo1.jpg;wfpics",  # Include logo
    "--version-file=version_info.txt",
    "--windowed",
    "--hidden-import=PyQt5.sip"  # Sometimes needed for PyQt5
])                                                                        