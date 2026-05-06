from flask import Flask, render_template, request, redirect, url_for, Response
import boto3
import uuid
import csv
from io import StringIO
from datetime import datetime

app = Flask(__name__)

# AWS/DynamoDB configuration
REGION_NAME = "us-east-1"
STUDENTS_TABLE = "AttendanceStudents"
ATTENDANCE_TABLE = "AttendanceRecords"

dynamodb = boto3.resource("dynamodb", region_name=REGION_NAME)
students_table = dynamodb.Table(STUDENTS_TABLE)
attendance_table = dynamodb.Table(ATTENDANCE_TABLE)


def get_students():
    """Read all students from DynamoDB."""
    response = students_table.scan()
    students = response.get("Items", [])
    return sorted(students, key=lambda student: student.get("name", ""))


def get_attendance_records():
    """Read all attendance records from DynamoDB."""
    response = attendance_table.scan()
    records = response.get("Items", [])
    return sorted(records, key=lambda record: record.get("date", ""), reverse=True)


@app.route("/", methods=["GET", "POST"])
def login():
    """Simple lecturer login page for the prototype."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "lecturer" and password == "Uni2026Safe!":
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid login details")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    """Dashboard showing basic database-backed summary figures."""
    students = get_students()
    attendance_records = get_attendance_records()

    total_students = len(students)

    today = datetime.now().strftime("%Y-%m-%d")
    today_records = [
        record for record in attendance_records
        if record.get("date") == today
    ]

    attendance_today = len([
        record for record in today_records
        if record.get("status") == "Present"
    ])

    absent_today = len([
        record for record in today_records
        if record.get("status") == "Absent"
    ])

    return render_template(
        "dashboard.html",
        total_students=total_students,
        attendance_today=attendance_today,
        absent_today=absent_today
    )


@app.route("/students", methods=["GET", "POST"])
def students():
    """Add and list student records using DynamoDB."""
    if request.method == "POST":
        name = request.form.get("name")
        course = request.form.get("course")
        email = request.form.get("email")

        if name and course:
            student_id = str(uuid.uuid4())

            students_table.put_item(
                Item={
                    "student_id": student_id,
                    "name": name,
                    "course": course,
                    "email": email or ""
                }
            )

        return redirect(url_for("students"))

    all_students = get_students()
    return render_template("students.html", students=all_students)


@app.route("/delete_student/<student_id>")
def delete_student(student_id):
    """Delete a student record from DynamoDB."""
    students_table.delete_item(
        Key={
            "student_id": student_id
        }
    )

    return redirect(url_for("students"))


@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    """Record and display attendance records using DynamoDB."""
    students = get_students()

    if request.method == "POST":
        student_id = request.form.get("student_id")
        date = request.form.get("date")
        status = request.form.get("status")

        selected_student = next(
            (
                student for student in students
                if student.get("student_id") == student_id
            ),
            None
        )

        if selected_student and date and status:
            record_id = str(uuid.uuid4())

            attendance_table.put_item(
                Item={
                    "record_id": record_id,
                    "student_id": student_id,
                    "student_name": selected_student.get("name", ""),
                    "date": date,
                    "status": status
                }
            )

        return redirect(url_for("attendance"))

    records = get_attendance_records()
    return render_template(
        "attendance.html",
        students=students,
        records=records
    )


@app.route("/export_csv")
def export_csv():
    """Export attendance records from DynamoDB as a CSV file."""
    records = get_attendance_records()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Date", "Student", "Status"])

    for record in records:
        writer.writerow([
            record.get("date", ""),
            record.get("student_name", ""),
            record.get("status", "")
        ])

    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=attendance_report.csv"
    )

    return response


@app.route("/logout")
def logout():
    """Return user to login page."""
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

    
    