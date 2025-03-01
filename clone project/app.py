from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="templates")
app.secret_key="your_secret_key"

UPLOAD_FOLDER = "D:\\OneDrive\\Desktop\\clone project\\static\\uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

EMAIL_ADDRESS="carnab658@gmail.com"
EMAIL_PASSWORD="svwn xgre darf eirj"
app.config['MAIL DEFAULT SENDER']='your_email@gmail.com'

def send_email(to_email, otp):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = "Password Reset OTP"

        body = f"Your OTP for password reset is: {otp}. Do not share it with anyone."
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]
        hometown = request.form["hometown"]
        password = request.form["password"]
        photo = request.files["photo"]

        if photo:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            photo.save(photo_path)  

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, phone, email, hometown, password, photo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, phone, email, hometown, password,filename ))
        conn.commit()
        conn.close()

        return redirect("/login")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect(url_for("welcome", email=email))
        else:
            return "Invalid credentials. Please try again."

    return render_template("login.html")


@app.route("/welcome/<email>")
def welcome(email):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, photo FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    print (user)
    if user:
        name, photo_path = user
        first_path = "/static/uploads/"
        path = first_path + photo_path
        
        print(path)
        return render_template("welcome.html", name=name, photo=path)
    else:
        return "User not found."


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            otp = random.randint(100000, 999999)  
            session["otp"] = otp
            session["email"] = email
            print(session)
            send_email(email, otp)
            flash("OTP sent to your email!", "success")
            return render_template("verify_otp.html")
        else:
            flash("Email not registered!", "danger")

    return render_template("forgot_password.html")


@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    print("Entering Verify otp module")
    if request.method == "POST":
        entered_otp = request.form["otp"]
        print(entered_otp)
        print(session)
        if "otp" in session and int(entered_otp) == session["otp"]:
            return redirect(url_for("reset_password"))
        else:
            flash("Invalid OTP. Please try again!", "danger")

    return render_template("verify_otp.html")

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        new_password = request.form["password"]
        email = session.get("email")

        if email:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
            conn.commit()
            conn.close()
            session.pop("otp", None)  
            session.pop("email", None)  
            flash("Password reset successfully! Please login.", "success")
            return redirect(url_for("login"))

    return render_template("reset_password.html")


if __name__ == "__main__":
    app.run(debug=True)
