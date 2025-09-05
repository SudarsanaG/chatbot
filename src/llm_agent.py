"""
LLM-Powered Medical Scheduling Agent using LangChain and LangGraph
Handles natural conversation flow and entity extraction with OpenAI
"""

import os
import json
import re
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from datetime import datetime

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Local imports
from src.agent import PatientInfo, AppointmentInfo, ConversationState
from src.utils import validate_email, validate_phone, validate_date
from fuzzywuzzy import fuzz

class ConversationMemory(TypedDict):
    """Memory for conversation state"""
    messages: Annotated[List, add_messages]
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

class LLMMedicalSchedulingAgent:
    """
    LLM-powered medical scheduling agent using LangChain and LangGraph
    """
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the LLM agent"""
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=self.api_key
        )
        
        # Load data
        self.patients_db = self._load_patients_db()
        self.schedules_db = self._load_schedules_db()
        
        # Initialize conversation state
        self.current_state = ConversationState.GREETING
        self.current_patient = PatientInfo()
        self.current_appointment = None
        self.conversation_history = []
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
    
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
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for conversation management"""
        
        # Define the workflow
        workflow = StateGraph(ConversationMemory)
        
        # Add nodes for each conversation state
        workflow.add_node("greeting", self._handle_greeting)
        workflow.add_node("collecting_info", self._handle_info_collection)
        workflow.add_node("patient_lookup", self._handle_patient_lookup)
        workflow.add_node("new_patient_registration", self._handle_new_patient_registration)
        workflow.add_node("doctor_selection", self._handle_doctor_selection)
        workflow.add_node("scheduling", self._handle_scheduling)
        workflow.add_node("insurance_collection", self._handle_insurance_collection)
        workflow.add_node("confirmation", self._handle_confirmation)
        
        # Define the conversation flow
        workflow.set_entry_point("greeting")
        
        # Add conditional edges based on conversation state
        workflow.add_conditional_edges(
            "greeting",
            self._route_from_greeting,
            {
                "collecting_info": "collecting_info",
                "patient_lookup": "patient_lookup",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "collecting_info",
            self._route_from_collecting_info,
            {
                "patient_lookup": "patient_lookup",
                "new_patient_registration": "new_patient_registration",
                "doctor_selection": "doctor_selection",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "patient_lookup",
            self._route_from_patient_lookup,
            {
                "doctor_selection": "doctor_selection",
                "new_patient_registration": "new_patient_registration",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "new_patient_registration",
            self._route_from_new_patient,
            {
                "doctor_selection": "doctor_selection",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "doctor_selection",
            self._route_from_doctor_selection,
            {
                "scheduling": "scheduling",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "scheduling",
            self._route_from_scheduling,
            {
                "insurance_collection": "insurance_collection",
                "confirmation": "confirmation",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "insurance_collection",
            self._route_from_insurance,
            {
                "confirmation": "confirmation",
                "end": END
            }
        )
        
        workflow.add_edge("confirmation", END)
        
        return workflow.compile()
    
    def process_message(self, user_input: str) -> str:
        """Process user message through the LLM workflow"""
        
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Prepare the conversation memory
        memory = ConversationMemory(
            messages=[HumanMessage(content=user_input)],
            current_state=self.current_state.value,
            patient_info=self._patient_to_dict(self.current_patient),
            appointment_info=self._appointment_to_dict(self.current_appointment),
            available_doctors=list(self.schedules_db['Doctor'].unique()) if not self.schedules_db.empty else [],
            available_slots=[]
        )
        
        # Run the workflow
        try:
            result = self.workflow.invoke(memory)
            
            # Extract response from the result
            if result.get("messages"):
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    response = last_message.content
                else:
                    response = "I'm processing your request. Please wait a moment."
            else:
                response = "I'm processing your request. Please wait a moment."
            
            # Update conversation state
            if "current_state" in result:
                self.current_state = ConversationState(result["current_state"])
            
            # Update patient and appointment info
            if "patient_info" in result:
                self.current_patient = self._dict_to_patient(result["patient_info"])
            
            if "appointment_info" in result:
                self.current_appointment = self._dict_to_appointment(result["appointment_info"])
            
            # Add response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            error_response = f"I apologize, but I encountered an error: {str(e)}. Please try again."
            self.conversation_history.append({"role": "assistant", "content": error_response})
            return error_response
    
    def _extract_entities_with_llm(self, user_input: str) -> ExtractedEntities:
        """Use LLM to extract entities from user input"""
        
        extraction_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
            You are an expert at extracting medical appointment information from natural language.
            Extract the following information from the user's input and return it as JSON:
            
            - first_name: Patient's first name
            - last_name: Patient's last name  
            - date_of_birth: Date of birth (format: YYYY-MM-DD)
            - phone: Phone number
            - email: Email address
            - insurance_provider: Insurance company name
            - insurance_id: Insurance ID/policy number
            - doctor_preference: Preferred doctor name
            - appointment_date: Desired appointment date
            - appointment_time: Desired appointment time
            - patient_type: "New" or "Returning"
            - cancellation_reason: Reason for cancellation (if applicable)
            
            Only extract information that is explicitly mentioned. Return null for missing fields.
            Be flexible with name variations and partial information.
            """),
            HumanMessage(content=user_input)
        ])
        
        parser = JsonOutputParser(pydantic_object=ExtractedEntities)
        
        try:
            chain = extraction_prompt | self.llm | parser
            result = chain.invoke({"input": user_input})
            return ExtractedEntities(**result)
        except Exception as e:
            print(f"Entity extraction error: {e}")
            return ExtractedEntities()
    
    def _handle_greeting(self, memory: ConversationMemory) -> ConversationMemory:
        """Handle greeting state with LLM"""
        
        greeting_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
            You are a friendly medical scheduling assistant. Greet the patient warmly and ask how you can help them today.
            Keep responses concise and professional. If they mention booking an appointment, guide them to provide their name.
            """),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        chain = greeting_prompt | self.llm
        response = chain.invoke(memory)
        
        memory["messages"].append(response)
        memory["current_state"] = "collecting_info"
        
        return memory
    
    def _handle_info_collection(self, memory: ConversationMemory) -> ConversationMemory:
        """Handle information collection with LLM"""
        
        # Extract entities using LLM
        user_input = memory["messages"][-1].content
        entities = self._extract_entities_with_llm(user_input)
        
        # Update patient info with extracted entities
        patient_info = memory.get("patient_info", {})
        if entities.first_name:
            patient_info["first_name"] = entities.first_name
        if entities.last_name:
            patient_info["last_name"] = entities.last_name
        if entities.date_of_birth:
            patient_info["date_of_birth"] = entities.date_of_birth
        if entities.phone:
            patient_info["phone"] = entities.phone
        if entities.email:
            patient_info["email"] = entities.email
        if entities.patient_type:
            patient_info["patient_type"] = entities.patient_type
        
        memory["patient_info"] = patient_info
        
        # Determine next state based on collected information
        if patient_info.get("first_name") and patient_info.get("last_name"):
            # Check if patient exists in database
            if self._patient_exists(patient_info["first_name"], patient_info["last_name"]):
                memory["current_state"] = "patient_lookup"
                response = AIMessage(content=f"Hello {patient_info['first_name']}! I found you in our system. Let me verify your information and then we can proceed with scheduling your appointment.")
            else:
                memory["current_state"] = "new_patient_registration"
                response = AIMessage(content=f"Hello {patient_info['first_name']}! I don't see you in our system yet. Let me collect some additional information to register you as a new patient.")
        else:
            # Still need more information
            missing_info = []
            if not patient_info.get("first_name"):
                missing_info.append("first name")
            if not patient_info.get("last_name"):
                missing_info.append("last name")
            
            response = AIMessage(content=f"I'd be happy to help you schedule an appointment! I need your {' and '.join(missing_info)} to get started.")
        
        memory["messages"].append(response)
        return memory
    
    def _handle_patient_lookup(self, memory: ConversationMemory) -> ConversationMemory:
        """Handle patient lookup with LLM"""
        
        patient_info = memory.get("patient_info", {})
        first_name = patient_info.get("first_name", "")
        last_name = patient_info.get("last_name", "")
        
        # Find patient in database
        patient = self._find_patient(first_name, last_name)
        
        if patient is not None:
            # Update patient info with database data
            memory["patient_info"] = {
                "first_name": patient["first_name"],
                "last_name": patient["last_name"],
                "date_of_birth": patient["date_of_birth"],
                "phone": patient["phone"],
                "email": patient["email"],
                "patient_type": "Returning"
            }
            
            memory["current_state"] = "doctor_selection"
            available_doctors = list(self.schedules_db['Doctor'].unique())
            response = AIMessage(content=f"Perfect! I found your information, {first_name}. Which doctor would you like to see? Available doctors: {', '.join(available_doctors)}")
        else:
            memory["current_state"] = "new_patient_registration"
            response = AIMessage(content=f"I couldn't find a patient with that name in our system. Let me register you as a new patient. I'll need some additional information.")
        
        memory["messages"].append(response)
        return memory
    
    def _handle_new_patient_registration(self, memory: ConversationMemory) -> ConversationMemory:
        """Handle new patient registration with LLM"""
        
        patient_info = memory.get("patient_info", {})
        
        # Check if we have all required information
        required_fields = ["first_name", "last_name", "date_of_birth", "phone", "email"]
        missing_fields = [field for field in required_fields if not patient_info.get(field)]
        
        if missing_fields:
            # Still need more information
            field_names = {
                "date_of_birth": "date of birth",
                "phone": "phone number",
                "email": "email address"
            }
            
            missing_display = [field_names.get(field, field) for field in missing_fields]
            response = AIMessage(content=f"To complete your registration, I need your {' and '.join(missing_display)}.")
        else:
            # Register new patient
            self._register_new_patient(patient_info)
            memory["patient_info"]["patient_type"] = "New"
            memory["current_state"] = "doctor_selection"
            
            available_doctors = list(self.schedules_db['Doctor'].unique())
            response = AIMessage(content=f"Perfect! You're now registered, {patient_info['first_name']}. Which doctor would you like to see? Available doctors: {', '.join(available_doctors)}")
        
        memory["messages"].append(response)
        return memory
    
    def _handle_doctor_selection(self, memory: ConversationMemory) -> ConversationMemory:
        """Handle doctor selection with LLM"""
        
        user_input = memory["messages"][-1].content
        entities = self._extract_entities_with_llm(user_input)
        
        available_doctors = memory.get("available_doctors", [])
        selected_doctor = None
        
        if entities.doctor_preference:
            # Use fuzzy matching to find the best doctor match
            best_match = None
            best_score = 0
            
            for doctor in available_doctors:
                score = fuzz.ratio(entities.doctor_preference.lower(), doctor.lower())
                if score > best_score and score > 60:
                    best_score = score
                    best_match = doctor
            
            if best_match:
                selected_doctor = best_match
        
        if selected_doctor:
            # Initialize appointment
            memory["appointment_info"] = {
                "patient": memory["patient_info"],
                "doctor": selected_doctor,
                "status": "Pending"
            }
            
            memory["current_state"] = "scheduling"
            response = AIMessage(content=self._show_available_slots(selected_doctor))
        else:
            response = AIMessage(content=f"I didn't catch which doctor you'd like to see. Available doctors are: {', '.join(available_doctors)}. Which one would you prefer?")
        
        memory["messages"].append(response)
        return memory
    
    def _handle_scheduling(self, memory: ConversationMemory) -> ConversationMemory:
        """Handle appointment scheduling with LLM"""
        
        user_input = memory["messages"][-1].content
        entities = self._extract_entities_with_llm(user_input)
        
        appointment_info = memory.get("appointment_info", {})
        
        if entities.appointment_date and entities.appointment_time:
            # Validate and set appointment
            if self._is_slot_available(appointment_info["doctor"], entities.appointment_date, entities.appointment_time):
                appointment_info["date"] = entities.appointment_date
                appointment_info["time"] = entities.appointment_time
                appointment_info["duration"] = 60 if memory["patient_info"].get("patient_type") == "New" else 30
                
                memory["appointment_info"] = appointment_info
                memory["current_state"] = "insurance_collection"
                
                response = AIMessage(content=f"Great! I've scheduled your appointment with {appointment_info['doctor']} on {entities.appointment_date} at {entities.appointment_time}. Now I need your insurance information to complete the booking.")
            else:
                response = AIMessage(content="I'm sorry, but that time slot is not available. Please choose from the available slots I showed you earlier.")
        else:
            response = AIMessage(content="Please select a date and time from the available slots I provided.")
        
        memory["messages"].append(response)
        return memory
    
    def _handle_insurance_collection(self, memory: ConversationMemory) -> ConversationMemory:
        """Handle insurance information collection with LLM"""
        
        user_input = memory["messages"][-1].content
        entities = self._extract_entities_with_llm(user_input)
        
        appointment_info = memory.get("appointment_info", {})
        
        if entities.insurance_provider and entities.insurance_id:
            appointment_info["insurance_provider"] = entities.insurance_provider
            appointment_info["insurance_id"] = entities.insurance_id
            
            memory["appointment_info"] = appointment_info
            memory["current_state"] = "confirmation"
            
            response = AIMessage(content=f"Perfect! I have all the information needed. Let me confirm your appointment details and complete the booking.")
        else:
            missing_info = []
            if not entities.insurance_provider:
                missing_info.append("insurance provider")
            if not entities.insurance_id:
                missing_info.append("insurance ID/policy number")
            
            response = AIMessage(content=f"To complete your appointment booking, I need your {' and '.join(missing_info)}.")
        
        memory["messages"].append(response)
        return memory
    
    def _handle_confirmation(self, memory: ConversationMemory) -> ConversationMemory:
        """Handle appointment confirmation with LLM"""
        
        appointment_info = memory.get("appointment_info", {})
        patient_info = memory.get("patient_info", {})
        
        # Save appointment to database
        self._save_appointment(appointment_info, patient_info)
        
        # Generate confirmation message
        confirmation_message = f"""
🎉 **Appointment Confirmed!**

**Patient:** {patient_info['first_name']} {patient_info['last_name']}
**Doctor:** {appointment_info['doctor']}
**Date:** {appointment_info['date']}
**Time:** {appointment_info['time']}
**Duration:** {appointment_info['duration']} minutes
**Type:** {patient_info['patient_type']} Patient
**Insurance:** {appointment_info.get('insurance_provider', 'N/A')}

Your appointment has been successfully scheduled! You will receive a confirmation email shortly.
        """.strip()
        
        response = AIMessage(content=confirmation_message)
        memory["messages"].append(response)
        
        # Reset for next conversation
        memory["current_state"] = "greeting"
        memory["patient_info"] = {}
        memory["appointment_info"] = {}
        
        return memory
    
    # Routing functions
    def _route_from_greeting(self, memory: ConversationMemory) -> str:
        """Route from greeting state"""
        return "collecting_info"
    
    def _route_from_collecting_info(self, memory: ConversationMemory) -> str:
        """Route from collecting info state"""
        patient_info = memory.get("patient_info", {})
        if patient_info.get("first_name") and patient_info.get("last_name"):
            if self._patient_exists(patient_info["first_name"], patient_info["last_name"]):
                return "patient_lookup"
            else:
                return "new_patient_registration"
        return "collecting_info"
    
    def _route_from_patient_lookup(self, memory: ConversationMemory) -> str:
        """Route from patient lookup state"""
        return "doctor_selection"
    
    def _route_from_new_patient(self, memory: ConversationMemory) -> str:
        """Route from new patient registration state"""
        return "doctor_selection"
    
    def _route_from_doctor_selection(self, memory: ConversationMemory) -> str:
        """Route from doctor selection state"""
        return "scheduling"
    
    def _route_from_scheduling(self, memory: ConversationMemory) -> str:
        """Route from scheduling state"""
        appointment_info = memory.get("appointment_info", {})
        if appointment_info.get("date") and appointment_info.get("time"):
            return "insurance_collection"
        return "scheduling"
    
    def _route_from_insurance(self, memory: ConversationMemory) -> str:
        """Route from insurance collection state"""
        return "confirmation"
    
    # Helper methods
    def _patient_exists(self, first_name: str, last_name: str) -> bool:
        """Check if patient exists in database"""
        if self.patients_db.empty:
            return False
        
        mask = (
            (self.patients_db['first_name'].str.lower() == first_name.lower()) &
            (self.patients_db['last_name'].str.lower() == last_name.lower())
        )
        return mask.any()
    
    def _find_patient(self, first_name: str, last_name: str) -> Optional[Dict]:
        """Find patient in database"""
        if self.patients_db.empty:
            return None
        
        mask = (
            (self.patients_db['first_name'].str.lower() == first_name.lower()) &
            (self.patients_db['last_name'].str.lower() == last_name.lower())
        )
        
        patient_row = self.patients_db[mask]
        if not patient_row.empty:
            return patient_row.iloc[0].to_dict()
        return None
    
    def _register_new_patient(self, patient_info: Dict[str, Any]) -> None:
        """Register new patient in database"""
        new_patient = pd.DataFrame([patient_info])
        self.patients_db = pd.concat([self.patients_db, new_patient], ignore_index=True)
        self.patients_db.to_csv("data/patients.csv", index=False)
    
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
    
    def _is_slot_available(self, doctor: str, date: str, time: str) -> bool:
        """Check if appointment slot is available"""
        if self.schedules_db.empty:
            return False
        
        mask = (
            (self.schedules_db["Doctor"] == doctor) &
            (self.schedules_db["Date"] == date) &
            (self.schedules_db["Time"] == time) &
            (self.schedules_db["Available"] == "Yes")
        )
        return mask.any()
    
    def _save_appointment(self, appointment_info: Dict[str, Any], patient_info: Dict[str, Any]) -> None:
        """Save appointment to database"""
        # This would integrate with your existing appointment saving logic
        # For now, we'll just print the appointment details
        print(f"Appointment saved: {appointment_info}")
    
    def _patient_to_dict(self, patient: PatientInfo) -> Dict[str, Any]:
        """Convert PatientInfo to dictionary"""
        if patient is None:
            return {}
        return {
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth,
            "phone": patient.phone,
            "email": patient.email,
            "patient_type": patient.patient_type
        }
    
    def _dict_to_patient(self, data: Dict[str, Any]) -> PatientInfo:
        """Convert dictionary to PatientInfo"""
        return PatientInfo(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            date_of_birth=data.get("date_of_birth", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            patient_type=data.get("patient_type", "New")
        )
    
    def _appointment_to_dict(self, appointment: AppointmentInfo) -> Dict[str, Any]:
        """Convert AppointmentInfo to dictionary"""
        if appointment is None:
            return {}
        return {
            "patient": self._patient_to_dict(appointment.patient) if appointment.patient else {},
            "doctor": appointment.doctor,
            "date": appointment.date,
            "time": appointment.time,
            "duration": appointment.duration,
            "status": appointment.status
        }
    
    def _dict_to_appointment(self, data: Dict[str, Any]) -> AppointmentInfo:
        """Convert dictionary to AppointmentInfo"""
        patient_data = data.get("patient", {})
        patient = self._dict_to_patient(patient_data) if patient_data else None
        
        return AppointmentInfo(
            patient=patient,
            doctor=data.get("doctor", ""),
            date=data.get("date", ""),
            time=data.get("time", ""),
            duration=data.get("duration", 30),
            status=data.get("status", "Pending")
        )
