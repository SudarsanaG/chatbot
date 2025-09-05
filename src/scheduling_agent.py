"""
Scheduling Agent
Specializes in doctor selection and appointment scheduling
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd
from datetime import datetime, timedelta
from src.gemini_client import GeminiClient
from src.agent import PatientInfo, AppointmentInfo
from fuzzywuzzy import fuzz

@dataclass
class SchedulingResult:
    """Result of scheduling operation"""
    success: bool
    message: str
    appointment_info: Optional[AppointmentInfo]
    next_state: str
    available_slots: List[Dict[str, Any]]

@dataclass
class DoctorInfo:
    """Doctor information"""
    name: str
    specialty: str
    available_slots: List[Dict[str, Any]]

class SchedulingAgent:
    """Agent responsible for doctor selection and appointment scheduling"""
    
    def __init__(self, gemini_client: GeminiClient, schedules_db: pd.DataFrame):
        self.gemini = gemini_client
        self.schedules_db = schedules_db
        self.available_doctors = self._get_available_doctors()
    
    def _get_available_doctors(self) -> List[str]:
        """Get list of available doctors from schedule database"""
        if self.schedules_db.empty:
            return []
        return list(self.schedules_db['Doctor'].unique())
    
    def handle_doctor_selection(self, user_input: str, patient: PatientInfo, conversation_history: List[Dict]) -> SchedulingResult:
        """Handle doctor selection process - deterministic, no LLM calls"""
        
        # Check if user input contains "Select" followed by doctor name
        if user_input.lower().startswith("select "):
            doctor_name = user_input[7:].strip()  # Remove "Select " prefix
            selected_doctor = self._find_exact_doctor_match(doctor_name)
        else:
            # Try fuzzy matching for other inputs
            selected_doctor = self._find_best_doctor_match(user_input)
        
        if selected_doctor:
            # Create appointment info
            appointment_info = AppointmentInfo(patient=patient)
            appointment_info.doctor = selected_doctor
            appointment_info.duration = 60 if patient.patient_type == "New" else 30
            
            # Get available slots for the doctor
            available_slots = self._get_available_slots(selected_doctor)
            
            if available_slots:
                # Directly show available slots - no LLM call needed
                response = f"✅ **Selected Dr. {selected_doctor}**\n\n"
                response += self._format_available_slots(available_slots, selected_doctor, patient.patient_type)
                
                return SchedulingResult(
                    success=True,
                    message=response,
                    appointment_info=appointment_info,
                    next_state="scheduling",
                    available_slots=available_slots
                )
            else:
                # No available slots
                message = f"❌ **Dr. {selected_doctor}** doesn't have any available slots at the moment. Please select a different doctor."
                return SchedulingResult(
                    success=False,
                    message=message,
                    appointment_info=None,
                    next_state="doctor_selection",
                    available_slots=[]
                )
        else:
            # No specific doctor mentioned - show available doctors
            return self._show_available_doctors(patient)
    
    def handle_appointment_scheduling(self, user_input: str, appointment_info: AppointmentInfo, conversation_history: List[Dict]) -> SchedulingResult:
        """Handle appointment time selection and booking - deterministic, no LLM calls"""
        
        # Check if user input contains booking information
        if "book appointment with" in user_input.lower():
            # Extract date and time from the input
            selected_slot = self._extract_slot_from_booking_input(user_input, appointment_info.doctor)
        else:
            # Try to extract slot selection (number or date/time)
            selected_slot = self._extract_slot_selection(user_input, appointment_info.doctor)
        
        if selected_slot:
            # Validate and book the slot
            booking_result = self._book_appointment_slot(appointment_info, selected_slot)
            
            if booking_result["success"]:
                # Update appointment info
                appointment_info.date = selected_slot["date"]
                appointment_info.time = selected_slot["time"]
                
                # Generate deterministic response with patient type info
                patient_type_text = "returning patient" if appointment_info.patient.patient_type == "Returning" else "new patient"
                response = f"🎉 **Appointment Booked Successfully!**\n\n"
                response += f"👨‍⚕️ **Doctor:** {appointment_info.doctor}\n"
                response += f"📅 **Date:** {selected_slot['date']}\n"
                response += f"🕐 **Time:** {selected_slot['time']}\n"
                response += f"⏱️ **Duration:** {appointment_info.duration} minutes ({patient_type_text})\n\n"
                response += f"✅ Your appointment has been confirmed. You will receive a confirmation email shortly."
                
                return SchedulingResult(
                    success=True,
                    message=response,
                    appointment_info=appointment_info,
                    next_state="completed",
                    available_slots=[]
                )
            else:
                return SchedulingResult(
                    success=False,
                    message=booking_result["message"],
                    appointment_info=appointment_info,
                    next_state="scheduling",
                    available_slots=self._get_available_slots(appointment_info.doctor)
                )
        else:
            # No clear slot selection - show available slots again
            available_slots = self._get_available_slots(appointment_info.doctor)
            response = f"❓ **Please select a time slot for Dr. {appointment_info.doctor}**\n\n"
            response += self._format_available_slots(available_slots, appointment_info.doctor, appointment_info.patient.patient_type)
            
            return SchedulingResult(
                success=False,
                message=response,
                appointment_info=appointment_info,
                next_state="scheduling",
                available_slots=available_slots
            )
    
    def _find_best_doctor_match(self, user_input: str) -> Optional[str]:
        """Find the best matching doctor using fuzzy matching"""
        
        if not user_input or not self.available_doctors:
            return None
        
        user_input_clean = user_input.lower().strip()
        
        # Check if user input is a number (doctor selection by number)
        import re
        numbers = re.findall(r'\d+', user_input_clean)
        if numbers:
            try:
                doctor_number = int(numbers[0])
                recommendations = self.get_doctor_recommendations(PatientInfo())  # Get all recommendations
                if 1 <= doctor_number <= len(recommendations):
                    return recommendations[doctor_number - 1].name
            except (ValueError, IndexError):
                pass
        
        # Remove common prefixes
        prefixes_to_remove = ['dr.', 'dr', 'doctor']
        for prefix in prefixes_to_remove:
            if user_input_clean.startswith(prefix):
                user_input_clean = user_input_clean[len(prefix):].strip()
        
        best_match = None
        best_score = 0
        
        for doctor in self.available_doctors:
            doctor_lower = doctor.lower()
            
            # Calculate fuzzy match score
            score = fuzz.ratio(user_input_clean, doctor_lower)
            
            # Boost score for substring matches
            if user_input_clean in doctor_lower or doctor_lower in user_input_clean:
                score = max(score, 80)
            
            # Check individual name parts
            doctor_parts = doctor_lower.replace('dr.', '').strip().split()
            for part in doctor_parts:
                if part and len(part) > 2:
                    part_score = fuzz.ratio(user_input_clean, part)
                    if part_score > 70:
                        score = max(score, part_score)
            
            # Check first and last name matches
            if len(doctor_parts) >= 2:
                first_name = doctor_parts[0]
                last_name = doctor_parts[-1]
                if user_input_clean == first_name or user_input_clean == last_name:
                    score = max(score, 90)
                
                # Check if user input matches first name (like "kevin" matching "kevin harris")
                if user_input_clean == first_name:
                    score = max(score, 95)
            
            if score > best_score and score > 60:
                best_score = score
                best_match = doctor
        
        return best_match
    
    def _find_exact_doctor_match(self, doctor_name: str) -> Optional[str]:
        """Find exact doctor match for button selections"""
        if not doctor_name or not self.available_doctors:
            return None
        
        # Clean the input
        doctor_name_clean = doctor_name.strip()
        
        # Try exact match first
        for doctor in self.available_doctors:
            if doctor.lower() == doctor_name_clean.lower():
                return doctor
        
        # Try partial match
        for doctor in self.available_doctors:
            if doctor_name_clean.lower() in doctor.lower():
                return doctor
        
        return None
    
    def _extract_slot_from_booking_input(self, user_input: str, doctor: str) -> Optional[Dict[str, Any]]:
        """Extract slot information from booking input like 'Book appointment with Dr. Smith on 2025-01-15 at 10:00'"""
        import re
        
        # Pattern to match date and time
        # Look for patterns like "on 2025-01-15 at 10:00" or "on 2025-01-15 at 10:00:00"
        pattern = r'on\s+(\d{4}-\d{2}-\d{2})\s+at\s+(\d{1,2}:\d{2}(?::\d{2})?)'
        match = re.search(pattern, user_input, re.IGNORECASE)
        
        if match:
            date = match.group(1)
            time = match.group(2)
            
            # Validate that this slot exists and is available
            available_slots = self._get_available_slots(doctor)
            for slot in available_slots:
                if str(slot["date"]) == date and str(slot["time"]) == time:
                    return slot
        
        return None
    
    def _get_available_slots(self, doctor: str) -> List[Dict[str, Any]]:
        """Get available appointment slots for a doctor"""
        
        if self.schedules_db.empty:
            return []
        
        available_slots = self.schedules_db[
            (self.schedules_db["Doctor"] == doctor) & 
            (self.schedules_db["Available"] == "Yes")
        ]
        
        slots = []
        for _, slot in available_slots.iterrows():
            slots.append({
                "date": slot['Date'],
                "time": slot['Time'],
                "doctor": doctor
            })
        
        return slots
    
    def _extract_slot_selection(self, user_input: str, doctor: str) -> Optional[Dict[str, Any]]:
        """Extract slot selection from user input"""
        
        # Try to extract slot number
        import re
        numbers = re.findall(r'\d+', user_input)
        
        if numbers:
            slot_number = int(numbers[0])
            available_slots = self._get_available_slots(doctor)
            
            if 1 <= slot_number <= len(available_slots):
                return available_slots[slot_number - 1]
        
        # Try to extract date and time
        entities = self.gemini.extract_entities(user_input)
        
        if entities.get("appointment_date") and entities.get("appointment_time"):
            # Check if this slot is available
            available_slots = self._get_available_slots(doctor)
            for slot in available_slots:
                if (str(slot["date"]) == entities["appointment_date"] and 
                    str(slot["time"]) == entities["appointment_time"]):
                    return slot
        
        return None
    
    def _book_appointment_slot(self, appointment_info: AppointmentInfo, slot: Dict[str, Any]) -> Dict[str, Any]:
        """Book an appointment slot"""
        
        try:
            # Find the slot in the database
            slot_index = self.schedules_db[
                (self.schedules_db["Doctor"] == appointment_info.doctor) &
                (self.schedules_db["Date"] == slot["date"]) &
                (self.schedules_db["Time"] == slot["time"])
            ].index
            
            if len(slot_index) > 0:
                # Mark slot as unavailable
                self.schedules_db.loc[slot_index[0], "Available"] = "No"
                
                # Save the updated schedule
                try:
                    self.schedules_db.to_excel("data/schedules_new.xlsx", index=False)
                except PermissionError:
                    self.schedules_db.to_excel("data/schedules.xlsx", index=False)
                
                return {"success": True, "message": "Slot booked successfully"}
            else:
                return {"success": False, "message": "Slot not found or no longer available"}
        
        except Exception as e:
            return {"success": False, "message": f"Error booking slot: {str(e)}"}
    
    def _format_available_slots(self, slots: List[Dict[str, Any]], doctor: str, patient_type: str) -> str:
        """Format available slots for display"""
        
        if not slots:
            return f"I'm sorry, but {doctor} doesn't have any available slots at the moment."
        
        # Group slots by date
        slots_by_date = {}
        for slot in slots:
            date = slot['date']
            time = slot['time']
            if date not in slots_by_date:
                slots_by_date[date] = []
            slots_by_date[date].append(time)
        
        # Minimal message with duration info
        duration = 60 if patient_type == "New" else 30
        response = f"📅 **Please select your {duration}-minute appointment time below:**"
        
        return response
    
    def get_doctor_recommendations(self, patient_info: PatientInfo) -> List[DoctorInfo]:
        """Get doctor recommendations based on patient info"""
        
        recommendations = []
        for doctor in self.available_doctors:
            available_slots = self._get_available_slots(doctor)
            if available_slots:
                recommendations.append(DoctorInfo(
                    name=doctor,
                    specialty="General Practice",  # This could be enhanced with actual specialty data
                    available_slots=available_slots
                ))
        
        return recommendations
    
    def _show_available_doctors(self, patient: PatientInfo) -> SchedulingResult:
        """Show available doctors for selection"""
        
        if not self.available_doctors:
            return SchedulingResult(
                success=False,
                message="I'm sorry, but there are no doctors available at the moment. Please try again later.",
                appointment_info=None,
                next_state="doctor_selection",
                available_slots=[]
            )
        
        # Get doctor recommendations with available slots
        recommendations = self.get_doctor_recommendations(patient)
        
        if not recommendations:
            return SchedulingResult(
                success=False,
                message="I'm sorry, but none of our doctors have available slots at the moment. Please try again later.",
                appointment_info=None,
                next_state="doctor_selection",
                available_slots=[]
            )
        
        # Minimal message - just indicate selection is ready
        response = f"👨‍⚕️ **Please select your doctor below:**"
        
        return SchedulingResult(
            success=False,
            message=response,
            appointment_info=None,
            next_state="doctor_selection",
            available_slots=[]
        )
