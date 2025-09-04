import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import pandas as pd
import datetime
from typing import Dict, List, Optional

def send_intake_form(email: str, pdf_path: str = "forms/New Patient Intake Form.pdf") -> str:
    """
    Send intake form to patient via email
    
    Args:
        email: Patient's email address
        pdf_path: Path to the intake form PDF
    
    Returns:
        Status message
    """
    if not os.path.exists(pdf_path):
        return "❌ Intake form not found."

    # --- Simulation Mode (Default) ---
    return f"✅ Intake form sent to {email} (simulated - check forms folder)"

    # --- Real Mode (uncomment below if you want to send real emails) ---
    """
    try:
        msg = MIMEMultipart()
        msg['Subject'] = "Your Appointment Intake Form - RagaAI Medical"
        msg['From'] = "noreply@ragaai-medical.com"
        msg['To'] = email
        
        # Email body
        body = """
        Dear Patient,
        
        Thank you for scheduling your appointment with us. Please find attached your intake form.
        
        Please complete and return this form before your appointment to help us prepare for your visit.
        
        If you have any questions, please don't hesitate to contact us.
        
        Best regards,
        RagaAI Medical Scheduling Team
        """
        
        msg.attach(MIMEText(body, 'plain'))

        # Attach PDF
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {os.path.basename(pdf_path)}'
        )
        msg.attach(part)

        # Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("your-email@example.com", "your-app-password")
            smtp.send_message(msg)

        return f"✅ Intake form emailed to {email}"
        
    except Exception as e:
        return f"❌ Failed to send intake form: {str(e)}"
    """

def validate_patient_data(patient_data: Dict) -> Dict[str, str]:
    """
    Validate patient data for completeness and format
    
    Args:
        patient_data: Dictionary containing patient information
    
    Returns:
        Dictionary with validation results
    """
    errors = {}
    
    # Validate required fields
    required_fields = ['first_name', 'dob', 'email', 'phone']
    for field in required_fields:
        if not patient_data.get(field):
            errors[field] = f"{field.replace('_', ' ').title()} is required"
    
    # Validate email format
    if patient_data.get('email'):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, patient_data['email']):
            errors['email'] = "Invalid email format"
    
    # Validate phone format
    if patient_data.get('phone'):
        phone_pattern = r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'
        if not re.match(phone_pattern, patient_data['phone']):
            errors['phone'] = "Invalid phone number format"
    
    # Validate DOB format
    if patient_data.get('dob'):
        try:
            datetime.datetime.strptime(patient_data['dob'], '%Y-%m-%d')
        except ValueError:
            try:
                datetime.datetime.strptime(patient_data['dob'], '%m/%d/%Y')
            except ValueError:
                errors['dob'] = "Invalid date format. Use YYYY-MM-DD or MM/DD/YYYY"
    
    return errors

def format_phone_number(phone: str) -> str:
    """
    Format phone number to standard format
    
    Args:
        phone: Raw phone number string
    
    Returns:
        Formatted phone number
    """
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Format as (XXX) XXX-XXXX
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return original if can't format

def format_date(date_str: str, input_format: str = '%Y-%m-%d', output_format: str = '%B %d, %Y') -> str:
    """
    Format date string to readable format
    
    Args:
        date_str: Date string
        input_format: Input date format
        output_format: Output date format
    
    Returns:
        Formatted date string
    """
    try:
        date_obj = datetime.datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except ValueError:
        return date_str

def calculate_age(dob: str) -> int:
    """
    Calculate age from date of birth
    
    Args:
        dob: Date of birth string
    
    Returns:
        Age in years
    """
    try:
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                birth_date = datetime.datetime.strptime(dob, fmt).date()
                today = datetime.date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                return age
            except ValueError:
                continue
        return 0
    except:
        return 0

def generate_appointment_id() -> str:
    """
    Generate unique appointment ID
    
    Returns:
        Unique appointment ID string
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(datetime.datetime.now().microsecond)[:3]
    return f"APT{timestamp}{random_suffix}"

def backup_data():
    """
    Create backup of all data files
    
    Returns:
        Status message
    """
    try:
        backup_dir = f"backups/backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup CSV files
        if os.path.exists("data/patients.csv"):
            import shutil
            shutil.copy2("data/patients.csv", f"{backup_dir}/patients.csv")
        
        # Backup Excel files
        if os.path.exists("data/schedules.xlsx"):
            shutil.copy2("data/schedules.xlsx", f"{backup_dir}/schedules.xlsx")
        
        if os.path.exists("data/appointments.xlsx"):
            shutil.copy2("data/appointments.xlsx", f"{backup_dir}/appointments.xlsx")
        
        return f"✅ Data backed up to {backup_dir}"
        
    except Exception as e:
        return f"❌ Backup failed: {str(e)}"

def get_system_stats() -> Dict:
    """
    Get system statistics
    
    Returns:
        Dictionary with system statistics
    """
    stats = {
        'patients': 0,
        'appointments': 0,
        'doctors': 0,
        'available_slots': 0
    }
    
    try:
        # Count patients
        if os.path.exists("data/patients.csv"):
            patients_df = pd.read_csv("data/patients.csv")
            stats['patients'] = len(patients_df)
        
        # Count appointments
        if os.path.exists("data/appointments.xlsx"):
            appointments_df = pd.read_excel("data/appointments.xlsx")
            stats['appointments'] = len(appointments_df)
        
        # Count doctors and available slots
        if os.path.exists("data/schedules.xlsx"):
            schedules_df = pd.read_excel("data/schedules.xlsx")
            stats['doctors'] = len(schedules_df['Doctor'].unique())
            stats['available_slots'] = len(schedules_df[schedules_df['Available'] == 'Yes'])
        
    except Exception as e:
        print(f"Error getting system stats: {str(e)}")
    
    return stats

def clean_old_data(days_to_keep: int = 30):
    """
    Clean old appointment data
    
    Args:
        days_to_keep: Number of days of data to keep
    """
    try:
        if not os.path.exists("data/appointments.xlsx"):
            return "No appointments data to clean"
        
        appointments_df = pd.read_excel("data/appointments.xlsx")
        
        # Convert date column to datetime
        appointments_df['Date'] = pd.to_datetime(appointments_df['Date'])
        
        # Keep only recent appointments
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
        recent_appointments = appointments_df[appointments_df['Date'] >= cutoff_date]
        
        # Save cleaned data
        recent_appointments.to_excel("data/appointments.xlsx", index=False)
        
        removed_count = len(appointments_df) - len(recent_appointments)
        return f"✅ Cleaned {removed_count} old appointments"
        
    except Exception as e:
        return f"❌ Data cleaning failed: {str(e)}"
