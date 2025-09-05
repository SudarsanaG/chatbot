"""
Ollama-based Medical Scheduling Agent (Free Local LLM)
Uses Ollama with local models instead of OpenAI API
"""

import os
import json
import re
import requests
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from datetime import datetime

# Local imports
from src.agent import PatientInfo, AppointmentInfo, ConversationState
from fuzzywuzzy import fuzz

class ConversationMemory(TypedDict):
    """Memory for conversation state"""
    messages: List[Dict[str, str]]
    current_state: str
    patient_info: Dict[str, Any]
    appointment_info: Dict[str, Any]
    available_doctors: List[str]
    available_slots: List[Dict[str, Any]]

@dataclass
class ExtractedEntities:
    """Structured entity extraction results"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None
    doctor_preference: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    patient_type: Optional[str] = None
    cancellation_reason: Optional[str] = None

class OllamaLLM:
    """Simple Ollama LLM wrapper"""
    
    def __init__(self, model_name: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def invoke(self, prompt: str) -> str:
        """Invoke the Ollama model"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama API error: {e}")
            return "I'm sorry, I'm having trouble connecting to the AI service. Please try again."
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return "I'm sorry, I encountered an error. Please try again."

class OllamaMedicalSchedulingAgent:
    """
    Ollama-powered medical scheduling agent (Free Local LLM)
    """
    
    def __init__(self, model_name: str = None):
        """Initialize the Ollama agent"""
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.llm = OllamaLLM(self.model_name)
        
        # Load data
        self.patients_db = self._load_patients_db()
        self.schedules_db = self._load_schedules_db()
        
        # Initialize conversation state
        self.conversation_state = ConversationState.GREETING
        self.current_patient = PatientInfo()
        self.current_appointment = None
        self.conversation_history = []
        
        print(f"🤖 Ollama Agent initialized with model: {self.model_name}")
    
    def _load_patients_db(self) -> pd.DataFrame:
        """Load patient database from CSV"""
        try:
            return pd.read_csv("data/patients.csv")
        except FileNotFoundError:
            return pd.DataFrame()
    
    def _load_schedules_db(self) -> pd.DataFrame:
        """Load doctor schedules from Excel"""
        try:
            try:
                return pd.read_excel("data/schedules_new.xlsx")
            except (PermissionError, FileNotFoundError):
                return pd.read_excel("data/schedules.xlsx")
        except FileNotFoundError:
            return pd.DataFrame()
    
    def process_message(self, user_input: str) -> str:
        """Process user message through the Ollama LLM"""
        
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Create context for the LLM
        context = self._build_context(user_input)
        
        # Get LLM response
        try:
            response = self.llm.invoke(context)
            
            # Process the response and update state
            response = self._process_llm_response(response, user_input)
            
            # Add response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            error_response = f"I apologize, but I encountered an error: {str(e)}. Please try again."
            self.conversation_history.append({"role": "assistant", "content": error_response})
            return error_response
    
    def _build_context(self, user_input: str) -> str:
        """Build context for the LLM"""
        
        # Get conversation history
        history = ""
        for msg in self.conversation_history[-6:]:  # Last 6 messages
            role = "User" if msg["role"] == "user" else "Assistant"
            history += f"{role}: {msg['content']}\n"
        
        # Get current state info
        state_info = self._get_state_info()
        
        # Get available data
        available_doctors = list(self.schedules_db['Doctor'].unique()) if not self.schedules_db.empty else []
        
        context = f"""You are a friendly medical scheduling assistant. Help patients book appointments naturally.

CONVERSATION HISTORY:
{history}

CURRENT STATE: {self.conversation_state.value}
{state_info}

AVAILABLE DOCTORS: {', '.join(available_doctors) if available_doctors else 'None'}

PATIENT INFO:
- Name: {self.current_patient.first_name} {self.current_patient.last_name}
- Phone: {self.current_patient.phone}
- Email: {self.current_patient.email}
- Type: {self.current_patient.patient_type}

CURRENT USER MESSAGE: {user_input}

INSTRUCTIONS:
1. Respond naturally and helpfully
2. Extract any patient information mentioned
3. Guide the conversation toward booking an appointment
4. If they provide a name, ask for more details
5. If they want to book, help them select a doctor
6. Keep responses concise and professional
7. Use the available doctors list when suggesting options

RESPONSE:"""
        
        return context
    
    def _get_state_info(self) -> str:
        """Get information about current state"""
        if self.conversation_state == ConversationState.GREETING:
            return "Just started - need to collect patient information"
        elif self.conversation_state == ConversationState.COLLECTING_INFO:
            return "Collecting patient information - need name, phone, email"
        elif self.conversation_state == ConversationState.PATIENT_LOOKUP:
            return "Looking up existing patient in database"
        elif self.conversation_state == ConversationState.NEW_PATIENT_REGISTRATION:
            return "Registering new patient - need additional details"
        elif self.conversation_state == ConversationState.DOCTOR_SELECTION:
            return "Patient needs to select a doctor"
        elif self.conversation_state == ConversationState.SCHEDULING:
            return "Scheduling appointment - need date and time"
        elif self.conversation_state == ConversationState.INSURANCE_COLLECTION:
            return "Collecting insurance information"
        elif self.conversation_state == ConversationState.CONFIRMATION:
            return "Confirming appointment details"
        else:
            return "Unknown state"
    
    def _process_llm_response(self, response: str, user_input: str) -> str:
        """Process LLM response and update internal state"""
        
        # Extract entities from user input
        entities = self._extract_entities_simple(user_input)
        
        # Update patient info
        if entities.first_name:
            self.current_patient.first_name = entities.first_name
        if entities.last_name:
            self.current_patient.last_name = entities.last_name
        if entities.phone:
            self.current_patient.phone = entities.phone
        if entities.email:
            self.current_patient.email = entities.email
        if entities.patient_type:
            self.current_patient.patient_type = entities.patient_type
        
        # Update conversation state based on context
        self._update_conversation_state(entities, user_input)
        
        # Add specific information to response if needed
        if self.conversation_state == ConversationState.DOCTOR_SELECTION:
            available_doctors = list(self.schedules_db['Doctor'].unique())
            if available_doctors and "doctor" in response.lower():
                response += f"\n\nAvailable doctors: {', '.join(available_doctors)}"
        
        return response
    
    def _extract_entities_simple(self, text: str) -> ExtractedEntities:
        """Simple entity extraction using regex patterns"""
        entities = ExtractedEntities()
        text_lower = text.lower()
        
        # Extract names (simple patterns)
        name_patterns = [
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"i am (\w+)",
            r"call me (\w+)",
            r"(\w+) (\w+)",  # First Last pattern
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if len(match.groups()) == 1:
                    entities.first_name = match.group(1).title()
                elif len(match.groups()) == 2:
                    entities.first_name = match.group(1).title()
                    entities.last_name = match.group(2).title()
                break
        
        # Extract phone
        phone_pattern = r"(\d{3}[-.]?\d{3}[-.]?\d{4})"
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            entities.phone = phone_match.group(1)
        
        # Extract email
        email_pattern = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
        email_match = re.search(email_pattern, text)
        if email_match:
            entities.email = email_match.group(1)
        
        # Extract doctor preference
        doctor_keywords = ["dr.", "doctor", "physician", "specialist"]
        for keyword in doctor_keywords:
            if keyword in text_lower:
                # Extract text after keyword
                pattern = f"{keyword}\\s+([a-zA-Z\\s]+)"
                match = re.search(pattern, text_lower)
                if match:
                    entities.doctor_preference = match.group(1).strip()
                    break
        
        return entities
    
    def _update_conversation_state(self, entities: ExtractedEntities, user_input: str):
        """Update conversation state based on extracted entities and context"""
        
        if self.conversation_state == ConversationState.GREETING:
            if entities.first_name or "appointment" in user_input.lower():
                self.conversation_state = ConversationState.COLLECTING_INFO
        
        elif self.conversation_state == ConversationState.COLLECTING_INFO:
            if entities.first_name and entities.last_name:
                # Check if patient exists
                if self._patient_exists(entities.first_name, entities.last_name):
                    self.conversation_state = ConversationState.PATIENT_LOOKUP
                else:
                    self.conversation_state = ConversationState.NEW_PATIENT_REGISTRATION
            elif entities.first_name and not entities.last_name:
                # Still need last name
                pass
        
        elif self.conversation_state == ConversationState.PATIENT_LOOKUP:
            self.conversation_state = ConversationState.DOCTOR_SELECTION
        
        elif self.conversation_state == ConversationState.NEW_PATIENT_REGISTRATION:
            if entities.phone and entities.email:
                self.conversation_state = ConversationState.DOCTOR_SELECTION
        
        elif self.conversation_state == ConversationState.DOCTOR_SELECTION:
            if entities.doctor_preference:
                # Find matching doctor
                selected_doctor = self._find_doctor_match(entities.doctor_preference)
                if selected_doctor:
                    self.current_appointment = AppointmentInfo(patient=self.current_patient)
                    self.current_appointment.doctor = selected_doctor
                    self.conversation_state = ConversationState.SCHEDULING
        
        elif self.conversation_state == ConversationState.SCHEDULING:
            if entities.appointment_date and entities.appointment_time:
                self.conversation_state = ConversationState.INSURANCE_COLLECTION
        
        elif self.conversation_state == ConversationState.INSURANCE_COLLECTION:
            if entities.insurance_provider and entities.insurance_id:
                self.conversation_state = ConversationState.CONFIRMATION
        
        elif self.conversation_state == ConversationState.CONFIRMATION:
            if "confirm" in user_input.lower() or "yes" in user_input.lower():
                self.conversation_state = ConversationState.COMPLETED
    
    def _patient_exists(self, first_name: str, last_name: str) -> bool:
        """Check if patient exists in database"""
        if self.patients_db.empty:
            return False
        
        mask = (
            (self.patients_db['first_name'].str.lower() == first_name.lower()) &
            (self.patients_db['last_name'].str.lower() == last_name.lower())
        )
        return mask.any()
    
    def _find_doctor_match(self, doctor_preference: str) -> Optional[str]:
        """Find matching doctor using fuzzy matching"""
        available_doctors = list(self.schedules_db['Doctor'].unique())
        
        best_match = None
        best_score = 0
        
        for doctor in available_doctors:
            score = fuzz.ratio(doctor_preference.lower(), doctor.lower())
            if score > best_score and score > 60:
                best_score = score
                best_match = doctor
        
        return best_match
    
    def _show_available_slots(self, doctor: str) -> str:
        """Show available appointment slots for selected doctor"""
        available_slots = self.schedules_db[
            (self.schedules_db["Doctor"] == doctor) & 
            (self.schedules_db["Available"] == "Yes")
        ]
        
        if available_slots.empty:
            return f"I'm sorry, but {doctor} doesn't have any available slots at the moment. Would you like to choose a different doctor?"
        
        # Group slots by date
        slots_by_date = {}
        for _, slot in available_slots.iterrows():
            date = slot['Date']
            time = slot['Time']
            if date not in slots_by_date:
                slots_by_date[date] = []
            slots_by_date[date].append(time)
        
        slots_text = "📅 **Available Appointment Slots:**\n\n"
        for date, times in slots_by_date.items():
            slots_text += f"🗓️ **{date}:**\n"
            for i, time in enumerate(times, 1):
                slots_text += f"   {i}. {time}\n"
            slots_text += "\n"
        
        slots_text += "💡 **Please choose a slot by saying the number or date and time.**"
        return slots_text
