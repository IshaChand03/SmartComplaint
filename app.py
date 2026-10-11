import os
from datetime import timedelta
from flask import Flask, render_template, redirect
from flask_jwt_extended import JWTManager
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from database import get_connection
from routes.auth import auth_bp
from routes.users import users_bp
from routes.admin import admin_bp
from routes.complaints import complaints_bp
from services.escalation_service import escalate_overdue_complaints
from routes.dashboard import dashboard_bp

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)
JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(complaints_bp)
app.register_blueprint(dashboard_bp)


@app.route("/")
def home():
    return redirect("/login")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/complaints")
def complaints_page():
    return render_template("complaints.html")


@app.route("/complaints/new")
def new_complaint_page():
    return render_template("complaint-new.html")


@app.route("/complaints/<int:complaint_id>")
def complaint_details_page(complaint_id):
    return render_template("complaint-details.html")

@app.route("/queues")
def queues_page():
    return render_template("queues.html")


@app.route("/admin")
def admin_page():
    return render_template("admin.html")
@app.route("/test-db")
def test_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM departments")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"departments": [r[0] for r in rows]}


# ---------- Background job ----------

def run_escalation_job():
    try:
        count = escalate_overdue_complaints()
        print(f"[Scheduler] Escalation check finished. Escalated: {count}")
    except Exception as error:
        print(f"[Scheduler] Escalation check failed: {error}")


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_escalation_job, "interval", minutes=5, id="escalation_job")
    scheduler.start()
    print("[Scheduler] Started. Checking for overdue complaints every 5 minutes.")


if __name__ == "__main__":
    # In debug mode Flask starts the app twice. Start the timer only in the
    # real worker process, otherwise the job would run twice.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_scheduler()
    app.run(debug=True)