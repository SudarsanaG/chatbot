"""
Reminder System for Medical Scheduling Agent
Handles automated reminders via email and SMS
"""

import smtplib
import schedule
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
import datetime
from typing import List, Dict, Optional
import os
from twilio.rest import Client
import json

class ReminderSystem:
    """Automated reminder system for medical appointments"""
    
    def __init__(self):
        self.email_config = self._load_email_config()
        self.sms_config = self._load_sms_config()
        self.reminders_sent = set()  # Track sent reminders to avoid duplicates
        
    def _load_email_config(self) -> Dict:
        """Load email configuration from environment or config file"""
        return {
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "email": os.getenv("EMAIL_ADDRESS", "your-email@example.com"),
            "password": os.getenv("EMAIL_PASSWORD", "your-app-password"),
            "from_name": "RagaAI Medical Scheduling"
        }
    
    def _load_sms_config(self) -> Dict:
        """Load SMS configuration from environment or config file"""
        return {
            "account_sid": os.getenv("TWILIO_ACCOUNT_SID", "your-account-sid"),
            "auth_token": os.getenv("TWILIO_AUTH_TOKEN", "your-auth-token"),
            "from_number": os.getenv("TWILIO_FROM_NUMBER", "+1234567890")
        }
    
    def send_email_reminder(self, patient_email: str, patient_name: str, 
                          appointment_details: Dict, reminder_type: str) -> bool:
        """Send email reminder to patient"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.email_config['from_name']} <{self.email_config['email']}>"
            msg['To'] = patient_email
            msg['Subject'] = self._get_email_subject(reminder_type, appointment_details)
            
            # Create email body
            body = self._create_email_body(patient_name, appointment_details, reminder_type)
            msg.attach(MIMEText(body, 'html'))
            
            # Attach intake form if it's the first reminder
            if reminder_type == "first":
                self._attach_intake_form(msg)
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            text = msg.as_string()
            server.sendmail(self.email_config['email'], patient_email, text)
            server.quit()
            
            print(f"✅ Email reminder sent to {patient_name} ({patient_email})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {patient_email}: {str(e)}")
            return False
    
    def send_sms_reminder(self, patient_phone: str, patient_name: str, 
                         appointment_details: Dict, reminder_type: str) -> bool:
        """Send SMS reminder to patient"""
        try:
            # Initialize Twilio client
            client = Client(self.sms_config['account_sid'], self.sms_config['auth_token'])
            
            # Create SMS message
            message_body = self._create_sms_body(patient_name, appointment_details, reminder_type)
            
            # Send SMS
            message = client.messages.create(
                body=message_body,
                from_=self.sms_config['from_number'],
                to=patient_phone
            )
            
            print(f"✅ SMS reminder sent to {patient_name} ({patient_phone})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send SMS to {patient_phone}: {str(e)}")
            return False
    
    def _get_email_subject(self, reminder_type: str, appointment_details: Dict) -> str:
        """Get email subject based on reminder type"""
        doctor = appointment_details.get('doctor', 'Dr. Smith')
        date = appointment_details.get('date', 'TBD')
        
        if reminder_type == "first":
            return f"Appointment Reminder - {date} with {doctor}"
        elif reminder_type == "second":
            return f"Intake Form Reminder - {date} with {doctor}"
        elif reminder_type == "third":
            return f"Confirmation Request - {date} with {doctor}"
        else:
            return f"Appointment Update - {date} with {doctor}"
    
    def _create_email_body(self, patient_name: str, appointment_details: Dict, 
                          reminder_type: str) -> str:
        """Create HTML email body"""
        doctor = appointment_details.get('doctor', 'Dr. Smith')
        date = appointment_details.get('date', 'TBD')
        time = appointment_details.get('time', 'TBD')
        duration = appointment_details.get('duration', 30)
        
        if reminder_type == "first":
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5aa0;">Appointment Reminder</h2>
                    <p>Dear {patient_name},</p>
                    <p>This is a friendly reminder about your upcoming appointment:</p>
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Doctor:</strong> {doctor}</p>
                        <p><strong>Date:</strong> {date}</p>
                        <p><strong>Time:</strong> {time}</p>
                        <p><strong>Duration:</strong> {duration} minutes</p>
                    </div>
                    <p>Please arrive 15 minutes early for check-in. If you need to reschedule, please contact us at least 24 hours in advance.</p>
                    <p>Best regards,<br>RagaAI Medical Scheduling Team</p>
                </div>
            </body>
            </html>
            """
        
        elif reminder_type == "second":
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5aa0;">Intake Form Reminder</h2>
                    <p>Dear {patient_name},</p>
                    <p>Your appointment with {doctor} is scheduled for {date} at {time}.</p>
                    <p><strong>Please confirm:</strong> Have you completed and submitted your intake form?</p>
                    <p>If you haven't filled out the form yet, please do so as soon as possible. This helps us prepare for your visit and reduces wait times.</p>
                    <p>If you need the form resent, please reply to this email or call our office.</p>
                    <p>Best regards,<br>RagaAI Medical Scheduling Team</p>
                </div>
            </body>
            </html>
            """
        
        elif reminder_type == "third":
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5aa0;">Appointment Confirmation Request</h2>
                    <p>Dear {patient_name},</p>
                    <p>Your appointment with {doctor} is scheduled for {date} at {time}.</p>
                    <p><strong>Please confirm:</strong> Will you be attending this appointment?</p>
                    <p>If you need to cancel or reschedule, please reply to this email with your reason for cancellation. We understand that circumstances change and we're here to help.</p>
                    <p>If you don't respond, we'll assume you're still planning to attend.</p>
                    <p>Best regards,<br>RagaAI Medical Scheduling Team</p>
                </div>
            </body>
            </html>
            """
        
        return body
    
    def _create_sms_body(self, patient_name: str, appointment_details: Dict, 
                        reminder_type: str) -> str:
        """Create SMS message body"""
        doctor = appointment_details.get('doctor', 'Dr. Smith')
        date = appointment_details.get('date', 'TBD')
        time = appointment_details.get('time', 'TBD')
        
        if reminder_type == "first":
            return f"Hi {patient_name}! Reminder: You have an appointment with {doctor} on {date} at {time}. Please arrive 15 min early. Reply STOP to opt out."
        
        elif reminder_type == "second":
            return f"Hi {patient_name}! Quick check: Have you filled out your intake form for your {date} appointment with {doctor}? Reply YES/NO."
        
        elif reminder_type == "third":
            return f"Hi {patient_name}! Final confirmation needed: Will you attend your {date} appointment with {doctor}? Reply YES/NO or CANCEL with reason."
        
        return f"Hi {patient_name}! Update about your {date} appointment with {doctor}."
    
    def _attach_intake_form(self, msg: MIMEMultipart):
        """Attach intake form PDF to email"""
        try:
            form_path = "forms/New Patient Intake Form.pdf"
            if os.path.exists(form_path):
                with open(form_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(form_path)}'
                )
                msg.attach(part)
        except Exception as e:
            print(f"Warning: Could not attach intake form: {str(e)}")
    
    def schedule_reminders(self, appointment_details: Dict):
        """Schedule all three reminders for an appointment"""
        patient_name = appointment_details.get('patient_name', 'Patient')
        patient_email = appointment_details.get('patient_email', '')
        patient_phone = appointment_details.get('patient_phone', '')
        appointment_date = datetime.datetime.strptime(appointment_details['date'], '%Y-%m-%d').date()
        
        # Calculate reminder dates
        reminder_1_date = appointment_date - datetime.timedelta(days=3)  # 3 days before
        reminder_2_date = appointment_date - datetime.timedelta(days=1)  # 1 day before
        reminder_3_date = appointment_date - datetime.timedelta(hours=2)  # 2 hours before
        
        # Schedule reminders
        self._schedule_reminder(reminder_1_date, "first", patient_name, patient_email, 
                               patient_phone, appointment_details)
        self._schedule_reminder(reminder_2_date, "second", patient_name, patient_email, 
                               patient_phone, appointment_details)
        self._schedule_reminder(reminder_3_date, "third", patient_name, patient_email, 
                               patient_phone, appointment_details)
        
        print(f"📅 Scheduled 3 reminders for {patient_name}'s appointment on {appointment_date}")
    
    def _schedule_reminder(self, reminder_date: datetime.date, reminder_type: str,
                          patient_name: str, patient_email: str, patient_phone: str,
                          appointment_details: Dict):
        """Schedule a single reminder"""
        reminder_id = f"{appointment_details.get('patient_id', 'unknown')}_{reminder_type}_{reminder_date}"
        
        if reminder_id in self.reminders_sent:
            return  # Already scheduled
        
        # Schedule the reminder
        schedule.every().day.at("09:00").do(
            self._send_scheduled_reminder,
            reminder_id, reminder_type, patient_name, patient_email, 
            patient_phone, appointment_details
        ).tag(reminder_id)
        
        self.reminders_sent.add(reminder_id)
    
    def _send_scheduled_reminder(self, reminder_id: str, reminder_type: str,
                               patient_name: str, patient_email: str, patient_phone: str,
                               appointment_details: Dict):
        """Send a scheduled reminder"""
        try:
            # Send email reminder
            if patient_email:
                self.send_email_reminder(patient_email, patient_name, appointment_details, reminder_type)
            
            # Send SMS reminder
            if patient_phone:
                self.send_sms_reminder(patient_phone, patient_name, appointment_details, reminder_type)
            
            # Remove from schedule after sending
            schedule.clear(reminder_id)
            print(f"✅ Sent {reminder_type} reminder to {patient_name}")
            
        except Exception as e:
            print(f"❌ Failed to send {reminder_type} reminder to {patient_name}: {str(e)}")
    
    def start_reminder_service(self):
        """Start the reminder service in a separate thread"""
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        reminder_thread = threading.Thread(target=run_scheduler, daemon=True)
        reminder_thread.start()
        print("🔄 Reminder service started")
    
    def send_immediate_reminder(self, appointment_details: Dict, reminder_type: str = "first"):
        """Send an immediate reminder (for testing)"""
        patient_name = appointment_details.get('patient_name', 'Patient')
        patient_email = appointment_details.get('patient_email', '')
        patient_phone = appointment_details.get('patient_phone', '')
        
        if patient_email:
            self.send_email_reminder(patient_email, patient_name, appointment_details, reminder_type)
        
        if patient_phone:
            self.send_sms_reminder(patient_phone, patient_name, appointment_details, reminder_type)

# Global reminder system instance
reminder_system = ReminderSystem()

