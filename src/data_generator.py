"""
Data Generator for Medical Scheduling Agent
Creates synthetic patient data and doctor schedules for testing
"""

import pandas as pd
import random
import datetime
from typing import List, Dict
import os

class MedicalDataGenerator:
    """Generate synthetic medical data for testing"""
    
    def __init__(self):
        self.first_names = [
            "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Jessica",
            "William", "Ashley", "James", "Amanda", "Christopher", "Jennifer", "Daniel",
            "Lisa", "Matthew", "Nancy", "Anthony", "Karen", "Mark", "Betty", "Donald",
            "Helen", "Steven", "Sandra", "Paul", "Donna", "Andrew", "Carol", "Joshua",
            "Ruth", "Kenneth", "Sharon", "Kevin", "Michelle", "Brian", "Laura", "George",
            "Sarah", "Edward", "Kimberly", "Ronald", "Deborah", "Timothy", "Dorothy",
            "Jason", "Amy", "Jeffrey", "Angela", "Ryan", "Brenda", "Jacob", "Emma",
            "Gary", "Olivia", "Nicholas", "Cynthia", "Eric", "Marie", "Jonathan", "Janet"
        ]
        
        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
            "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
            "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
            "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
            "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
            "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy"
        ]
        
        self.doctors = [
            "Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Rodriguez", "Dr. David Kim",
            "Dr. Lisa Thompson", "Dr. Robert Martinez", "Dr. Jennifer Lee", "Dr. Christopher Brown",
            "Dr. Amanda Wilson", "Dr. Daniel Garcia", "Dr. Jessica Davis", "Dr. Matthew Taylor",
            "Dr. Ashley Anderson", "Dr. Joshua Thomas", "Dr. Michelle White", "Dr. Kevin Harris"
        ]
        
        self.insurance_carriers = [
            "Blue Cross Blue Shield", "Aetna", "Cigna", "Humana", "Kaiser Permanente",
            "UnitedHealth", "Medicare", "Medicaid", "Anthem", "Molina Healthcare"
        ]
    
    def generate_patients(self, count: int = 50) -> pd.DataFrame:
        """Generate synthetic patient data"""
        patients = []
        
        for i in range(count):
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            
            # Generate realistic DOB (ages 18-80)
            birth_year = random.randint(1944, 2006)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)  # Safe day for all months
            dob = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
            
            # Generate phone number
            phone = f"555{random.randint(1000000, 9999999)}"
            
            # Generate email
            email = f"{first_name.lower()}.{last_name.lower()}@example.com"
            
            # Determine patient type (70% returning, 30% new)
            patient_type = "Returning" if random.random() < 0.7 else "New"
            
            patient = {
                "PatientID": i + 1,
                "FirstName": first_name,
                "LastName": last_name,
                "DOB": dob,
                "Phone": phone,
                "Email": email,
                "PatientType": patient_type
            }
            patients.append(patient)
        
        return pd.DataFrame(patients)
    
    def generate_schedules(self, days_ahead: int = 30) -> pd.DataFrame:
        """Generate doctor schedules for the next N days"""
        schedules = []
        start_date = datetime.date.today()
        
        # Generate schedules for each doctor
        for doctor in self.doctors:
            # Each doctor works 5 days a week (Monday-Friday)
            for day_offset in range(days_ahead):
                current_date = start_date + datetime.timedelta(days=day_offset)
                
                # Skip weekends
                if current_date.weekday() >= 5:
                    continue
                
                # Generate time slots (9 AM to 5 PM, 30-minute intervals)
                time_slots = [
                    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                    "12:00", "12:30", "13:00", "13:30", "14:00", "14:30",
                    "15:00", "15:30", "16:00", "16:30", "17:00"
                ]
                
                # Randomly make some slots unavailable (20% chance)
                for time_slot in time_slots:
                    available = "Yes" if random.random() > 0.2 else "No"
                    
                    schedule = {
                        "Doctor": doctor,
                        "Date": current_date.strftime("%Y-%m-%d"),
                        "Time": time_slot,
                        "Available": available
                    }
                    schedules.append(schedule)
        
        return pd.DataFrame(schedules)
    
    def generate_sample_appointments(self, count: int = 10) -> pd.DataFrame:
        """Generate sample appointments for testing"""
        appointments = []
        
        for i in range(count):
            # Random patient info
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            doctor = random.choice(self.doctors)
            
            # Random date in the future
            appointment_date = datetime.date.today() + datetime.timedelta(days=random.randint(1, 30))
            
            # Random time
            time_slots = ["09:00", "10:30", "14:00", "15:30"]
            appointment_time = random.choice(time_slots)
            
            # Random patient type
            patient_type = random.choice(["New", "Returning"])
            duration = 60 if patient_type == "New" else 30
            
            appointment = {
                "PatientName": f"{first_name} {last_name}",
                "DOB": f"{random.randint(1950, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "Phone": f"555{random.randint(1000000, 9999999)}",
                "Email": f"{first_name.lower()}.{last_name.lower()}@example.com",
                "Doctor": doctor,
                "Date": appointment_date.strftime("%Y-%m-%d"),
                "Time": appointment_time,
                "Duration": duration,
                "PatientType": patient_type,
                "InsuranceCarrier": random.choice(self.insurance_carriers),
                "MemberID": f"ID{random.randint(100000, 999999)}",
                "GroupNumber": f"GRP{random.randint(1000, 9999)}",
                "Status": "Confirmed",
                "CreatedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            appointments.append(appointment)
        
        return pd.DataFrame(appointments)
    
    def create_data_files(self):
        """Create all data files with synthetic data"""
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Generate and save patients
        patients_df = self.generate_patients(50)
        patients_df.to_csv("data/patients.csv", index=False)
        print(f"✅ Generated {len(patients_df)} patients in data/patients.csv")
        
        # Generate and save schedules
        schedules_df = self.generate_schedules(30)
        try:
            schedules_df.to_excel("data/schedules.xlsx", index=False)
            print(f"✅ Generated {len(schedules_df)} schedule entries in data/schedules.xlsx")
        except PermissionError:
            # If file is locked, create a backup version
            schedules_df.to_excel("data/schedules_new.xlsx", index=False)
            print(f"✅ Generated {len(schedules_df)} schedule entries in data/schedules_new.xlsx (original file was locked)")
        
        # Generate and save sample appointments
        appointments_df = self.generate_sample_appointments(10)
        appointments_df.to_excel("data/appointments.xlsx", index=False)
        print(f"✅ Generated {len(appointments_df)} sample appointments in data/appointments.xlsx")
        
        return {
            "patients": patients_df,
            "schedules": schedules_df,
            "appointments": appointments_df
        }

if __name__ == "__main__":
    generator = MedicalDataGenerator()
    data = generator.create_data_files()
    print("\n🎉 All synthetic data files created successfully!")
