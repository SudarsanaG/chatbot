"""
User Management System
Handles user registration, lookup, and storage in CSV
"""

import pandas as pd
import os
from typing import Optional, Dict, Any
from datetime import datetime
from src.agent import PatientInfo

class UserManager:
    """Manages user registration and lookup"""
    
    def __init__(self, csv_path: str = "data/users.csv"):
        self.csv_path = csv_path
        self.users_df = self._load_users()
    
    def _load_users(self) -> pd.DataFrame:
        """Load users from CSV or create new file"""
        if os.path.exists(self.csv_path):
            try:
                return pd.read_csv(self.csv_path)
            except Exception:
                return self._create_empty_users_df()
        else:
            return self._create_empty_users_df()
    
    def _create_empty_users_df(self) -> pd.DataFrame:
        """Create empty users DataFrame"""
        return pd.DataFrame(columns=[
            'user_id', 'first_name', 'last_name', 'date_of_birth', 
            'phone', 'email', 'patient_type', 'registration_date', 
            'last_visit', 'total_appointments'
        ])
    
    def _save_users(self):
        """Save users to CSV"""
        # Only create directory if the path has a directory component
        dir_path = os.path.dirname(self.csv_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        self.users_df.to_csv(self.csv_path, index=False)
    
    def is_returning_user(self, patient_info: PatientInfo) -> bool:
        """Check if user is returning based on name and phone number combination"""
        if not patient_info.first_name or not patient_info.phone:
            return False
        
        # Check by name and phone combination (primary method)
        name_phone_match = (
            (self.users_df['first_name'].str.lower() == patient_info.first_name.lower()) &
            (self.users_df['phone'] == patient_info.phone)
        )
        if name_phone_match.any():
            return True
        
        # Fallback: Check by phone only (if name+phone combo not found)
        if patient_info.phone:
            phone_match = self.users_df['phone'] == patient_info.phone
            if phone_match.any():
                return True
        
        # Fallback: Check by email (if phone not found)
        if patient_info.email:
            email_match = self.users_df['email'] == patient_info.email
            if email_match.any():
                return True
        
        return False
    
    def register_user(self, patient_info: PatientInfo) -> Dict[str, Any]:
        """Register a new user or update existing user"""
        
        # Check if user already exists
        existing_user = self._find_existing_user(patient_info)
        
        if existing_user is not None:
            # Update existing user
            user_id = existing_user['user_id']
            self.users_df.loc[self.users_df['user_id'] == user_id, 'last_visit'] = datetime.now().strftime('%Y-%m-%d')
            self.users_df.loc[self.users_df['user_id'] == user_id, 'total_appointments'] += 1
            patient_type = "Returning"
        else:
            # Create new user
            user_id = self._generate_user_id()
            new_user = {
                'user_id': user_id,
                'first_name': patient_info.first_name,
                'last_name': patient_info.last_name,
                'date_of_birth': patient_info.dob,
                'phone': patient_info.phone,
                'email': patient_info.email,
                'patient_type': "New",
                'registration_date': datetime.now().strftime('%Y-%m-%d'),
                'last_visit': datetime.now().strftime('%Y-%m-%d'),
                'total_appointments': 1
            }
            self.users_df = pd.concat([self.users_df, pd.DataFrame([new_user])], ignore_index=True)
            patient_type = "New"
        
        # Update patient info
        patient_info.patient_id = user_id
        patient_info.patient_type = patient_type
        
        # Save to CSV
        self._save_users()
        
        return {
            'success': True,
            'user_id': user_id,
            'patient_type': patient_type,
            'is_new_user': patient_type == "New"
        }
    
    def _find_existing_user(self, patient_info: PatientInfo) -> Optional[Dict[str, Any]]:
        """Find existing user by name and phone combination, with fallbacks"""
        if not patient_info.first_name and not patient_info.phone and not patient_info.email:
            return None
        
        # Primary: Check by name and phone combination
        if patient_info.first_name and patient_info.phone:
            name_phone_match = (
                (self.users_df['first_name'].str.lower() == patient_info.first_name.lower()) &
                (self.users_df['phone'] == patient_info.phone)
            )
            if name_phone_match.any():
                return self.users_df[name_phone_match].iloc[0].to_dict()
        
        # Fallback: Check by phone only
        if patient_info.phone:
            phone_match = self.users_df['phone'] == patient_info.phone
            if phone_match.any():
                return self.users_df[phone_match].iloc[0].to_dict()
        
        # Fallback: Check by email
        if patient_info.email:
            email_match = self.users_df['email'] == patient_info.email
            if email_match.any():
                return self.users_df[email_match].iloc[0].to_dict()
        
        return None
    
    def _generate_user_id(self) -> str:
        """Generate unique user ID"""
        if self.users_df.empty:
            return "USER_001"
        
        # Get the highest user ID number
        user_ids = self.users_df['user_id'].str.extract(r'USER_(\d+)')[0].astype(int)
        next_id = user_ids.max() + 1 if not user_ids.empty else 1
        return f"USER_{next_id:03d}"
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information by ID"""
        user_match = self.users_df['user_id'] == user_id
        if user_match.any():
            return self.users_df[user_match].iloc[0].to_dict()
        return None
    
    def get_all_users(self) -> pd.DataFrame:
        """Get all users"""
        return self.users_df.copy()
    
    def get_user_stats(self) -> Dict[str, int]:
        """Get user statistics"""
        if self.users_df.empty:
            return {'total_users': 0, 'new_users': 0, 'returning_users': 0}
        
        return {
            'total_users': len(self.users_df),
            'new_users': len(self.users_df[self.users_df['patient_type'] == 'New']),
            'returning_users': len(self.users_df[self.users_df['patient_type'] == 'Returning'])
        }
