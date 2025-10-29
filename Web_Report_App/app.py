from flask import Flask, render_template
import pandas as pd
import os
from datetime import datetime, timedelta
import threading
import webbrowser
import sys

app = Flask(__name__)

# NOTE: The path points to the Attendance_Log.csv file in the parent directory
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Attendance_Log.csv')

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

# --- NEW FUNCTION: Calculate Work Time ---
def calculate_work_time(row):
    """Calculates the time difference between Check_Out_Time and Check_In_Time."""
    check_in_str = row['Check_In_Time']
    check_out_str = row['Check_Out_Time']
    date_str = row['Date']

    # Only calculate if both times are present
    if check_in_str and check_out_str:
        try:
            # Combine Date and Time strings into datetime objects
            check_in_dt = datetime.strptime(f"{date_str} {check_in_str}", "%Y-%m-%d %H:%M:%S")
            check_out_dt = datetime.strptime(f"{date_str} {check_out_str}", "%Y-%m-%d %H:%M:%S")

            # Calculate the timedelta
            time_diff = check_out_dt - check_in_dt
            
            # Format the difference into a readable H:MM:SS string
            total_seconds = int(time_diff.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            return f"{hours}h {minutes:02}m {seconds:02}s"

        except ValueError:
            return "Error"
    
    # Return a blank or "N/A" string if Check-Out is missing
    return ""
# --- END NEW FUNCTION ---

@app.route('/')
def index():
    try:
        df = pd.read_csv(CSV_PATH)

        # CRITICAL CHECK: Ensure the required columns exist
        required_cols = ['Name', 'Date', 'Check_In_Time', 'Check_Out_Time', 'Status']
        if not all(col in df.columns for col in required_cols):
             return "Error: CSV file columns are incorrect. Please delete Attendance_Log.csv and run 03_Attendance_System.py again.", 500

        # --- NEW STEP: APPLY Work Time Calculation ---
        df['Total_Work_Time'] = df.apply(calculate_work_time, axis=1)
        # ----------------------------------------------

        # Sort data
        df = df.sort_values(by=['Date', 'Check_In_Time'], ascending=[False, False])
        
        # Fill any NaN (Not a Number) values that pandas introduces with empty strings
        df = df.fillna('')

        # Convert the DataFrame to a list of dictionaries for the HTML template
        records = df.to_dict('records') 
        
        current_time = datetime.now().strftime("%H:%M:%S")
        
        return render_template('index.html', attendance_records=records, current_time=current_time)
        
    except FileNotFoundError:
        return "Attendance Log file not found. Run the 03_Attendance_System.py script first!", 404
    except Exception as e:
        print(f"FATAL FLASK ERROR: {e}")
        return f"An internal server error occurred: {e}", 500

if __name__ == '__main__':
    threading.Timer(1.0, open_browser).start()
    app.run(debug=True, port=5000)