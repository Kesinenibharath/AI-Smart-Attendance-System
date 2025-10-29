import face_recognition
import numpy as np
import os
import pickle

# --- Configuration ---
FACES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Registered_Faces")
ENCODING_FILE = "face_encodings.pkl" 

known_face_encodings = []
known_face_names = []

print(f"Starting face encoding process from {FACES_DIR}...")

for filename in os.listdir(FACES_DIR):
    if filename.endswith((".jpg", ".jpeg", ".png")):
        
        # Name is extracted from the first part of the filename
        name = filename.split("_")[0] 
        image_path = os.path.join(FACES_DIR, filename)
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        
        if encodings:
            face_encoding = encodings[0]
            known_face_encodings.append(face_encoding)
            known_face_names.append(name)
            print(f"Encoded face for: {name} from {filename}")
        else:
            print(f"Warning: Could not find a face in {filename}. Skipping.")

# --- Save Encodings ---
data = {
    "encodings": known_face_encodings,
    "names": known_face_names
}

with open(ENCODING_FILE, 'wb') as f:
    pickle.dump(data, f)

print("\n--- Encoding Complete! ---")
print(f"Total unique names encoded: {len(set(known_face_names))}")
print(f"Saved encodings to: {ENCODING_FILE}")