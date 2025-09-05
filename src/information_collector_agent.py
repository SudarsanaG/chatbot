"""
Information Collection Agent
Specializes in collecting and validating patient information
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from src.gemini_client import GeminiClient
from src.agent import PatientInfo
import re
from email_validator import validate_email, EmailNotValidError
import phonenumbers

@dataclass
class CollectionResult:
    """Result of information collection"""
    success: bool
    message: str
    patient_info: PatientInfo
    next_state: str
    missing_fields: List[str]

class InformationCollectorAgent:
    """Agent responsible for collecting patient information"""
    
    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client
        self.required_fields = ["first_name", "last_name", "date_of_birth", "phone", "email"]
        self.field_display_names = {
            "first_name": "first name",
            "last_name": "last name", 
            "date_of_birth": "date of birth",
            "phone": "phone number",
            "email": "email address"
        }
    
    def process_greeting(self, user_input: str, conversation_history: List[Dict]) -> CollectionResult:
        """Handle initial greeting and start information collection"""
        
        # Extract any name information from greeting
        entities = self.gemini.extract_entities(user_input)
        
        patient_info = PatientInfo()
        if entities.get("first_name"):
            patient_info.first_name = entities["first_name"]
        
        if entities.get("last_name"):
            patient_info.last_name = entities["last_name"]
        
        # Generate appropriate response
        context = "Initial greeting - starting information collection process"
        response = self.gemini.generate_response(user_input, context, "information_collector")
        
        # Determine next state
        if patient_info.first_name and patient_info.last_name:
            next_state = "patient_lookup"
            message = f"Hello {patient_info.first_name}! I found your name. Let me verify your information in our system."
        elif patient_info.first_name:
            next_state = "collecting_info"
            message = f"Nice to meet you, {patient_info.first_name}! What's your last name?"
        else:
            next_state = "collecting_info"
            message = response if response else "Hello! I'm your AI medical scheduling assistant. What's your first name?"
        
        return CollectionResult(
            success=True,
            message=message,
            patient_info=patient_info,
            next_state=next_state,
            missing_fields=self._get_missing_fields(patient_info)
        )
    
    def collect_information(self, user_input: str, current_patient: PatientInfo, conversation_history: List[Dict]) -> CollectionResult:
        """Collect and validate patient information"""
        
        # Extract entities from user input with conversation context
        context_text = " ".join([msg.get("content", "") for msg in conversation_history[-5:]])
        entities = self.gemini.extract_entities(user_input, context_text)
        
        # Update patient info with extracted entities
        updated_patient = self._update_patient_info(current_patient, entities)
        
        # Handle confirmation responses
        updated_patient = self._handle_confirmation_response(user_input, updated_patient)
        
        # Validate the information
        validation_result = self._validate_patient_info(updated_patient)
        
        # Get missing fields from validation result
        missing_fields = validation_result["missing_fields"]
        validation_errors = validation_result["validation_errors"]
        
        # Validation completed
        
        if validation_result["valid"]:
            # All required information collected
            next_state = "patient_lookup" if updated_patient.patient_type == "Returning" else "new_patient_registration"
            
            # Customize message based on patient type
            if updated_patient.patient_type == "Returning":
                message = f"Perfect! I have all your information, {updated_patient.first_name}. I see you're a returning patient, so we'll book a 30-minute appointment for you. Let me proceed with your appointment scheduling."
            else:
                message = f"Perfect! I have all your information, {updated_patient.first_name}. As a new patient, we'll book a 60-minute appointment for you. Let me proceed with your appointment scheduling."
        else:
            # Still need more information
            next_state = "collecting_info"
            
            # Generate contextual response for missing information
            context = f"Collecting patient information. Current patient: {updated_patient.first_name}. Missing: {', '.join(missing_fields)}"
            message = self.gemini.generate_response(user_input, context, "information_collector")
            
            # If no good response from LLM, provide fallback
            if not message or len(message) < 10:
                message = self._generate_missing_info_message(missing_fields, updated_patient.first_name)
        
        return CollectionResult(
            success=validation_result["valid"],
            message=message,
            patient_info=updated_patient,
            next_state=next_state,
            missing_fields=missing_fields
        )
    
    def _update_patient_info(self, current_patient: PatientInfo, entities: Dict[str, Any]) -> PatientInfo:
        """Update patient info with extracted entities"""
        
        # Create a copy of current patient info
        updated_patient = PatientInfo(
            first_name=current_patient.first_name,
            last_name=current_patient.last_name,
            dob=current_patient.dob,
            phone=current_patient.phone,
            email=current_patient.email,
            patient_type=current_patient.patient_type,
            patient_id=current_patient.patient_id
        )
        
        # Update with new entities
        if entities.get("first_name"):
            updated_patient.first_name = entities["first_name"]
        
        if entities.get("last_name"):
            updated_patient.last_name = entities["last_name"]
        
        if entities.get("date_of_birth"):
            # Normalize the date format
            updated_patient.dob = self._normalize_date_format(entities["date_of_birth"])
        
        if entities.get("phone"):
            updated_patient.phone = entities["phone"]
        
        if entities.get("email"):
            updated_patient.email = entities["email"]
        
        if entities.get("patient_type"):
            updated_patient.patient_type = entities["patient_type"]
        
        return updated_patient
    
    def _handle_confirmation_response(self, user_input: str, current_patient: PatientInfo) -> PatientInfo:
        """Handle confirmation responses like 'Yes', 'Correct', etc."""
        
        user_input_lower = user_input.lower().strip()
        
        # Check if this is a confirmation response
        confirmation_words = ["yes", "yeah", "yep", "correct", "right", "that's right", "that is correct", "confirm"]
        
        if any(word in user_input_lower for word in confirmation_words):
            # If user is confirming, we should keep the current patient info as is
            # This prevents the system from asking for the same information again
            return current_patient
        
        return current_patient
    
    def _normalize_date_format(self, date_str: str) -> str:
        """Normalize date format to MM/DD/YYYY"""
        try:
            import datetime
            import re
            
            # Clean the date string
            original_date = date_str.strip()
            date_str = original_date
            
            # Try to parse various formats
            formats = [
                '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%m/%d/%y',
                '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d',
                '%B %d, %Y', '%b %d, %Y',  # July 9, 1999
                '%d %B %Y', '%d %b %Y',    # 9 July 1999
                '%B %d %Y', '%b %d %Y',    # July 9 1999
            ]
            
            for fmt in formats:
                try:
                    parsed_date = datetime.datetime.strptime(date_str, fmt)
                    normalized = parsed_date.strftime('%m/%d/%Y')
                    return normalized
                except ValueError:
                    continue
            
            # Try to parse natural language dates like "9th July 1999"
            if re.search(r'\d{1,2}(st|nd|rd|th)?\s+\w+\s+\d{4}', date_str):
                # Remove ordinal suffixes (st, nd, rd, th)
                cleaned = re.sub(r'(\d{1,2})(st|nd|rd|th)', r'\1', date_str)
                for fmt in ['%d %B %Y', '%d %b %Y']:
                    try:
                        parsed_date = datetime.datetime.strptime(cleaned, fmt)
                        normalized = parsed_date.strftime('%m/%d/%Y')
                        return normalized
                    except ValueError:
                        continue
            
            # If all else fails, return the original string
            return original_date
        except Exception as e:
            return date_str
    
    def _validate_patient_info(self, patient: PatientInfo) -> Dict[str, Any]:
        """Validate patient information"""
        
        missing_fields = []
        validation_errors = []
        
        # Check required fields
        if not patient.first_name or not patient.first_name.strip():
            missing_fields.append("first_name")
        
        if not patient.last_name or not patient.last_name.strip():
            missing_fields.append("last_name")
        
        if not patient.dob or not patient.dob.strip():
            missing_fields.append("date_of_birth")
        else:
            # Validate date format
            if not self._validate_date_format(patient.dob):
                validation_errors.append("Invalid date format. Please use MM/DD/YYYY")
        
        if not patient.phone or not patient.phone.strip():
            missing_fields.append("phone")
        else:
            # Validate phone format
            if not self._validate_phone_format(patient.phone):
                validation_errors.append("Invalid phone number format")
        
        if not patient.email or not patient.email.strip():
            missing_fields.append("email")
        else:
            # Validate email format
            if not self._validate_email_format(patient.email):
                validation_errors.append("Invalid email format")
        
        return {
            "valid": len(missing_fields) == 0 and len(validation_errors) == 0,
            "missing_fields": missing_fields,
            "validation_errors": validation_errors
        }
    
    def _validate_date_format(self, date_str: str) -> bool:
        """Validate date format - be more flexible"""
        try:
            import datetime
            import re
            
            # Clean the date string
            date_str = date_str.strip()
            
            # Try standard formats first
            formats = [
                '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%m/%d/%y',
                '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d',
                '%B %d, %Y', '%b %d, %Y',  # July 9, 1999
                '%d %B %Y', '%d %b %Y',    # 9 July 1999
                '%B %d %Y', '%b %d %Y',    # July 9 1999
            ]
            
            for fmt in formats:
                try:
                    datetime.datetime.strptime(date_str, fmt)
                    return True
                except ValueError:
                    continue
            
            # Try to parse natural language dates like "9th July 1999"
            if re.search(r'\d{1,2}(st|nd|rd|th)?\s+\w+\s+\d{4}', date_str):
                # Remove ordinal suffixes (st, nd, rd, th)
                cleaned = re.sub(r'(\d{1,2})(st|nd|rd|th)', r'\1', date_str)
                for fmt in ['%d %B %Y', '%d %b %Y']:
                    try:
                        datetime.datetime.strptime(cleaned, fmt)
                        return True
                    except ValueError:
                        continue
            
            return False
        except Exception:
            return False
    
    def _validate_phone_format(self, phone_str: str) -> bool:
        """Validate phone number format"""
        try:
            import re
            
            # Remove common formatting characters
            clean_phone = re.sub(r'[^\d+]', '', phone_str)
            
            # Check if it's a valid length (10-15 digits)
            if len(clean_phone) < 10 or len(clean_phone) > 15:
                return False
            
            # Check if it's all digits (after removing +)
            if clean_phone.startswith('+'):
                clean_phone = clean_phone[1:]
            
            if not clean_phone.isdigit():
                return False
            
            # For 10-digit numbers, they should be valid
            if len(clean_phone) == 10:
                return True
            
            # For 11-digit numbers starting with 1 (US format)
            if len(clean_phone) == 11 and clean_phone.startswith('1'):
                return True
            
            # For international numbers (12-15 digits)
            if len(clean_phone) >= 12:
                return True
            
            return False
        except Exception:
            return False
    
    def _validate_email_format(self, email_str: str) -> bool:
        """Validate email format"""
        try:
            validate_email(email_str)
            return True
        except EmailNotValidError:
            return False
    
    def _get_missing_fields(self, patient: PatientInfo) -> List[str]:
        """Get list of missing required fields"""
        missing = []
        if not patient.first_name:
            missing.append("first_name")
        if not patient.last_name:
            missing.append("last_name")
        if not patient.dob:
            missing.append("date_of_birth")
        if not patient.phone:
            missing.append("phone")
        if not patient.email:
            missing.append("email")
        return missing
    
    def _generate_missing_info_message(self, missing_fields: List[str], first_name: str = "") -> str:
        """Generate message for missing information"""
        
        if not missing_fields:
            return "I have all the information I need. Thank you!"
        
        # Convert field names to display names
        display_names = [self.field_display_names.get(field, field) for field in missing_fields]
        
        if len(display_names) == 1:
            message = f"I need your {display_names[0]} to continue."
        else:
            message = f"I need your {' and '.join(display_names)} to continue."
        
        if first_name:
            message = f"{first_name}, {message.lower()}"
        
        return message
