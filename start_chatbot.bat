@echo off
echo 🏥 RagaAI Medical Scheduling Agent
echo ====================================
echo Starting the chatbot web interface...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the chatbot
python start_chatbot.py

pause

