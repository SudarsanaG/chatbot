"""
Configuration file for RagaAI Medical Scheduling Agent
"""

import os
from typing import Dict, Any

class Config:
    """Application configuration"""
    
    # Email Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "noreply@ragaai-medical.com")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")
    
    # SMS Configuration (Twilio)
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your-account-sid")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your-auth-token")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "+1234567890")
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
    
    # Application Configuration
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Data Configuration
    DATA_DIR = "data"
    EXPORTS_DIR = "exports"
    BACKUPS_DIR = "backups"
    FORMS_DIR = "forms"
    
    # Appointment Configuration
    NEW_PATIENT_DURATION = 60  # minutes
    RETURNING_PATIENT_DURATION = 30  # minutes
    
    # Reminder Configuration
    REMINDER_1_DAYS_BEFORE = 3
    REMINDER_2_DAYS_BEFORE = 1
    REMINDER_3_HOURS_BEFORE = 2
    
    # Business Hours
    BUSINESS_START_HOUR = 9
    BUSINESS_END_HOUR = 17
    BUSINESS_DAYS = [0, 1, 2, 3, 4]  # Monday to Friday
    
    @classmethod
    def get_email_config(cls) -> Dict[str, Any]:
        """Get email configuration"""
        return {
            "smtp_server": cls.SMTP_SERVER,
            "smtp_port": cls.SMTP_PORT,
            "email": cls.EMAIL_ADDRESS,
            "password": cls.EMAIL_PASSWORD,
            "from_name": "RagaAI Medical Scheduling"
        }
    
    @classmethod
    def get_sms_config(cls) -> Dict[str, Any]:
        """Get SMS configuration"""
        return {
            "account_sid": cls.TWILIO_ACCOUNT_SID,
            "auth_token": cls.TWILIO_AUTH_TOKEN,
            "from_number": cls.TWILIO_FROM_NUMBER
        }
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [cls.DATA_DIR, cls.EXPORTS_DIR, cls.BACKUPS_DIR, cls.FORMS_DIR]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

