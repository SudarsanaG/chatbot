"""
AI Scheduling Agent - Main Agent Class
Implements ADK (Agent Development Toolkit) principles for medical appointment scheduling
"""

import json
import re
import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import openpyxl
from fuzzywuzzy import fuzz
import phonenumbers
from email_validator import validate_email, EmailNotValidError

class ConversationState(Enum):
    GREETING = "greeting"
    COLLECTING_INFO = "collecting_info"
    PATIENT_LOOKUP = "patient_lookup"
    NEW_PATIENT_REGISTRATION = "new_patient_registration"
    DOCTOR_SELECTION = "doctor_selection"
    SCHEDULING = "scheduling"
    INSURANCE_COLLECTION = "insurance_collection"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"

@dataclass
class PatientInfo:
    """Patient information structure"""
    first_name: str = ""
    last_name: str = ""
    dob: str = ""
    phone: str = ""
    email: str = ""
    patient_type: str = "New"  # New or Returning
    patient_id: Optional[int] = None

@dataclass
class InsuranceInfo:
    """Insurance information structure"""
    carrier: str = ""
    member_id: str = ""
    group_number: str = ""

@dataclass
class AppointmentInfo:
    """Appointment information structure"""
    patient: PatientInfo
    doctor: str = ""
    date: str = ""
    time: str = ""
    duration: int = 30  # minutes
    insurance: InsuranceInfo = None
    status: str = "Pending"

