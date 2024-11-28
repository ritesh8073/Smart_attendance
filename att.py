import matplotlib.pyplot as plt
import re
from collections import defaultdict

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
    # Initialize data structures to track attendance
    students = defaultdict(lambda: {'present': 0, 'total_sessions': 0})
    
    # Regular expression patterns to match "Present" and "Absent" students
    present_pattern = re.compile(r"Present Students:\s*(.*?)\s*Absent Students:", re.DOTALL)
    absent_pattern = re.compile(r"Absent Students:\s*(.*?)\s*(?=\n---|$)", re.DOTALL)

    # Process attendance data
    sessions = attendance_data.strip().split("\n\n--- Attendance Session:")
    
    for session in sessions:
        # Extract present and absent student lists using regex
        present_students = re.findall(r"\((.*?)\)", present_pattern.search(session).group(1) if present_pattern.search(session) else "")
        absent_students = re.findall(r"\((.*?)\)", absent_pattern.search(session).group(1) if absent_pattern.search(session) else "")
        
        # For present students
        for student in present_students:
            student_name = student.split(')')[0].strip()
            students[student_name]['present'] += 1
            students[student_name]['total_sessions'] += 1

        # For absent students
        for student in absent_students:
            student_name = student.split(')')[0].strip()
            students[student_name]['total_sessions'] += 1
    
    # Calculate attendance percentages
    attendance_percentages = {}
    for student, data in students.items():
        total_sessions = data['total_sessions']
        if total_sessions > 0:
            attendance_percentages[student] = (data['present'] / total_sessions) * 100
        else:
            # If no sessions are recorded for the student, set their percentage to 0
            attendance_percentages[student] = 0
    
    return attendance_percentages

# Function to display the pie chart for a selected student
def display_pie_chart(student_name, attendance_percentages):
    if student_name in attendance_percentages:
        attendance_percentage = attendance_percentages[student_name]
        absent_percentage = 100 - attendance_percentage
        
        # Create the pie chart
        labels = ['Present', 'Absent']
        sizes = [attendance_percentage, absent_percentage]
        colors = ['#4CAF50', '#FF5733']  # Green for Present, Red for Absent

        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
        ax.set_title(f'{student_name} Attendance: {attendance_percentage:.1f}%')
        plt.show()
    else:
        print(f"Data for student '{student_name}' not found.")

# Main function to handle user input and display results
def main():
    # Ask the user for the file path of the attendance data
    file_path = input("Enter the path of the attendance text file: ").strip()

    # Read and process the attendance data
    attendance_data = read_attendance_data(file_path)
    
    if attendance_data is None:
        return

    # Process the attendance data
    attendance_percentages = process_attendance_data(attendance_data)

    # Display list of students and their attendance percentages
    print("\nStudent Attendance Percentages:")
    for student, percentage in attendance_percentages.items():
        print(f"{student}: {percentage:.1f}%")
    
    # Ask the user to select a student to view detailed attendance
    selected_student = input("\nEnter the student name to view their attendance: ").strip()

    # Display the pie chart for the selected student
    display_pie_chart(selected_student, attendance_percentages)

# Run the main function
if __name__ == "__main__":
    main()
