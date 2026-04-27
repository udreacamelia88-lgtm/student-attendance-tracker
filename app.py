from flask import Flask, render_template, request, redirect, url_for, Response
import csv
from io import StringIO

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/students")
def students():
    return render_template("students.html")


@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    if request.method == "POST":
        student = request.form.get("student")
        date = request.form.get("date")
        status = request.form.get("status")

        print("Attendance saved:", student, date, status)

        return redirect(url_for("attendance"))

    return render_template("attendance.html")


@app.route("/export_csv")
def export_csv():
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Date", "Student", "Status"])
    writer.writerow(["23/04/2026", "John Smith", "Present"])
    writer.writerow(["23/04/2026", "Sarah White", "Present"])
    writer.writerow(["23/04/2026", "Ahmed Khan", "Late"])

    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )

    response.headers["Content-Disposition"] = "attachment; filename=attendance_report.csv"

    return response


if __name__ == "__main__":
    app.run(debug=True)
    