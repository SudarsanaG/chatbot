"""
Patient Management Agent
Specializes in patient lookup, registration, and database management
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd
from src.gemini_client import GeminiClient
from src.agent import PatientInfo
from fuzzywuzzy import fuzz

@dataclass
class PatientLookupResult:
    """Result of patient lookup operation"""
    found: bool
    patient: Optional[PatientInfo]
    message: str
    next_state: str

@dataclass
class RegistrationResult:
    """Result of patient registration operation"""
    success: bool
    patient: PatientInfo
    message: str
    next_state: str

class PatientManagementAgent:
    """Agent responsible for patient database management"""
    
    def __init__(self, gemini_client: GeminiClient, patients_db: pd.DataFrame):
        self.gemini = gemini_client
        self.patients_db = patients_db
    
    def lookup_patient(self, patient_info: PatientInfo, conversation_history: List[Dict]) -> PatientLookupResult:
        """Look up patient in the database"""
        
        if self.patients_db.empty:
            return PatientLookupResult(
                found=False,
                patient=None,
                message=f"I don't see you in our system, {patient_info.first_name}. Let me register you as a new patient.",
                next_state="new_patient_registration"
            )
        
        # Search for patient using fuzzy matching
        best_match = None
        best_score = 0
        
        for _, db_patient in self.patients_db.iterrows():
            # Calculate name similarity
            name_score = fuzz.ratio(
                patient_info.first_name.lower(),
                str(db_patient["FirstName"]).lower()
            )
            
            # Check if last name matches (if provided)
            last_name_match = True
            if patient_info.last_name:
                last_name_score = fuzz.ratio(
                    patient_info.last_name.lower(),
                    str(db_patient.get("LastName", "")).lower()
                )
                last_name_match = last_name_score > 80
            
            # Check date of birth match (if provided)
            dob_match = True
            if patient_info.dob:
                dob_match = str(db_patient["DOB"]) == patient_info.dob
            
            # Calculate overall score
            if name_score > 80 and last_name_match and dob_match:
                if name_score > best_score:
                    best_score = name_score
                    best_match = db_patient
        
        if best_match is not None:
            # Found existing patient
            found_patient = PatientInfo(
                first_name=best_match["FirstName"],
                last_name=best_match.get("LastName", ""),
                dob=str(best_match["DOB"]),
                phone=str(best_match.get("Phone", "")),
                email=best_match.get("Email", ""),
                patient_type="Returning",
                patient_id=best_match["PatientID"]
            )
            
            context = f"Found returning patient: {found_patient.first_name} {found_patient.last_name}"
            response = self.gemini.generate_response(
                f"Found patient {found_patient.first_name}", 
                context, 
                "patient_manager"
            )
            
            if not response or len(response) < 20:
                response = f"Welcome back, {found_patient.first_name}! I found you in our system as a returning patient."
            
            return PatientLookupResult(
                found=True,
                patient=found_patient,
                message=response,
                next_state="doctor_selection"
            )
        else:
            # Patient not found
            context = f"Patient not found: {patient_info.first_name} {patient_info.last_name}"
            response = self.gemini.generate_response(
                f"Patient {patient_info.first_name} not found", 
                context, 
                "patient_manager"
            )
            
            if not response or len(response) < 20:
                response = f"I don't see you in our system, {patient_info.first_name}. Let me register you as a new patient."
            
            return PatientLookupResult(
                found=False,
                patient=patient_info,
                message=response,
                next_state="new_patient_registration"
            )
    
    def register_new_patient(self, patient_info: PatientInfo, conversation_history: List[Dict]) -> RegistrationResult:
        """Register a new patient in the database"""
        
        # Validate that we have all required information
        required_fields = ["first_name", "last_name", "dob", "phone", "email"]
        missing_fields = []
        
        for field in required_fields:
            if not getattr(patient_info, field, None):
                missing_fields.append(field)
        
        if missing_fields:
            # Still need more information
            field_display_names = {
                "first_name": "first name",
                "last_name": "last name",
                "dob": "date of birth",
                "phone": "phone number",
                "email": "email address"
            }
            
            missing_display = [field_display_names.get(field, field) for field in missing_fields]
            
            context = f"Missing patient information: {', '.join(missing_display)}"
            response = self.gemini.generate_response(
                f"Need {', '.join(missing_display)}", 
                context, 
                "patient_manager"
            )
            
            if not response or len(response) < 20:
                response = f"To complete your registration, I need your {' and '.join(missing_display)}."
            
            return RegistrationResult(
                success=False,
                patient=patient_info,
                message=response,
                next_state="new_patient_registration"
            )
        
        # Generate new patient ID
        new_patient_id = self._generate_patient_id()
        patient_info.patient_id = new_patient_id
        patient_info.patient_type = "New"
        
        # Create new patient record
        new_patient_row = {
            "PatientID": new_patient_id,
            "FirstName": patient_info.first_name,
            "LastName": patient_info.last_name,
            "DOB": patient_info.dob,
            "Phone": patient_info.phone,
            "Email": patient_info.email,
            "PatientType": patient_info.patient_type,
            "RegistrationDate": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to database
        try:
            new_patient_df = pd.DataFrame([new_patient_row])
            self.patients_db = pd.concat([self.patients_db, new_patient_df], ignore_index=True)
            self.patients_db.to_csv("data/patients.csv", index=False)
            
            context = f"Successfully registered new patient: {patient_info.first_name} {patient_info.last_name}"
            response = self.gemini.generate_response(
                f"Registered {patient_info.first_name}", 
                context, 
                "patient_manager"
            )
            
            if not response or len(response) < 20:
                response = f"Perfect! You're now registered, {patient_info.first_name}. Let's proceed with scheduling your appointment."
            
            return RegistrationResult(
                success=True,
                patient=patient_info,
                message=response,
                next_state="doctor_selection"
            )
            
        except Exception as e:
            error_message = f"I encountered an error while registering you: {str(e)}. Please try again."
            return RegistrationResult(
                success=False,
                patient=patient_info,
                message=error_message,
                next_state="new_patient_registration"
            )
    
    def update_patient_info(self, patient_id: int, updates: Dict[str, Any]) -> bool:
        """Update existing patient information"""
        
        try:
            # Find patient in database
            patient_mask = self.patients_db["PatientID"] == patient_id
            if not patient_mask.any():
                return False
            
            # Update fields
            for field, value in updates.items():
                if field in self.patients_db.columns:
                    self.patients_db.loc[patient_mask, field] = value
            
            # Save updated database
            self.patients_db.to_csv("data/patients.csv", index=False)
            return True
            
        except Exception as e:
            print(f"Error updating patient info: {e}")
            return False
    
    def get_patient_by_id(self, patient_id: int) -> Optional[PatientInfo]:
        """Get patient information by ID"""
        
        try:
            patient_row = self.patients_db[self.patients_db["PatientID"] == patient_id]
            if patient_row.empty:
                return None
            
            patient_data = patient_row.iloc[0]
            return PatientInfo(
                first_name=patient_data["FirstName"],
                last_name=patient_data.get("LastName", ""),
                dob=str(patient_data["DOB"]),
                phone=str(patient_data.get("Phone", "")),
                email=patient_data.get("Email", ""),
                patient_type=patient_data.get("PatientType", "New"),
                patient_id=patient_data["PatientID"]
            )
            
        except Exception as e:
            print(f"Error getting patient by ID: {e}")
            return None
    
    def search_patients(self, search_term: str) -> List[PatientInfo]:
        """Search for patients by name or other criteria"""
        
        results = []
        if self.patients_db.empty:
            return results
        
        search_term_lower = search_term.lower()
        
        for _, patient_row in self.patients_db.iterrows():
            # Search in first name, last name, and email
            first_name = str(patient_row["FirstName"]).lower()
            last_name = str(patient_row.get("LastName", "")).lower()
            email = str(patient_row.get("Email", "")).lower()
            
            if (search_term_lower in first_name or 
                search_term_lower in last_name or 
                search_term_lower in email):
                
                patient_info = PatientInfo(
                    first_name=patient_row["FirstName"],
                    last_name=patient_row.get("LastName", ""),
                    dob=str(patient_row["DOB"]),
                    phone=str(patient_row.get("Phone", "")),
                    email=patient_row.get("Email", ""),
                    patient_type=patient_row.get("PatientType", "New"),
                    patient_id=patient_row["PatientID"]
                )
                results.append(patient_info)
        
        return results
    
    def _generate_patient_id(self) -> int:
        """Generate a new unique patient ID"""
        
        if self.patients_db.empty:
            return 1
        
        max_id = self.patients_db["PatientID"].max()
        return int(max_id) + 1
    
    def get_patient_statistics(self) -> Dict[str, Any]:
        """Get patient database statistics"""
        
        if self.patients_db.empty:
            return {
                "total_patients": 0,
                "new_patients": 0,
                "returning_patients": 0
            }
        
        total_patients = len(self.patients_db)
        new_patients = len(self.patients_db[self.patients_db.get("PatientType", "New") == "New"])
        returning_patients = len(self.patients_db[self.patients_db.get("PatientType", "New") == "Returning"])
        
        return {
            "total_patients": total_patients,
            "new_patients": new_patients,
            "returning_patients": returning_patients
        }
