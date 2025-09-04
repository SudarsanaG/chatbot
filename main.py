import streamlit as st
import pandas as pd
import os
import datetime
from src.utils import send_intake_form

# Load data
patients_file = "data/patients.csv"
patients = pd.read_csv(patients_file)
schedules = pd.read_excel("data/schedules.xlsx")

st.title("AI Scheduling Agent")

# Step 1: Patient info
st.subheader("Patient Lookup")
name = st.text_input("Enter your first name")
dob = st.date_input(
    "Enter your Date of Birth",
    min_value=datetime.date.today().replace(year=datetime.date.today().year - 100),
    max_value=datetime.date.today()
)
if st.button("Find Patient"):
    match = patients[(patients["FirstName"].str.lower() == name.lower()) &
                     (patients["DOB"] == str(dob))]

    if not match.empty:
        # Existing patient
        st.session_state["patient"] = match.iloc[0].to_dict()
        st.success(f"Welcome back, {name}! You are a Returning patient.")
    else:
        # Mark as new patient (so inputs show below)
        st.session_state["patient_not_found"] = True

# Step 1b: New patient registration (separate from button)
if st.session_state.get("patient_not_found", False) and "patient" not in st.session_state:
    st.subheader("📝 New Patient Registration")

    # persist values across reruns
    if "new_email" not in st.session_state:
        st.session_state["new_email"] = ""
    if "new_phone" not in st.session_state:
        st.session_state["new_phone"] = ""

    st.session_state["new_email"] = st.text_input(
        "Enter your email address", value=st.session_state["new_email"]
    )
    st.session_state["new_phone"] = st.text_input(
        "Enter your phone number", value=st.session_state["new_phone"]
    )

    if st.session_state["new_email"]:  # only register once email is filled
        new_patient = {
            "PatientID": len(patients) + 1,
            "FirstName": name,
            "LastName": "",
            "DOB": str(dob),
            "Phone": st.session_state["new_phone"],
            "Email": st.session_state["new_email"],
            "PatientType": "New"
        }
        st.session_state["patient"] = new_patient
        st.success(f"{name} registered as a New patient with email {st.session_state['new_email']}.")

        # Save new patient to CSV
        patients = pd.concat([patients, pd.DataFrame([new_patient])], ignore_index=True)
        patients.to_csv(patients_file, index=False)

# Step 2: Doctor slot selection
if "patient" in st.session_state:
    st.subheader("Schedule Appointment")
    doctor = st.selectbox("Choose Doctor", schedules["Doctor"].unique())
    available_slots = schedules[(schedules["Doctor"] == doctor) &
                                (schedules["Available"] == "Yes")]

    if not available_slots.empty:
        slot = st.selectbox(
            "Available Slots", 
            [f"{row['Date']} {row['Time']}" for _, row in available_slots.iterrows()]
        )

        if st.button("Confirm Appointment"):
            new_appt = {
                "PatientName": st.session_state["patient"]["FirstName"],
                "DOB": st.session_state["patient"]["DOB"],
                "Doctor": doctor,
                "Slot": slot,
                "Status": "Confirmed"
            }

            # Save appointment
            appt_file = "data/appointments.xlsx"
            if os.path.exists(appt_file):
                appts = pd.read_excel(appt_file)
                appts = pd.concat([appts, pd.DataFrame([new_appt])], ignore_index=True)
            else:
                appts = pd.DataFrame([new_appt])
            appts.to_excel(appt_file, index=False)

            st.success(f"Appointment confirmed for {new_appt['PatientName']} with {doctor} at {slot}. ✅")
            st.info("Saved to appointments.xlsx")

            # Send intake form (simulated)
            email = st.session_state["patient"].get("Email", "test@example.com")
            msg = send_intake_form(email)
            st.info(msg)

            # --------------------
            # 📲 Reminder System
            # --------------------
            st.subheader("📲 Automated Reminders")

            reminders = [
                f"1️⃣ Reminder 1: Dear {new_appt['PatientName']}, you have an appointment with {doctor} at {slot}.",
                f"2️⃣ Reminder 2: Dear {new_appt['PatientName']}, please confirm you have filled the intake form for your appointment with {doctor}.",
                f"3️⃣ Reminder 3: Dear {new_appt['PatientName']}, will you attend this appointment with {doctor} at {slot}? If not, kindly provide the reason for cancellation."
            ]

            for r in reminders:
                st.write(r)
    else:
        st.error("No available slots for this doctor.")
