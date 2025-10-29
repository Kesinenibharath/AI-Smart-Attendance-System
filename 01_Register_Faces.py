import cv2
import os
import sys

# --- Configuration ---
OUTPUT_DIR = "Registered_Faces"
NUM_IMAGES = 30 # Number of images to capture
START_KEY = ord('s') 
QUIT_KEY = ord('q')
# ---

# --- 1. Get Admin Input ---
print("\n--- AI Attendance System: Face Registration Tool ---")

# Prompt for Name
person_name = input("Enter the full name of the person (e.g., John Doe): ").strip()
if not person_name:
    print("Name cannot be empty. Exiting.")
    sys.exit()

# Prompt for Registered Number/ID
reg_number = input("Enter the Registered Number/ID (e.g., 101): ").strip()
if not reg_number:
    print("Registered Number cannot be empty. Exiting.")
    sys.exit()

# Create a unique identifier for the filename (e.g., "John_Doe_101")
PERSON_ID = f"{person_name.replace(' ', '_')}_{reg_number}" 

# --- 2. Setup ---
# Create the output directory if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"Created directory: {OUTPUT_DIR}")

# Try to find an available camera
def find_working_camera():
    for i in range(3):  # Try first 3 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"Successfully connected to camera {i}")
                return cap
            cap.release()
    return None

# Initialize the webcam
cap = find_working_camera()
if cap is None:
    print("Error: Could not find any working camera. Please check:")
    print("1. Camera is properly connected")
    print("2. Camera is not being used by another application")
    print("3. Camera permissions are granted")
    sys.exit()

print(f"\nTargeting: {person_name} (ID: {reg_number})")
print(f"Instructions: Press the '{chr(START_KEY)}' key to START capturing {NUM_IMAGES} images.")

count = 0
capturing = False

# --- 3. Camera Loop for Capture ---
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1) # Mirror the frame for intuitive use

    # Prepare status text for display
    status_text = f"STATUS: Press '{chr(START_KEY)}' to START"
    if capturing:
        status_text = f"CAPTURING... ({count}/{NUM_IMAGES})"
    
    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(frame, f"Name/ID: {person_name} / {reg_number}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    cv2.imshow('Face Registration Tool - Press Q to Exit', frame)

    key = cv2.waitKey(1) & 0xFF

    if key == START_KEY:
        capturing = True
        print("Starting capture...")
        
    if capturing and count < NUM_IMAGES:
        # Save image using the combined ID (e.g., John_Doe_101_0.jpg)
        img_name = f"{PERSON_ID}_{count}.jpg"
        img_path = os.path.join(OUTPUT_DIR, img_name)
        cv2.imwrite(img_path, frame)
        print(f"Image saved: {img_name}")
        count += 1
        cv2.waitKey(200) # Small delay to capture different poses
        
    if count >= NUM_IMAGES:
        capturing = False
        print(f"\nSuccessfully captured {NUM_IMAGES} images for {person_name}.")
        break
    
    # Break the loop on 'q' press
    if key == QUIT_KEY:
        print("Exiting tool.")
        break

# Release the camera and close all windows
cap.release()
cv2.destroyAllWindows()