from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
import os
import re
from collections import defaultdict
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For using flash messages

# Function to read the entire attendance data from a file
def read_attendance_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            attendance_data = file.read()
        return attendance_data
    except FileNotFoundError:
        print(f"File not found at the path: {file_path}")
        return None

# Function to process the attendance data and calculate percentages
def process_attendance_data(attendance_data):
    students = defaultdict(lambda: {'present': 0, 'total_sessions': 0})
    
    present_pattern = re.compile(r"Present Students:\s*(.*?)\s*Absent Students:", re.DOTALL)
    absent_pattern = re.compile(r"Absent Students:\s*(.*?)\s*(?=\n---|$)", re.DOTALL)

    sessions = attendance_data.strip().split("\n\n--- Attendance Session:")
    
    for session in sessions:
        present_students = present_pattern.search(session)
        absent_students = absent_pattern.search(session)
        
        if present_students:
            present_list = re.findall(r"([\w\s]+ \(\w+\))", present_students.group(1))
            for student in present_list:
                students[student]['present'] += 1
                students[student]['total_sessions'] += 1
        
        if absent_students:
            absent_list = re.findall(r"([\w\s]+ \(\w+\))", absent_students.group(1))
            for student in absent_list:
                students[student]['total_sessions'] += 1
    
    attendance_percentages = {}
    for student, data in students.items():
        total_sessions = data['total_sessions']
        if total_sessions > 0:
            attendance_percentages[student] = (data['present'] / total_sessions) * 100
        else:
            attendance_percentages[student] = 0
    
    return attendance_percentages

# Function to create a PDF report
def create_pdf_report(statistics):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Attendance Report", ln=True, align="C")
    pdf.ln(10)

    # Adding students with attendance below 75%
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Students with Attendance Below 75%", ln=True)
    pdf.set_font("Arial", "", 12)

    # Set to track students already printed
    printed_students = set()

    for student, percentage in statistics.items():
        if percentage < 75:
            if student not in printed_students:
                pdf.set_text_color(255, 0, 0)  # Red color for low attendance
                pdf.cell(0, 10, f"{student} - {percentage:.1f}%", ln=True)
                pdf.set_text_color(0, 0, 0)  # Reset color to black
                printed_students.add(student)

    pdf.ln(5)

    # Adding students with attendance 75% or above
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Students with Attendance 75% or Above", ln=True)
    pdf.set_font("Arial", "", 12)

    for student, percentage in statistics.items():
        if percentage >= 75:
            if student not in printed_students:
                pdf.set_text_color(0, 128, 0)  # Green color for good attendance
                pdf.cell(0, 10, f"{student} - {percentage:.1f}%", ln=True)
                pdf.set_text_color(0, 0, 0)  # Reset color to black
                printed_students.add(student)

    pdf_output_path = "attendance_report.pdf"
    pdf.output(pdf_output_path)
    return pdf_output_path

@app.route('/', methods=['GET', 'POST'])
def home():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]

    if request.method == 'POST':
        selected_file = request.form.get('file')
        if selected_file:
            file_path = os.path.join(folder_path, selected_file)
            attendance_data = read_attendance_data(file_path)
            if attendance_data is not None:
                attendance_percentages = process_attendance_data(attendance_data)
                pdf_path = create_pdf_report(attendance_percentages)
                return jsonify({"status": "success", "pdf_path": pdf_path, "file_name": selected_file})
            return jsonify({"status": "error", "message": "Error reading the file. Please try again."})

    return render_template('attendance_statistics.html', files=files)

@app.route('/download/<file_name>')
def download(file_name):
    pdf_path = "attendance_report.pdf"
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=f"{file_name}_attendance_report.pdf")
    else:
        flash("Report not found. Please try again.")
        return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