class MedicalSchedulingAgent:
    """
    AI Medical Scheduling Agent using ADK principles
    Handles natural conversation flow for appointment booking
    """
    
    def __init__(self):
        self.conversation_state = ConversationState.GREETING
        self.current_patient = PatientInfo()
        self.current_appointment = None
        self.conversation_history = []
        self.patients_db = self._load_patients_db()
        self.schedules_db = self._load_schedules_db()
        
    def _load_patients_db(self) -> pd.DataFrame:
        """Load patient database from CSV"""
        try:
            return pd.read_csv("data/patients.csv")
        except FileNotFoundError:
            return pd.DataFrame()
    
    def _load_schedules_db(self) -> pd.DataFrame:
        """Load doctor schedules from Excel"""
        try:
            # Try new file first (has more data), then original file if not available
            try:
                return pd.read_excel("data/schedules_new.xlsx")
            except (PermissionError, FileNotFoundError):
                return pd.read_excel("data/schedules.xlsx")
        except FileNotFoundError:
            return pd.DataFrame()
    
    def process_message(self, user_input: str) -> str:
        """
        Main message processing function
        Routes conversation based on current state
        """
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Extract entities from user input
        entities = self._extract_entities(user_input)
        
        # Process based on current conversation state
        response = self._route_conversation(user_input, entities)
        
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from user input using NLP"""
        entities = {}
        text_lower = text.lower()
        
        # Extract name patterns
        name_patterns = [
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"i am (\w+)",
            r"call me (\w+)",
            r"name: (\w+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text_lower)
            if match:
                entities["first_name"] = match.group(1).title()
                break
        
        # If no name pattern found, check if it's just a simple name (single word, letters only)
        if "first_name" not in entities and len(text.strip().split()) == 1 and text.strip().isalpha():
            entities["first_name"] = text.strip().title()
        
        # Extract date of birth patterns
        dob_patterns = [
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"born on (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"dob: (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, text)
            if match:
                entities["dob"] = match.group(1)
                break
        
        # Extract email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            entities["email"] = email_match.group(0)
        
        # Extract phone patterns
        phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            entities["phone"] = phone_match.group(0)
        
        # Extract doctor preferences
        doctor_keywords = ["dr.", "doctor", "physician", "specialist"]
        for keyword in doctor_keywords:
            if keyword in text_lower:
                # Extract doctor name after keyword
                pattern = f"{keyword}\\s+([a-zA-Z\\s]+)"
                match = re.search(pattern, text_lower)
                if match:
                    entities["doctor_preference"] = match.group(1).strip()
                    break
        
        return entities
    
    def _route_conversation(self, user_input: str, entities: Dict[str, Any]) -> str:
        """Route conversation based on current state"""
        
        if self.conversation_state == ConversationState.GREETING:
            return self._handle_greeting(user_input, entities)
        
        elif self.conversation_state == ConversationState.COLLECTING_INFO:
            return self._handle_info_collection(user_input, entities)
        
        elif self.conversation_state == ConversationState.PATIENT_LOOKUP:
            return self._handle_patient_lookup(user_input, entities)
        
        elif self.conversation_state == ConversationState.NEW_PATIENT_REGISTRATION:
            return self._handle_new_patient_registration(user_input, entities)
        
        elif self.conversation_state == ConversationState.DOCTOR_SELECTION:
            return self._handle_doctor_selection(user_input, entities)
        
        elif self.conversation_state == ConversationState.SCHEDULING:
            return self._handle_scheduling(user_input, entities)
        
        elif self.conversation_state == ConversationState.INSURANCE_COLLECTION:
            return self._handle_insurance_collection(user_input, entities)
        
        elif self.conversation_state == ConversationState.CONFIRMATION:
            return self._handle_confirmation(user_input, entities)
        
        else:
            return "I'm not sure how to help with that. Let me start over. Hello! I'm your AI scheduling assistant."
    
    def _handle_greeting(self, user_input: str, entities: Dict[str, Any]) -> str:
        """Handle initial greeting and start conversation"""
        # Check if user provided name in greeting
        if "first_name" in entities:
            self.current_patient.first_name = entities["first_name"]
            self.conversation_state = ConversationState.COLLECTING_INFO
            return f"Nice to meet you, {entities['first_name']}! What's your date of birth? (Please use MM/DD/YYYY format)"
        
        # If it's a simple greeting, ask for name
        if any(word in user_input.lower() for word in ["hi", "hello", "hey", "book", "appointment"]):
            return "Hello! I'm your AI medical scheduling assistant. What's your first name?"
        
        # If it's just a name without greeting words, treat it as a name
        if len(user_input.strip().split()) == 1 and user_input.strip().isalpha():
            self.current_patient.first_name = user_input.strip().title()
            self.conversation_state = ConversationState.COLLECTING_INFO
            return f"Nice to meet you, {user_input.strip().title()}! What's your date of birth? (Please use MM/DD/YYYY format)"
        
        return "Hello! I'm your AI medical scheduling assistant. What's your first name?"
    
    def _handle_info_collection(self, user_input: str, entities: Dict[str, Any]) -> str:
        """Handle collection of basic patient information"""
        
        # Update patient info with extracted entities
        if "first_name" in entities and not self.current_patient.first_name:
            self.current_patient.first_name = entities["first_name"]
        
        if "dob" in entities:
            self.current_patient.dob = entities["dob"]
            self.conversation_state = ConversationState.PATIENT_LOOKUP
            return self._perform_patient_lookup()
        
        # Ask for missing information
        if not self.current_patient.first_name:
            return "I didn't catch your name. Could you please tell me your first name?"
        
        if not self.current_patient.dob:
            return f"Thank you, {self.current_patient.first_name}. What's your date of birth? (Please use MM/DD/YYYY format)"
        
        return "I need a bit more information. What's your date of birth?"
    
    def _perform_patient_lookup(self) -> str:
        """Perform patient lookup in database"""
        if self.patients_db.empty:
            self.conversation_state = ConversationState.NEW_PATIENT_REGISTRATION
            return f"I don't see you in our system, {self.current_patient.first_name}. Let me register you as a new patient. What's your email address?"
        
        # Search for patient using fuzzy matching
        for _, patient in self.patients_db.iterrows():
            name_match = fuzz.ratio(
                self.current_patient.first_name.lower(),
                patient["FirstName"].lower()
            )
            dob_match = str(patient["DOB"]) == self.current_patient.dob
            
            if name_match > 80 and dob_match:
                # Found existing patient
                self.current_patient.patient_id = patient["PatientID"]
                self.current_patient.last_name = patient.get("LastName", "")
                self.current_patient.phone = str(patient.get("Phone", ""))
                self.current_patient.email = patient.get("Email", "")
                self.current_patient.patient_type = "Returning"
                
                self.conversation_state = ConversationState.DOCTOR_SELECTION
                return f"Welcome back, {self.current_patient.first_name}! I found you in our system as a returning patient. Which doctor would you like to see? Available doctors: {', '.join(self.schedules_db['Doctor'].unique())}"
        
        # Patient not found
        self.conversation_state = ConversationState.NEW_PATIENT_REGISTRATION
        return f"I don't see you in our system, {self.current_patient.first_name}. Let me register you as a new patient. What's your email address?"
    
    def _handle_patient_lookup(self, user_input: str, entities: Dict[str, Any]) -> str:
        """Handle patient lookup responses"""
        return self._perform_patient_lookup()
    
    def _handle_new_patient_registration(self, user_input: str, entities: Dict[str, Any]) -> str:
        """Handle new patient registration"""
        
        if "email" in entities:
            # Validate email format (simplified validation)
            email = entities["email"]
            if "@" in email and "." in email:
                self.current_patient.email = email
            else:
                return "That doesn't look like a valid email address. Could you please provide a valid email?"
        
        if "phone" in entities:
            self.current_patient.phone = entities["phone"]
        
        # Check if we have all required info
        if not self.current_patient.email:
            return "I need your email address to complete registration. What's your email?"
        
        if not self.current_patient.phone:
            return "I also need your phone number. What's your phone number?"
        
        # Register new patient
        self.current_patient.patient_id = len(self.patients_db) + 1
        self.current_patient.patient_type = "New"
        
        # Add to database
        new_patient_row = {
            "PatientID": self.current_patient.patient_id,
            "FirstName": self.current_patient.first_name,
            "LastName": self.current_patient.last_name,
            "DOB": self.current_patient.dob,
            "Phone": self.current_patient.phone,
            "Email": self.current_patient.email,
            "PatientType": self.current_patient.patient_type
        }
        
        self.patients_db = pd.concat([self.patients_db, pd.DataFrame([new_patient_row])], ignore_index=True)
        self.patients_db.to_csv("data/patients.csv", index=False)
        
        self.conversation_state = ConversationState.DOCTOR_SELECTION
        return f"Perfect! You're now registered, {self.current_patient.first_name}. Which doctor would you like to see? Available doctors: {', '.join(self.schedules_db['Doctor'].unique())}"
    
    def _handle_doctor_selection(self, user_input: str, entities: Dict[str, Any]) -> str:
        """Handle doctor selection with improved name matching"""
        available_doctors = self.schedules_db['Doctor'].unique()
        
        # Clean and normalize user input
        user_input_clean = user_input.lower().strip()
        
        # Remove common prefixes and suffixes
        prefixes_to_remove = ['dr.', 'dr', 'doctor']
        for prefix in prefixes_to_remove:
            if user_input_clean.startswith(prefix):
                user_input_clean = user_input_clean[len(prefix):].strip()
        
        # First, try exact matches (case-insensitive)
        for doctor in available_doctors:
            if doctor.lower() == user_input.lower():
                self.current_appointment = AppointmentInfo(patient=self.current_patient)
                self.current_appointment.doctor = doctor
                self.conversation_state = ConversationState.SCHEDULING
                return self._show_available_slots(doctor)
        
        # Try fuzzy matching for better accuracy
        best_match = None
        best_score = 0
        
        for doctor in available_doctors:
            doctor_lower = doctor.lower()
            
            # Calculate fuzzy match score
            score = fuzz.ratio(user_input_clean, doctor_lower)
            
            # Also check if user input is contained in doctor name or vice versa
            if user_input_clean in doctor_lower or doctor_lower in user_input_clean:
                score = max(score, 80)  # Boost score for substring matches
            
            # Check individual name parts
            doctor_parts = doctor_lower.replace('dr.', '').strip().split()
            for part in doctor_parts:
                if part and len(part) > 2:  # Ignore very short parts
                    part_score = fuzz.ratio(user_input_clean, part)
                    if part_score > 70:  # Good match for individual name part
                        score = max(score, part_score)
            
            # Check if user input matches first name
            if len(doctor_parts) >= 2:
                first_name = doctor_parts[0]
                if user_input_clean == first_name:
                    score = max(score, 90)
            
            # Check if user input matches last name
            if len(doctor_parts) >= 2:
                last_name = doctor_parts[-1]
                if user_input_clean == last_name:
                    score = max(score, 90)
            
            if score > best_score and score > 60:  # Minimum threshold for matching
                best_score = score
                best_match = doctor
        
        if best_match:
            self.current_appointment = AppointmentInfo(patient=self.current_patient)
            self.current_appointment.doctor = best_match
            self.conversation_state = ConversationState.SCHEDULING
            return self._show_available_slots(best_match)
        
        return f"I didn't catch which doctor you'd like to see. Available doctors are: {', '.join(available_doctors)}. Which one would you prefer?"
    
    def _show_available_slots(self, doctor: str) -> str:
        """Show available appointment slots for selected doctor"""
        available_slots = self.schedules_db[
            (self.schedules_db["Doctor"] == doctor) & 
            (self.schedules_db["Available"] == "Yes")
        ]
        
        if available_slots.empty:
            return f"I'm sorry, but {doctor} doesn't have any available slots at the moment. Would you like to choose a different doctor?"
        
        # Determine appointment duration based on patient type
        duration = 60 if self.current_patient.patient_type == "New" else 30
        self.current_appointment.duration = duration
        
        # Group slots by date for better organization
        slots_by_date = {}
        for _, slot in available_slots.iterrows():
            date = slot['Date']
            time = slot['Time']
            if date not in slots_by_date:
                slots_by_date[date] = []
            slots_by_date[date].append(time)
        
        slots_text = "📅 **Available Appointment Slots:**\n\n"
        
        slot_number = 1
        for date, times in sorted(slots_by_date.items()):
            # Format date nicely
            try:
                from datetime import datetime
                date_obj = datetime.strptime(str(date), '%Y-%m-%d')
                formatted_date = date_obj.strftime('%A, %B %d, %Y')
            except:
                formatted_date = str(date)
            
            slots_text += f"🗓️ **{formatted_date}:**\n"
            for time in sorted(times):
                slots_text += f"   {slot_number}. {time}\n"
                slot_number += 1
            slots_text += "\n"
        
        slots_text += f"⏱️ Since you're a **{self.current_patient.patient_type.lower()} patient**, your appointment will be **{duration} minutes** long.\n\n"
        slots_text += "💡 **Please choose a slot by saying the number** (e.g., '1', '15', '25')"
        
        return slots_text
    
    def _handle_scheduling(self, user_input: str, entities: Dict[str, Any]) -> str:
        """Handle appointment scheduling"""
        # Extract slot selection
        slot_number = None
        for word in user_input.split():
            if word.isdigit():
                slot_number = int(word)
                break
        
        if not slot_number:
            return "I didn't catch which slot you'd like. Please tell me the number of your preferred slot."
        
        # Get available slots
        available_slots = self.schedules_db[
            (self.schedules_db["Doctor"] == self.current_appointment.doctor) & 
            (self.schedules_db["Available"] == "Yes")
        ]
        
        if slot_number < 1 or slot_number > len(available_slots):
            return f"Please choose a number between 1 and {len(available_slots)}."
        
        # Select the slot
        selected_slot = available_slots.iloc[slot_number - 1]
        self.current_appointment.date = selected_slot['Date']
        self.current_appointment.time = selected_slot['Time']
        
        # Mark slot as unavailable
        slot_index = self.schedules_db[
            (self.schedules_db["Doctor"] == self.current_appointment.doctor) &
            (self.schedules_db["Date"] == selected_slot['Date']) &
            (self.schedules_db["Time"] == selected_slot['Time'])
        ].index[0]
        
        self.schedules_db.loc[slot_index, "Available"] = "No"
        self.schedules_db.to_excel("data/schedules.xlsx", index=False)
        
        self.conversation_state = ConversationState.INSURANCE_COLLECTION
        # Use the doctor name as-is from the database (already has "Dr.")
        doctor_display = self.current_appointment.doctor
        
        return f"Great! I've selected {selected_slot['Date']} at {selected_slot['Time']} for your {self.current_appointment.duration}-minute appointment with {doctor_display}.\n\n💳 **Insurance Information:**\nWhat's your insurance carrier? (If you don't have insurance, just say 'no insurance' or 'self pay')"
    
    def _handle_insurance_collection(self, user_input: str, entities: Dict[str, Any]) -> str:
        """Handle insurance information collection"""
        if not hasattr(self.current_appointment, 'insurance') or not self.current_appointment.insurance:
            self.current_appointment.insurance = InsuranceInfo()
        
        # Extract insurance information
        if not self.current_appointment.insurance.carrier:
            user_input_lower = user_input.lower()
            
            # Check for "no insurance" responses
            no_insurance_phrases = ["no insurance", "don't have", "dont have", "none", "no carrier", "self pay", "cash", "not available"]
            if any(phrase in user_input_lower for phrase in no_insurance_phrases):
                self.current_appointment.insurance.carrier = "Self Pay"
                self.current_appointment.insurance.member_id = "Not Available"
                self.current_appointment.insurance.group_number = "Not Available"
                self.conversation_state = ConversationState.CONFIRMATION
                return self._generate_confirmation()
            
            # Look for common insurance carriers
            insurance_carriers = ["blue cross", "aetna", "cigna", "humana", "kaiser", "medicare", "medicaid"]
            
            for carrier in insurance_carriers:
                if carrier in user_input_lower:
                    self.current_appointment.insurance.carrier = carrier.title()
                    break
            
            if not self.current_appointment.insurance.carrier:
                self.current_appointment.insurance.carrier = user_input.strip()
            
            return f"Thank you. I have {self.current_appointment.insurance.carrier} as your carrier. What's your member ID?"
        
        elif not self.current_appointment.insurance.member_id:
            user_input_lower = user_input.lower()
            
            # Check for "not available" responses
            if any(phrase in user_input_lower for phrase in ["not available", "don't have", "dont have", "none", "n/a"]):
                self.current_appointment.insurance.member_id = "Not Available"
                self.current_appointment.insurance.group_number = "Not Available"
                self.conversation_state = ConversationState.CONFIRMATION
                return self._generate_confirmation()
            
            # Extract member ID (usually alphanumeric)
            member_id_pattern = r'[A-Za-z0-9]{6,}'
            match = re.search(member_id_pattern, user_input)
            if match:
                self.current_appointment.insurance.member_id = match.group(0)
            else:
                self.current_appointment.insurance.member_id = user_input.strip()
            
            return "Got it. What's your group number? (If you don't have one, just say 'not available' or 'none')"
        
        elif not self.current_appointment.insurance.group_number:
            user_input_lower = user_input.lower()
            if any(phrase in user_input_lower for phrase in ["none", "n/a", "not available", "don't have", "dont have"]):
                self.current_appointment.insurance.group_number = "Not Available"
            else:
                self.current_appointment.insurance.group_number = user_input.strip()
            
            self.conversation_state = ConversationState.CONFIRMATION
            return self._generate_confirmation()
        
        return "I have all your insurance information. Let me confirm your appointment details."
    
    def _generate_confirmation(self) -> str:
        """Generate appointment confirmation"""
        confirmation = f"""
