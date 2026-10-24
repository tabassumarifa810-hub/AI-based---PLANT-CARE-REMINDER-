
from flask import Flask, render_template, request, redirect, url_for, session
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-secret"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            return "Please fill in every field."

        if len(password) < 8:
            return "Password must be at least 8 characters."

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                (name, email, hashed_password)
            )
            connection.commit()
            return redirect(url_for("login"))

        except Exception:
            connection.rollback()
            return "Registration failed. This email may already be registered."

        finally:
            cursor.close()
            connection.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT id, name, email, password FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()

            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                return redirect(url_for("dashboard"))

            return "Invalid email or password."

        finally:
            cursor.close()
            connection.close()

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT * FROM plants
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        )
        plants = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return render_template("dashboard.html", plants=plants)


@app.route("/plants/add", methods=["GET", "POST"])
def add_plant():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        plant_name = request.form["plant_name"].strip()
        species = request.form.get("species", "").strip()
        watering_interval = request.form.get("watering_interval", "7")
        last_watered = request.form.get("last_watered") or None

        if not plant_name:
            return "Please enter a plant name."

        try:
            watering_interval = int(watering_interval)
            if watering_interval < 1:
                return "Watering interval must be at least 1 day."
        except ValueError:
            return "Please enter a valid watering interval."

        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO plants
                (user_id, plant_name, species, watering_interval, last_watered)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    session["user_id"],
                    plant_name,
                    species or None,
                    watering_interval,
                    last_watered,
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("dashboard"))

    return render_template("add_plant.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
