@echo off

call ./venv/Scripts/activate
set PYTHONIOENCODING=utf-8
rem Run the server (DEFAULT_MODEL is loaded from .env file)
python .\src\coding_server.py
pause