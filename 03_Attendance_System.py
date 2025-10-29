import face_recognition
import cv2
import numpy as np
import pickle
from datetime import datetime, timedelta
import csv
import os
import sys

# --- Configuration ---
ENCODING_FILE = "face_encodings.pkl" 
LOG_FILE = "Attendance_Log.csv"      
COOLDOWN_SECONDS = 5          # Time to wait before logging the same event again
MINIMUM_GAP_HOURS = 2         # Minimum time gap required for check-out (2 hours)

# Dictionary to track the last time a name was logged/updated
last_log_time = {} 

# --- 1. Load the AI Model and Data ---
try:
    with open(ENCODING_FILE, 'rb') as f:
        data = pickle.load(f)
        known_face_encodings = data["encodings"]
        known_face_names = data["names"]
    print(f"Successfully loaded {len(set(known_face_names))} unique known faces.")
except FileNotFoundError:
    print(f"ERROR: {ENCODING_FILE} not found. Please run 02_Encode_Faces.py first.")
    sys.exit()

# --- 2. Attendance Logging Function (FINAL VERSION) ---
def mark_attendance(name):
    """
    Handles Check-In and Check-Out with Cooldown and Minimum Gap constraints.
    """
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    current_time_str = now.strftime("%H:%M:%S")

    # ------------------ A. DEBOUNCE CHECK ------------------
    # Skip logging if still in cooldown
    if name in last_log_time and (now - last_log_time[name]) < timedelta(seconds=COOLDOWN_SECONDS):
        return
    # ----------------------------------------------------

    # Ensure log file exists with the correct header
    file_exists = os.path.isfile(LOG_FILE)
    if not file_exists:
        with open(LOG_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Date', 'Check_In_Time', 'Check_Out_Time', 'Status']) 
            
    # 1. Read the existing data
    with open(LOG_FILE, 'r') as f:
        reader = csv.reader(f)
        data_list = list(reader)

    header = data_list[0] if data_list else None
    records = data_list[1:]

    # 2. Check for an existing Check-In record today and ATTEMPT to UPDATE it (Check-Out)
    record_updated = False
    new_records = []
    
    for row in records:
        # Check if Name matches AND Date matches AND Check_Out_Time is EMPTY
        if len(row) >= 4 and row[0] == name and row[1] == today_date and row[3] == '':
            
            # --- B. 2-HOUR GAP LOGIC (Check-Out only) ---
            check_in_time_str = row[2]
            check_in_dt = datetime.strptime(f"{today_date} {check_in_time_str}", "%Y-%m-%d %H:%M:%S")
            time_difference = now - check_in_dt
            required_gap = timedelta(hours=MINIMUM_GAP_HOURS)
            
            if time_difference >= required_gap:
                # Condition met: Perform the Check-Out update
                row[3] = current_time_str
                row[4] = 'Checked Out'
                print(f"ATTENDANCE UPDATED (CHECK-OUT): {name} at {current_time_str}. Gap met!")
                record_updated = True
            else:
                # Condition NOT met: Print message and skip update
                print(f"⚠️ Check-Out skipped for {name}: Must wait {MINIMUM_GAP_HOURS}h since check-in. Elapsed: {str(time_difference).split('.')[0]}")
            # --- END 2-HOUR GAP LOGIC ---
            
        new_records.append(row)

    # 3. If no record was updated (i.e., First Check-In of the day OR Check-Out failed the gap rule)
    if not record_updated:
        # Check if a Check-In already exists for today (we should only create a new record if NO record exists)
        already_checked_in = any(row[0] == name and row[1] == today_date for row in records)
        
        if not already_checked_in:
            # Create a new Check-In record: Name, Date, Check-In, Check-Out (empty), Status
            new_records.append([name, today_date, current_time_str, '', 'Checked In'])
            print(f"ATTENDANCE MARKED (CHECK-IN): {name} at {current_time_str}")

    # 4. Rewrite the entire CSV file with updated records
    with open(LOG_FILE, 'w', newline='') as f_write:
        writer = csv.writer(f_write)
        if header:
            writer.writerow(header)
        writer.writerows(new_records)
        
    # Reset the cooldown timer after a successful attempt (log or skip due to gap)
    last_log_time[name] = now


# --- 3. Real-Time Recognition Loop ---
video_capture = cv2.VideoCapture(0) # Index 0. If this fails, try 1 or 2.

# **CRITICAL FIX: CHECK IF CAMERA OPENED**
if not video_capture.isOpened():
    print("FATAL ERROR: Could not open camera. Check if another application is using it, or try index 1.")
    sys.exit()

face_locations = []
face_encodings = []
face_names = []
process_this_frame = True 

print("\n--- Starting Real-Time Attendance System. Press 'q' to quit. ---")

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    if process_this_frame:
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                mark_attendance(name)

            face_names.append(name)

    process_this_frame = not process_this_frame 

    # --- 4. Display Results on Video Stream ---
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        color = (0, 255, 0) # Default green
        if name == "Unknown":
            color = (0, 0, 255) # Red for Unknown
        elif name in last_log_time:
            # Simple visual feedback to show recognition is working
            color = (255, 165, 0) # Orange if currently in cooldown

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    cv2.imshow('AI Attendance Scanner', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()