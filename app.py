import os
import cv2
import dlib
import pickle
import numpy as np
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, request, render_template, redirect, url_for, session, send_file
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Path to save pickle files and photos
STUDENT_DATA_PATH = 'student_data/'
PICKLE_FILE = os.path.join(STUDENT_DATA_PATH, 'encodings.pkl')

# Ensure student data path exists
if not os.path.exists(STUDENT_DATA_PATH):
    os.makedirs(STUDENT_DATA_PATH)

# Ensure the pickle file exists
if not os.path.exists(PICKLE_FILE):
    with open(PICKLE_FILE, 'wb') as f:
        pass  # Create an empty pickle file if it doesn't exist yet

# Load face detection and face recognition models
face_detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
face_recognizer = dlib.face_recognition_model_v1('dlib_face_recognition_resnet_model_v1.dat')

# Initial credentials (username: 1AM22CI, password: CI@2024)
credentials = {"1AM22CI": generate_password_hash("CI@2024")}

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Path to your service account file
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)

def load_all_students():
    """Load all students from the pickle file."""
    students = []
    try:
        with open(PICKLE_FILE, 'rb') as f:
            while True:
                try:
                    student = pickle.load(f)
                    students.append(student)
                except EOFError:
                    break
    except FileNotFoundError:
        pass
    return students


@app.route('/', methods=['GET'])
def index():
    """Render the starting page (index.html)."""
    return render_template('index.html')

@app.route('/logout')
def logout():
    """Log out the user by clearing the session and redirecting to login page."""
    session.pop('user', None)  # Remove the user from the session
    session.pop('semester', None)  # Clear the semester, section, and subject data as well
    session.pop('section', None)
    session.pop('subject', None)
    return redirect(url_for('login'))  # Redirect to login page

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in credentials and check_password_hash(credentials[username], password):
            session['user'] = username
            return redirect(url_for('choose_semester'))
        else:
            return "Invalid credentials. Please try again."
    return render_template('login.html')

@app.route('/choose_semester', methods=['GET', 'POST'])
def choose_semester():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    semesters = [str(i) for i in range(1, 9)]  # Semesters 1 to 8
    sections = ['A', 'B', 'C', 'D', 'E', 'F', 'G']  # Sections A to G
    if request.method == 'POST':
        semester = request.form['semester']
        section = request.form['section']
        subject = request.form['subject']
        
        # Set session variables for semester, section, and subject
        session['semester'] = semester
        session['section'] = section
        session['subject'] = subject
        
        return redirect(url_for('options_page'))  # Redirect to options page
    
    return render_template('choose_semester.html', semesters=semesters, sections=sections)

@app.route('/options_page', methods=['GET'])
def options_page():
    """Display the options page."""
    semester = session.get('semester', 'Not Set')
    section = session.get('section', 'Not Set')
    subject = session.get('subject', 'Not Set')
    
    return render_template('options_page.html', semester=semester, section=section, subject=subject)

@app.route('/enroll', methods=['GET', 'POST'])
def enroll():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        usn = request.form['usn']
        semester = session.get('semester', 'Not Set')
        section = session.get('section', 'Not Set')
        files = request.files.getlist('photos')
        encodings = []
        
        # Process each photo and extract face encodings
        for file in files:
            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_detector(gray)
            
            for face in faces:
                shape = shape_predictor(gray, face)
                face_encoding = np.array(face_recognizer.compute_face_descriptor(img, shape))
                encodings.append(face_encoding)
        
        if encodings:
            # Load existing students from pickle
            existing_students = load_all_students()
            student_exists = False
            
            # Check if student already exists in the pickle file
            for student in existing_students:
                if student['usn'] == usn:
                    student['name'] = name  # Update the student's name
                    student['encodings'] = encodings  # Update the face encodings
                    student['semester'] = semester  # Update semester
                    student['section'] = section  # Update section
                    student_exists = True
                    break
            
            # If student doesn't exist, add new entry
            if not student_exists:
                existing_students.append({"name": name, "usn": usn, "encodings": encodings, "semester": semester, "section": section})
            
            # Save all students back to pickle file
            with open(PICKLE_FILE, 'wb') as f:
                for student in existing_students:
                    pickle.dump(student, f)
            
            message = f"Student {'updated' if student_exists else 'enrolled'} successfully."
        else:
            message = "No face detected in the images."
        
        return render_template('enroll_success.html', message=message)
    
    return render_template('enroll.html')