🎉 **APPOINTMENT CONFIRMED!** 🎉

👤 **Patient Information:**
• Name: {self.current_patient.first_name} {self.current_patient.last_name}
• Type: {self.current_patient.patient_type} Patient

📅 **Appointment Details:**
• Date: {self.current_appointment.date}
• Time: {self.current_appointment.time}
• Doctor: {self.current_appointment.doctor}
• Duration: {self.current_appointment.duration} minutes

💳 **Insurance Information:**
• Carrier: {self.current_appointment.insurance.carrier}
• Member ID: {self.current_appointment.insurance.member_id}
• Group Number: {self.current_appointment.insurance.group_number}

✅ **Next Steps:**
Your appointment has been saved to our system. You'll receive:
1. 📧 An intake form via email
2. 📱 Automated reminders before your appointment

Is there anything else I can help you with?
        """
        
        # Save appointment to database
        self._save_appointment()
        
        # Send intake form
        self._send_intake_form()
        
        # Schedule reminders
        self._schedule_reminders()
        
        self.conversation_state = ConversationState.COMPLETED
        return confirmation.strip()
    
    def _handle_confirmation(self, user_input: str, entities: Dict[str, Any]) -> str:
        """Handle confirmation responses"""
        if any(word in user_input.lower() for word in ["yes", "confirm", "correct", "right"]):
            return self._generate_confirmation()
        elif any(word in user_input.lower() for word in ["no", "wrong", "incorrect", "change"]):
            return "I understand you'd like to make changes. Let me know what you'd like to modify."
        else:
            return "Please let me know if this information is correct or if you'd like to make any changes."
    
    def _save_appointment(self):
        """Save appointment to Excel file"""
        appointment_data = {
            "PatientName": f"{self.current_patient.first_name} {self.current_patient.last_name}".strip(),
            "DOB": self.current_patient.dob,
            "Phone": self.current_patient.phone,
            "Email": self.current_patient.email,
            "Doctor": self.current_appointment.doctor,
            "Date": self.current_appointment.date,
            "Time": self.current_appointment.time,
            "Duration": self.current_appointment.duration,
            "PatientType": self.current_patient.patient_type,
            "InsuranceCarrier": self.current_appointment.insurance.carrier,
            "MemberID": self.current_appointment.insurance.member_id,
            "GroupNumber": self.current_appointment.insurance.group_number,
            "Status": "Confirmed",
            "CreatedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            existing_appointments = pd.read_excel("data/appointments.xlsx")
            appointments_df = pd.concat([existing_appointments, pd.DataFrame([appointment_data])], ignore_index=True)
        except FileNotFoundError:
            appointments_df = pd.DataFrame([appointment_data])
        
        appointments_df.to_excel("data/appointments.xlsx", index=False)
    
    def _send_intake_form(self):
        """Send intake form to patient"""
        # This would integrate with email service
        print(f"📧 Intake form sent to {self.current_patient.email}")
    
    def _schedule_reminders(self):
        """Schedule automated reminders"""
        # This would integrate with scheduling service
        print(f"📅 Reminders scheduled for {self.current_patient.first_name}")
    
    def reset_conversation(self):
        """Reset conversation state for new patient"""
        self.conversation_state = ConversationState.GREETING
        self.current_patient = PatientInfo()
        self.current_appointment = None
        self.conversation_history = []
