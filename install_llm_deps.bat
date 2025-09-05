@echo off
echo Installing LLM dependencies for RagaAI Medical Scheduling Agent...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install LangChain dependencies
echo Installing LangChain and OpenAI dependencies...
pip install langchain==0.1.20
pip install langchain-openai==0.1.8
pip install langchain-community==0.0.38
pip install langgraph==0.0.69
pip install openai==1.12.0

echo.
echo Installation complete!
echo.
echo To use LLM features:
echo 1. Set your OpenAI API key: set OPENAI_API_KEY=your-key-here
echo 2. Run the application: python chatbot_ui.py
echo.
pause