@app.route('/take_attendance', methods=['GET', 'POST'])
def take_attendance():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        subject = session.get('subject', 'default')
        section = session.get('section', 'A')
        semester = session.get('semester', '1')  # Get semester from session
        sheet_id = get_google_sheet_id(subject, section, semester)
        
        if not sheet_id:
            sheet_id = create_google_sheet(subject, section, semester)
        
        # Modify file naming to include semester
        attendance_file = f"attendance_{semester}_{subject}_{section}.txt"  # Include semester
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if 'class_images' not in request.files:
            return "No files part", 400  # Handle missing files
        
        files = request.files.getlist('class_images')
        
        if not files:
            return "No selected files", 400  # Handle no file selected
        
        present_students = set()  # Use set to avoid duplicates
        
        # Process each file
        for file in files:
            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_detector(gray)
            
            for face in faces:
                shape = shape_predictor(gray, face)
                face_encoding = np.array(face_recognizer.compute_face_descriptor(img, shape))
                
                # Compare this face with all enrolled students
                with open(PICKLE_FILE, 'rb') as f:
                    while True:
                        try:
                            student = pickle.load(f)
                            
                            # Only consider students from the current semester and section
                            if student['semester'] == semester and student['section'] == section:
                                matches = [np.linalg.norm(face_encoding - enc) < 0.6 for enc in student['encodings']]
                                if any(matches):
                                    present_students.add((student['name'], student['usn']))  # Add student to set
                                    break
                        except EOFError:
                            break
        
        # Load all students to get the absent students
        absent_students = [(student['name'], student['usn']) for student in load_all_students() if (student['name'], student['usn']) not in present_students and student['semester'] == semester and student['section'] == section]
        
        # Update attendance in Google Sheets
        update_attendance_in_sheet(sheet_id, list(present_students), absent_students, timestamp)
        
        # Save attendance in text file
        with open(attendance_file, 'a') as report:
            report.write(f"\n--- Attendance Session: {timestamp} ---\n")
            report.write("Present Students:\n")
            report.writelines(f"{name} ({usn})\n" for name, usn in present_students)
            report.write("\nAbsent Students:\n")
            report.writelines(f"{name} ({usn})\n" for name, usn in absent_students)
        
        return f"Attendance taken for {semester} {subject} ({section}). Report saved as {attendance_file}. View Sheet: https://docs.google.com/spreadsheets/d/{sheet_id}/edit?usp=sharing"
    
    return render_template('take_attendance.html')


@app.route('/attendance_statistics')
def attendance_statistics():
    return render_template('attendance_statistics.html')

def get_google_sheet_id(subject, section, semester):
    """Retrieve the Google Sheet ID for the given semester, subject, and section."""
    sheet_id_file = f'{subject}_{section}_{semester}_sheet_id.txt'  # Include semester in the file name
    if os.path.exists(sheet_id_file):
        with open(sheet_id_file, 'r') as file:
            sheet_id = file.read().strip()
        
        # Verify if the sheet exists by making a request to read the sheet's metadata
        try:
            sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            return sheet_id  # Sheet exists, return the ID
        except HttpError as e:
            if e.resp.status == 404:
                print(f"Sheet with ID {sheet_id} not found. Creating a new sheet...")
                return create_google_sheet(subject, section, semester)
            else:
                raise  # Reraise the exception for other HTTP errors
    else:
        print("Sheet ID file not found. Creating a new sheet...")
        return create_google_sheet(subject, section, semester)

def create_google_sheet(subject, section, semester):
    """Create a new Google Sheet and save its ID."""
    try:
        spreadsheet = {
            'properties': {'title': f'Attendance_{semester}_{subject}_{section}'},  # Include semester
            'sheets': [
                {'properties': {'title': 'Present'}},
                {'properties': {'title': 'Absent'}}
            ]
        }
        # Create the sheet
        sheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()
        sheet_id = sheet['spreadsheetId']
        
        # Save the sheet ID to a file for future use
        with open(f'{subject}_{section}_{semester}_sheet_id.txt', 'w') as file:
            file.write(sheet_id)
        
        # Make the sheet viewable by anyone with the link (view only)
        drive_service.permissions().create(
            fileId=sheet_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        return sheet_id
    except HttpError as err:
        print(f"Error creating or sharing the sheet: {err}")
        return None

def update_attendance_in_sheet(sheet_id, present_students, absent_students, timestamp):
    range_present = 'Present!A1'
    range_absent = 'Absent!A1'
    values_present = [[timestamp] + [f"{name} ({usn})" for name, usn in present_students]]
    values_absent = [[timestamp] + [f"{name} ({usn})" for name, usn in absent_students]]

    # Append the attendance data without overwriting existing data
    sheets_service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=range_present,
        valueInputOption='RAW',
        body={'values': values_present}
    ).execute()

    # Append absent students
    sheets_service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=range_absent,
        valueInputOption='RAW',
        body={'values': values_absent}
    ).execute()

if __name__ == '__main__':
    app.run(debug=True)
