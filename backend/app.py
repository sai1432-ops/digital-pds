from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_cors import CORS
from datetime import datetime, timedelta
import secrets
import uuid
import os
import json
import re
import requests
import qrcode
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ultralytics import YOLO
from werkzeug.utils import secure_filename
from sqlalchemy import text
from math import radians, sin, cos, sqrt, atan2
import traceback
import random

app = Flask(__name__)
CORS(app)
print("RUNNING UPDATED APP.PY")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret-key")

jwt = JWTManager(app)

@app.route("/uploads/<path:filename>")
def serve_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ================= DATABASE CONFIG =================
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/digitalpds"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ================= FLASK-MAIL CONFIG =================
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "appanagirisai7569@gmail.com"
app.config["MAIL_PASSWORD"] = "cniaeiafmvpgkvnu"
app.config["MAIL_DEFAULT_SENDER"] = "Mukh Swasthya <appanagirisai7569@gmail.com>"

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "best.pt")
model = YOLO(MODEL_PATH)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

QR_FOLDER = os.path.join(os.path.dirname(__file__), "dealer_qr_codes")
os.makedirs(QR_FOLDER, exist_ok=True)

PDS_CARDS_FOLDER = os.path.join(os.path.dirname(__file__), "uploads", "pds_cards")
os.makedirs(PDS_CARDS_FOLDER, exist_ok=True)


# ================= HELPER FUNCTION =================
def get_request_data():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict() or {}


def normalize_dealer_qr_value(dealer_qr_value):
    if not dealer_qr_value:
        return dealer_qr_value

    if dealer_qr_value.startswith("digitalpds://dealer/"):
        dealer_qr_value = dealer_qr_value.replace("digitalpds://dealer/", "", 1)

    if "?sig=" in dealer_qr_value:
        dealer_qr_value = dealer_qr_value.split("?sig=")[0]

    return dealer_qr_value.strip()


def to_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ["true", "1", "yes", "y"]


def normalize_stock_item_name(value):
    if value is None:
        return ""

    name = str(value).strip().upper()

    mapping = {
        "BRUSH": "BRUSH",
        "TOOTHBRUSH": "BRUSH",
        "TOOTH_BRUSH": "BRUSH",

        "TOOTHPASTE": "TOOTHPASTE",
        "PASTE": "TOOTHPASTE",

        "FLYER": "FLYER",
        "IEC": "FLYER",
        "IEC MATERIAL": "FLYER",
        "IEC MATERIALS": "FLYER",

        "KIT": "KIT",
        "KITS": "KIT"
    }

    return mapping.get(name, "")


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(R * c, 2)


def build_requests_session():
    session = requests.Session()
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["POST"])
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def generate_dealer_qr_value(dealer_id):
    random_part = uuid.uuid4().hex[:8].upper()
    return f"DLR-{dealer_id}-{random_part}"


def generate_dealer_qr_image(qr_value):
    filename = f"{qr_value}.png"
    file_path = os.path.join(QR_FOLDER, filename)

    qr_data = f"digitalpds://dealer/{qr_value}"

    img = qrcode.make(qr_data)
    img.save(file_path)

    return f"dealer_qr_codes/{filename}"
    

# ================= VERIFICATION HELPERS =================
def generate_otp():
    """Generates a 6-digit numeric OTP string."""
    return str(random.randint(100000, 999999))


def send_email_verification_otp(email, name, otp, role="User"):
    """Sends a verification OTP email using Flask-Mail.
    Raises Exception if mail server fails, to allow the caller to handle feedback.
    """
    try:
        msg = Message(
            subject=f"Mukh Swasthya {role} Email Verification OTP",
            recipients=[email]
        )
        msg.body = f"""
Hello {name},

Welcome to Mukh Swasthya.

Your OTP for email verification is: {otp}

This OTP is valid for 10 minutes.

Thank you,
Mukh Swasthya Team
"""
        mail.send(msg)
        print(f"VERIFICATION EMAIL SENT TO {email} for {role}")
    except Exception as e:
        print(f"EMAIL VERIFICATION ERROR for {email}: {str(e)}")
        # RE-RAISE so the endpoint knows it failed
        raise Exception(f"Failed to send email: {str(e)}")


# ================= HOME ROUTE =================
@app.route("/")
def home():
    return "Server is working"


@app.route("/test-email", methods=["GET"])
def test_email():
    try:
        msg = Message(
            subject="Test Email",
            recipients=["appanagirisai7569@gmail.com"],
            body="This is a test email from Flask."
        )
        mail.send(msg)
        return jsonify({"message": "Email sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= STATIC OR ROUTE =================
@app.route("/dealer_qr_codes/<path:filename>")
def serve_dealer_qr_image(filename):
    return send_from_directory(QR_FOLDER, filename)

@app.route("/uploads/<path:filename>")
def serve_upload_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ================= MODELS =================
class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255))
    office_location = db.Column(db.String(150), default="Central Headquarters")


class Dealer(db.Model):
    __tablename__ = "dealers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    company_name = db.Column(db.String(150))
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    username = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(255))
    dealer_qr_value = db.Column(db.String(120), unique=True, nullable=True)
    dealer_qr_image = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(150), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    email_verified = db.Column(db.Boolean, default=False)
    email_verification_otp = db.Column(db.String(10), nullable=True)
    email_verification_expiry = db.Column(db.DateTime, nullable=True)

    reset_code = db.Column(db.String(255), nullable=True)
    reset_expiry = db.Column(db.DateTime, nullable=True)


class DealerLocation(db.Model):
    __tablename__ = "dealer_locations"

    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(150), unique=True, nullable=False)
    dealer_id = db.Column(db.Integer, db.ForeignKey("dealers.id"), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255))
    
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_otp = db.Column(db.String(10), nullable=True)
    email_verification_expiry = db.Column(db.DateTime, nullable=True)

    pds_card_no = db.Column(db.String(50), unique=True)
    pds_linked_at = db.Column(db.DateTime)
    pds_verified = db.Column(db.Boolean, default=False)
    reset_code = db.Column(db.String(255), nullable=True)
    reset_expiry = db.Column(db.DateTime, nullable=True)
    
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(50), nullable=True)  # Updated to match DB string length
    education = db.Column(db.String(100), nullable=True)
    employment = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)

    dealer_id = db.Column(db.Integer, db.ForeignKey("dealers.id"), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey("dealer_locations.id"), nullable=True)
    dealer_assigned_at = db.Column(db.DateTime, nullable=True)
    dealer_assignment_locked = db.Column(db.Boolean, default=False)
    created_by_type = db.Column(db.String(20), default="SELF")
    pds_card_front = db.Column(db.String(255), nullable=True)
    pds_card_back = db.Column(db.String(255), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)

# ================= ONE-TIME MIGRATION =================
@app.before_request
def run_once_migration():
    if not hasattr(app, "_migration_done") or not app._migration_done:
        try:
            # Force verify all accounts that might have been defaulted to 0/False
            # to prevent login lockout for existing verified users
            updated_users = User.query.filter((User.email_verified == False) | (User.email_verified == None)).all()
            if updated_users:
                for u in updated_users:
                    u.email_verified = True
                db.session.commit()
                print(f">>> [MIGRATION] Verified {len(updated_users)} existing users")

            updated_dealers = Dealer.query.filter((Dealer.email_verified == False) | (Dealer.email_verified == None)).all()
            if updated_dealers:
                for d in updated_dealers:
                    d.email_verified = True
                db.session.commit()
                print(f">>> [MIGRATION] Verified {len(updated_dealers)} existing dealers")
                
            app._migration_done = True
        except Exception as e:
            print(f">>> [MIGRATION ERROR] {str(e)}")

class DealerStock(db.Model):
    __tablename__ = "dealer_stock"

    id = db.Column(db.Integer, primary_key=True)
    dealer_id = db.Column(db.Integer, db.ForeignKey("dealers.id"), nullable=False)
    item_name = db.Column(
        db.Enum("BRUSH", "TOOTHPASTE", "FLYER"),
        nullable=False
    )
    quantity = db.Column(db.Integer, default=0)


class StockRequest(db.Model):
    __tablename__ = "stock_requests"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(100), nullable=False)
    dealer_id = db.Column(db.Integer, db.ForeignKey("dealers.id"), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    requested_quantity = db.Column(db.Integer, nullable=False)
    total_kits = db.Column(db.Integer, default=0)
    urgency = db.Column(db.String(50), default="Normal")
    status = db.Column(db.Enum("PENDING", "APPROVED", "DISPATCHED", "DELIVERED", "REJECTED"), default="PENDING")
    requested_at = db.Column(db.DateTime, server_default=db.func.now())
    reviewed_at = db.Column(db.DateTime)
    dispatched_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime, nullable=True)
    admin_note = db.Column(db.Text)
    courier_name = db.Column(db.String(120))
    tracking_id = db.Column(db.String(120))

    dispatch_address = db.Column(db.Text, nullable=True)
    dispatch_city = db.Column(db.String(100), nullable=True)
    dispatch_state = db.Column(db.String(100), nullable=True)


class KitDistribution(db.Model):
    __tablename__ = "kit_distributions"

    id = db.Column(db.Integer, primary_key=True)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    dealer_id = db.Column(db.Integer, db.ForeignKey("dealers.id"), nullable=False)
    kit_unique_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.Enum("PENDING", "CONFIRMED"), default="PENDING")
    expiry = db.Column(db.DateTime)
    confirmed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    confirmation_mode = db.Column(db.String(50), default="USER_QR_SCAN")
    old_kit_returned = db.Column(db.Boolean, default=False)

    brush_received = db.Column(db.Integer, default=0)
    paste_received = db.Column(db.Integer, default=0)
    iec_received = db.Column(db.Integer, default=0)


class FamilyMember(db.Model):
    __tablename__ = "family_members"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    member_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    relation = db.Column(db.String(50))
    brushing_target = db.Column(db.Integer, default=14)
    weekly_brush_count = db.Column(db.Integer, default=0)


class BrushingCheckin(db.Model):
    __tablename__ = "brushing_checkins"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("family_members.id"), nullable=True)
    checkin_date = db.Column(db.Date, nullable=False)
    session = db.Column(db.Enum("MORNING", "EVENING"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Clinic(db.Model):
    __tablename__ = "clinics"

    id = db.Column(db.Integer, primary_key=True)
    clinic_name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.Text)
    district = db.Column(db.String(100))
    contact_number = db.Column(db.String(20))
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    website = db.Column(db.String(255), nullable=True)
    booking_available = db.Column(db.Boolean, default=True)


class TeethReport(db.Model):
    __tablename__ = "teeth_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    member_id = db.Column(db.Integer)
    image_path = db.Column(db.String(255))
    ai_result = db.Column(db.Text)
    risk_level = db.Column(db.String(20))
    created_at = db.Column(db.DateTime)


class RegistrationOtp(db.Model):
    __tablename__ = "registration_otps"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    otp_code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================= ADMIN PROFILE ROUTES =================
@app.route("/admin/profile", methods=["GET"])
@jwt_required()
def get_admin_profile():
    from flask_jwt_extended import get_jwt_identity
    admin_id = get_jwt_identity()
    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    return jsonify({
        "id": admin.id,
        "name": admin.name,
        "email": admin.email,
        "phone": admin.phone,
        "office_location": admin.office_location or "Central Headquarters"
    }), 200

@app.route("/admin/update-profile", methods=["PUT"])
@jwt_required()
def update_admin_profile():
    from flask_jwt_extended import get_jwt_identity
    admin_id = get_jwt_identity()
    admin = Admin.query.get(admin_id)
    
    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    admin.name = request.form.get("name", admin.name)
    admin.phone = request.form.get("phone", admin.phone)
    admin.office_location = request.form.get("office_location", admin.office_location)

    db.session.commit()
    
    return jsonify({
        "message": "Profile updated successfully"
    }), 200

@app.route("/admin/change-password", methods=["PUT"])
@jwt_required()
def change_admin_password():
    from flask_jwt_extended import get_jwt_identity
    data = get_request_data()
    
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if not current_password or not new_password:
        return jsonify({"error": "current_password and new_password are required"}), 400
        
    admin_id = get_jwt_identity()
    admin = Admin.query.get(admin_id)
    
    if not admin:
         return jsonify({"error": "Admin not found"}), 404
         
    if not bcrypt.check_password_hash(admin.password_hash, current_password):
         return jsonify({"error": "Incorrect current password"}), 401
         
    admin.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    db.session.commit()
    
    return jsonify({"message": "Password changed successfully"}), 200


@app.route("/admin/dashboard-stats", methods=["GET"])
def get_admin_dashboard_stats():
    try:
        # Improved counting using direct session query for stability
        total_dealers = db.session.query(Dealer).count()
        
        # Beneficiaries count only includes Head of Families (Users) as per request
        active_beneficiaries = db.session.query(User).count()
        
        # Calculate full distribution counts for percentages
        total_dist_rows = db.session.query(KitDistribution).count()
        confirmed_count = db.session.query(KitDistribution).filter_by(status="CONFIRMED").count()
        pending_count = db.session.query(KitDistribution).filter_by(status="PENDING").count()
        returned_count = db.session.query(KitDistribution).filter_by(old_kit_returned=True).count()

        if total_dist_rows > 0:
            kit_given_percentage = int((confirmed_count / total_dist_rows) * 100)
            kit_pending_percentage = int((pending_count / total_dist_rows) * 100)
            kit_returned_percentage = int((returned_count / total_dist_rows) * 100)
        else:
            kit_given_percentage = 0
            kit_pending_percentage = 0
            kit_returned_percentage = 0

        # Trends (last 3 months) - returning placeholder trends matching the model structure
        trends = []
        now = datetime.utcnow()
        for i in range(3):
            month_date = now - timedelta(days=i*30)
            month_label = month_date.strftime('%b')
            trends.append({
                "month": month_label,
                "kits": confirmed_count,
                "dealers": total_dealers
            })

        return jsonify({
            "totalDealers": str(total_dealers),
            "totalDealersChange": "+12%",
            "isDealersPositive": True,
            "activeBeneficiaries": str(active_beneficiaries),
            "activeBeneficiariesChange": "+5%",
            "isBeneficiariesPositive": True,
            "totalDistributions": str(confirmed_count),
            "totalDistributionsChange": "+2%",
            "isDistributionsPositive": True,
            "returnRate": str(returned_count),
            "returnRateChange": "0%",
            "isReturnRatePositive": True if kit_returned_percentage > 0 else False,
            "kitGivenPercentage": kit_given_percentage,
            "kitReturnedPercentage": kit_returned_percentage,
            "kitPendingPercentage": kit_pending_percentage,
            "distributionTrends": trends[::-1],
            "dealerTrends": trends[::-1]
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/admin/distributions", methods=["GET"])
def get_admin_distributions():
    try:
        # Query confirmed distributions with JOINs
        results = db.session.query(
            KitDistribution,
            User.name.label("beneficiary_name"),
            User.pds_card_no,
            Dealer.name.label("dealer_name")
        ).join(
            User, KitDistribution.beneficiary_id == User.id
        ).join(
            Dealer, KitDistribution.dealer_id == Dealer.id
        ).filter(
            KitDistribution.status == "CONFIRMED"
        ).order_by(
            KitDistribution.confirmed_at.desc()
        ).all()

        payload = []
        for dist, b_name, pds_no, d_name in results:
            payload.append({
                "id": dist.id,
                "kit_unique_id": dist.kit_unique_id,
                "beneficiary_name": b_name,
                "pds_card_no": pds_no,
                "dealer_name": d_name,
                "confirmed_at": dist.confirmed_at.isoformat() if dist.confirmed_at else None,
                "brush_received": dist.brush_received,
                "paste_received": dist.paste_received,
                "iec_received": dist.iec_received
            })
            
        return jsonify(payload), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ================= DEALER REGISTER ROUTE =================
@app.route("/dealer/register", methods=["POST"])
def dealer_register():
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received. Send JSON or form-data."}), 400

        required_fields = ["name", "email", "password", "phone", "company_name"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        email = data["email"].strip().lower()

        # Check if dealer already exists (possibly as a stub from the OTP phase)
        existing_dealer = Dealer.query.filter_by(email=email).first()

        hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

        if existing_dealer:
            print(f">>> [DEBUG] Updating existing dealer stub for: {email}")
            existing_dealer.name = data["name"]
            existing_dealer.phone = data["phone"]
            existing_dealer.company_name = data["company_name"]
            existing_dealer.address = data.get("address")
            existing_dealer.city = data.get("city")
            existing_dealer.state = data.get("state")
            existing_dealer.username = data.get("username")
            existing_dealer.password_hash = hashed_password
            existing_dealer.location = data.get("location")
            # Set verified to True as they have completed the registration
            existing_dealer.email_verified = True
            new_dealer = existing_dealer
        else:
            print(f">>> [DEBUG] Creating new dealer: {email}")
            new_dealer = Dealer(
                name=data["name"],
                email=email,
                phone=data["phone"],
                company_name=data["company_name"],
                address=data.get("address"),
                city=data.get("city"),
                state=data.get("state"),
                username=data.get("username"),
                password_hash=hashed_password,
                location=data.get("location"),
                is_active=to_bool(data.get("is_active", True)),
                email_verified=True  # Default to True since frontend verifies it first
            )
            db.session.add(new_dealer)
        db.session.flush() # Get new_dealer.id

        # Also create a default entry in dealer_locations if location is provided
        # User requested: Synchronize address with dealer_locations
        location_name = data.get("location") or data.get("address")
        if location_name:
            new_location = DealerLocation(
                dealer_id=new_dealer.id,
                location_name=location_name
            )
            db.session.add(new_location)
        
        # Also sync to dealer.location field for redundancy
        new_dealer.location = location_name

        qr_value = generate_dealer_qr_value(new_dealer.id)
        qr_image = generate_dealer_qr_image(qr_value)

        new_dealer.dealer_qr_value = qr_value
        new_dealer.dealer_qr_image = qr_image
        
        db.session.commit()

        return jsonify({
            "message": "Dealer registered successfully",
            "dealer_id": new_dealer.id,
            "name": new_dealer.name,
            "email": new_dealer.email,
            "dealer_qr_value": new_dealer.dealer_qr_value,
            "dealer_qr_image": new_dealer.dealer_qr_image
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= REGISTRATION OTP ROUTES =================
@app.route("/user/send-registration-otp", methods=["POST"])
def send_registration_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"error": "Email is required"}), 400

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 400

        # Generate 6-digit OTP using the existing helper
        otp = generate_otp()

        # Store or update OTP
        reg_otp = RegistrationOtp.query.filter_by(email=email).first()
        if reg_otp:
            reg_otp.otp_code = otp
            reg_otp.created_at = datetime.utcnow()
        else:
            reg_otp = RegistrationOtp(email=email, otp_code=otp)
            db.session.add(reg_otp)
        
        db.session.commit()

        # Send the verification email using the existing helper
        try:
            send_email_verification_otp(email, "New User", otp, role="Registration")
            return jsonify({"message": "Verification code sent to your email"}), 200
        except Exception as mail_err:
            db.session.rollback() # Rollback the OTP storage if email fails
            return jsonify({
                "error": f"Email sending failed: {str(mail_err)}",
                "otp_generated": False
            }), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/user/verify-registration-otp", methods=["POST"])
def verify_registration_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()
        otp = data.get("otp", "").strip()

        if not email or not otp:
            return jsonify({"error": "Email and OTP are required"}), 400

        reg_otp = RegistrationOtp.query.filter_by(email=email, otp_code=otp).first()

        if not reg_otp:
            return jsonify({"error": "Invalid verification code"}), 400

        # Check expiry (10 minutes)
        if datetime.utcnow() > reg_otp.created_at + timedelta(minutes=10):
            db.session.delete(reg_otp)
            db.session.commit()
            return jsonify({"error": "Verification code expired"}), 400

        # Success - code verified
        # Delete after success
        db.session.delete(reg_otp)
        db.session.commit()

        return jsonify({"message": "Email verified successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/dealer/send-registration-otp", methods=["POST"])
def send_dealer_registration_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"error": "Email is required"}), 400

        # Check if dealer already exists
        if Dealer.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered to a dealer"}), 400

        # Generate 6-digit OTP using the existing helper
        otp = generate_otp()

        # Store or update OTP
        reg_otp = RegistrationOtp.query.filter_by(email=email).first()
        if reg_otp:
            reg_otp.otp_code = otp
            reg_otp.created_at = datetime.utcnow()
        else:
            reg_otp = RegistrationOtp(email=email, otp_code=otp)
            db.session.add(reg_otp)
        
        db.session.commit()

        # Send the verification email using the existing helper
        try:
            send_email_verification_otp(email, "New Dealer", otp, role="Dealer Registration")
            return jsonify({"message": "Verification code sent to dealer's email"}), 200
        except Exception as mail_err:
            db.session.rollback()
            return jsonify({
                "error": f"Email sending failed: {str(mail_err)}",
                "otp_generated": False
            }), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/dealer/verify-registration-otp", methods=["POST"])
def verify_dealer_registration_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()
        otp = data.get("otp", "").strip()

        print(f">>> [DEBUG OTP] Checking OTP for: {email}, Code: |{otp}|")

        if not email or not otp:
            return jsonify({"error": "Email and OTP are required"}), 400

        reg_otp = RegistrationOtp.query.filter_by(email=email, otp_code=otp).first()

        if not reg_otp:
            # Check if it exists for email but has different OTP
            actual = RegistrationOtp.query.filter_by(email=email).first()
            if actual:
                print(f">>> [DEBUG OTP] Record found but OTP mismatch. Stored: |{actual.otp_code}| vs Received: |{otp}|")
            else:
                print(f">>> [DEBUG OTP] No OTP record found for email: {email}")
            return jsonify({"error": "Invalid verification code"}), 400

        print(f">>> [DEBUG OTP] Verification success for: {email}")

        # Check expiry (10 minutes)
        if datetime.utcnow() > reg_otp.created_at + timedelta(minutes=10):
            print(f">>> [DEBUG OTP] Code EXPIRED for: {email}")
            db.session.delete(reg_otp)
            db.session.commit()
            return jsonify({"error": "Verification code expired"}), 400

        # Success - code verified
        # Delete after success
        db.session.delete(reg_otp)
        db.session.commit()

        return jsonify({"message": "Email verified successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= USER REGISTER ROUTE =================
@app.route("/user/register", methods=["POST"])
@app.route("/api/user/register", methods=["POST"])
def user_register():
    # Since it's now multipart/form-data, data might be in request.form
    data = request.form.to_dict()
    if not data:
        # Fallback to JSON if someone still sends it
        data = request.get_json() or {}

    required_fields = ["name", "email", "password", "phone"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    email = data["email"].strip().lower()

    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    profile_image_path = None
    
    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file and file.filename:
            import uuid
            filename = secure_filename(f"profile_{uuid.uuid4()}_{file.filename}")
            upload_folder = os.path.join(app.root_path, 'uploads', 'profile_pictures')
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            profile_image_path = f"uploads/profile_pictures/{filename}"

    if existing_user:
        # If it's an admin-created account, we allow person to "take over" and register
        if existing_user.created_by_type == "ADMIN":
            print(f">>> [DEBUG] Updating existing ADMIN beneficiary account: {email}")
            existing_user.name = data["name"]
            existing_user.phone = data["phone"]
            existing_user.password_hash = hashed_password
            if data.get("age"): existing_user.age = int(data["age"]) if str(data["age"]).isdigit() else existing_user.age
            if data.get("gender"): existing_user.gender = data.get("gender")
            if data.get("education"): existing_user.education = data.get("education")
            if data.get("employment"): existing_user.employment = data.get("employment")
            if data.get("address"): existing_user.address = data.get("address")
            if profile_image_path: existing_user.profile_image = profile_image_path
            
            existing_user.created_by_type = "SELF" # Now it's a self-registered user
            existing_user.email_verified = True # They verified email in earlier step
            
            new_user = existing_user
        else:
            return jsonify({"error": "Email already exists"}), 400
    else:
        # Standard New Registration
        new_user = User(
            name=data["name"],
            email=email,
            phone=data["phone"],
            password_hash=hashed_password,
            age=int(data["age"]) if data.get("age") and str(data["age"]).isdigit() else None,
            gender=data.get("gender"),
            education=data.get("education"),
            employment=data.get("employment"),
            address=data.get("address"),
            profile_image=profile_image_path,
            dealer_id=None,
            created_by_type="SELF",
            email_verified=True,
            email_verification_otp=generate_otp(),
            email_verification_expiry=datetime.utcnow() + timedelta(minutes=10)
        )
        db.session.add(new_user)

    db.session.commit()

    return jsonify({
        "isSuccessful": True,
        "message": "User registered successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "access_token": "mock_token_" + str(new_user.id),
        "profile_image": new_user.profile_image
    }), 201

@app.route("/user/link-identity", methods=["POST"])
def link_identity():
    try:
        data = get_request_data()
        user_id = data.get("userId")
        card_no = data.get("identityCardNo")
        
        if not user_id or not card_no:
            return jsonify({"error": "userId and identityCardNo are required"}), 400
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        user.pds_card_no = card_no
        user.pds_verified = True
        user.pds_linked_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "message": "Identity linked successfully",
            "next_step": "SELECT_DEALER"
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ================= EMAIL VERIFICATION ROUTES =================
@app.route("/user/verify-email-otp", methods=["POST"])
def user_verify_email_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()
        otp = data.get("otp", "").strip()

        if not email or not otp:
            return jsonify({"error": "email and otp are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "Invalid target account"}), 400

        if user.email_verified:
            return jsonify({"message": "Email already verified"}), 200

        if user.email_verification_otp != otp:
            return jsonify({"error": "Invalid OTP"}), 400

        if not user.email_verification_expiry or datetime.utcnow() > user.email_verification_expiry:
            return jsonify({"error": "OTP expired"}), 400

        user.email_verified = True
        user.email_verification_otp = None
        user.email_verification_expiry = None
        db.session.commit()

        return jsonify({"message": "User email verified successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/dealer/verify-email-otp", methods=["POST"])
def dealer_verify_email_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()
        otp = data.get("otp", "").strip()

        if not email or not otp:
            return jsonify({"error": "email and otp are required"}), 400

        dealer = Dealer.query.filter_by(email=email).first()
        if not dealer:
            return jsonify({"error": "Invalid target account"}), 400

        if dealer.email_verified:
            return jsonify({"message": "Email already verified"}), 200

        if dealer.email_verification_otp != otp:
            return jsonify({"error": "Invalid OTP"}), 400

        if not dealer.email_verification_expiry or datetime.utcnow() > dealer.email_verification_expiry:
            return jsonify({"error": "OTP expired"}), 400

        dealer.email_verified = True
        dealer.email_verification_otp = None
        dealer.email_verification_expiry = None
        db.session.commit()

        return jsonify({"message": "Dealer email verified successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/user/resend-email-otp", methods=["POST"])
def user_resend_email_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"error": "email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"message": "If the account exists, OTP has been sent"}), 200

        if user.email_verified:
            return jsonify({"message": "Email already verified"}), 200

        otp = generate_otp()
        user.email_verification_otp = otp
        user.email_verification_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()

        send_email_verification_otp(user.email, user.name, otp, role="User")
        return jsonify({"message": "OTP sent successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/dealer/resend-email-otp", methods=["POST"])
def dealer_resend_email_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"error": "email is required"}), 400

        dealer = Dealer.query.filter_by(email=email).first()
        if not dealer:
            return jsonify({"message": "If the account exists, OTP has been sent"}), 200

        if dealer.email_verified:
            return jsonify({"message": "Email already verified"}), 200

        otp = generate_otp()
        dealer.email_verification_otp = otp
        dealer.email_verification_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()

        send_email_verification_otp(dealer.email, dealer.name, otp, role="Dealer")
        return jsonify({"message": "OTP sent successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= USER SELECT DEALER =================
@app.route("/api/user/select-dealer", methods=["POST"])
def select_dealer():
    try:
        data = get_request_data()
        user_id = data.get("user_id")
        dealer_id = data.get("dealer_id")
        
        print(f"DIAGNOSTIC - select_dealer called with: user_id={user_id}, dealer_id={dealer_id}")

        if not user_id or not dealer_id:
            return jsonify({"error": "user_id and dealer_id are required"}), 400

        user = User.query.get(int(user_id))
        dealer = Dealer.query.get(int(dealer_id))

        if not user or not dealer:
            return jsonify({"error": "User or Dealer not found"}), 404

        user.dealer_id = dealer.id
        user.dealer_assigned_at = datetime.utcnow()
        user.dealer_assignment_locked = True # Lock selection on confirm
        
        # Set location_id from dealer_locations
        location_obj = DealerLocation.query.filter_by(dealer_id=dealer.id).first()
        if location_obj:
            user.location_id = location_obj.id
            
        db.session.add(user) # Ensure object is in session
        db.session.commit()

        return jsonify({
            "message": f"Dealer {dealer.name} assigned to user {user.name}",
            "dealer_id": dealer.id
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG SELECT DEALER ERROR: {str(e)}") # Add debug logging
        return jsonify({"error": str(e)}), 500


@app.route("/admin/dealers", methods=["GET"])
def get_admin_dealers():
    try:
        dealers = Dealer.query.all()
        payload = []
        for d in dealers:
            payload.append({
                "id": d.id,
                "name": d.name,
                "companyName": d.company_name,
                "phone": d.phone,
                "email": d.email,
                "handle": d.username or d.name.lower().replace(" ", "_"),
                "location": d.location or d.address or "N/A",
                "address": d.address or "N/A",
                "city": d.city or "N/A",
                "state": d.state or "N/A",
                "pincode": "N/A", # Not currently in model, return default
                "contactPerson": d.name,
                "contactPhone": d.phone,
                "activeStatus": "Active" if d.is_active else "Inactive",
                "isOnline": True,
                "isEnabled": bool(d.is_active)
            })
        return jsonify(payload), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/dealers/<dealer_id>", methods=["GET"])
def get_admin_dealer_details(dealer_id):
    try:
        d_id = int(dealer_id)
        dealer = Dealer.query.get(d_id)

        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404

        return jsonify({
            "id": dealer.id,
            "name": dealer.name,
            "username": dealer.username or "",
            "handle": dealer.username or (dealer.name.lower().replace(" ", "_") if dealer.name else ""),
            "phone": dealer.phone or "N/A",
            "email": dealer.email or "N/A",
            "location": dealer.location or dealer.address or "N/A",
            "address": dealer.address or "N/A",
            "city": dealer.city or "N/A",
            "state": dealer.state or "N/A",
            "companyName": dealer.company_name or "N/A",
            "activeStatus": "Active" if dealer.is_active else "Inactive",
            "isEnabled": bool(dealer.is_active),
            "isOnline": bool(dealer.is_active)
        }), 200

    except ValueError:
        return jsonify({"error": "Invalid dealer ID"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dealers", methods=["GET"])
def get_active_dealers():
    try:
        dealers = Dealer.query.all()
        payload = []
        for d in dealers:
            payload.append({
                "id": d.id,
                "name": d.name,
                "location": d.address or d.location or d.city or "General",
                "email": d.email,
                "phone": d.phone,
                "company_name": d.company_name
            })
        return jsonify(payload), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= ADMIN GET BENEFICIARIES =================
@app.route("/admin/beneficiaries", methods=["GET"])
def get_admin_beneficiaries():
    try:
        # Query User with Dealer and Location
        results = db.session.query(
            User,
            Dealer.name.label("dealer_name"),
            Dealer.company_name.label("dealer_company"),
            Dealer.location.label("loc_name")
        ).outerjoin(
            Dealer, User.dealer_id == Dealer.id
        ).all()
        
        payload = []
        for user, d_name, d_company, l_name in results:
            payload.append({
                "id": user.id,
                "name": user.name,
                "pds_card_no": user.pds_card_no,
                "pds_verified": bool(user.pds_verified),
                "pds_linked_at": str(user.pds_linked_at.date()) if user.pds_linked_at else None,
                "phone": user.phone,
                "email": user.email,
                "dealer_name": d_name or "N/A",
                "location_name": l_name or d_company or "N/A"
            })
            
        return jsonify(payload), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ================= ADMIN CREATE BENEFICIARY ROUTE =================
@app.route("/api/admin/beneficiaries", methods=["POST"])
@jwt_required()
def api_admin_create_beneficiary():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    required_fields = ["name", "ration_card_no", "phone", "dealer_id"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if User.query.filter_by(pds_card_no=data["ration_card_no"]).first():
        return jsonify({"error": "PDS Number already registered"}), 400

    if User.query.filter_by(phone=data["phone"]).first():
        return jsonify({"error": "Phone number already registered"}), 400

    dealer = Dealer.query.get(int(data["dealer_id"]))
    if not dealer:
        return jsonify({"error": "Dealer not found"}), 404

    # Handle PDS card images
    pds_front_path = None
    pds_back_path = None
    
    if 'pds_front' in request.files:
        file = request.files['pds_front']
        if file and file.filename:
            filename = secure_filename(f"front_{uuid.uuid4()}_{file.filename}")
            filepath = os.path.join(PDS_CARDS_FOLDER, filename)
            file.save(filepath)
            pds_front_path = f"uploads/pds_cards/{filename}"

    if 'pds_back' in request.files:
        file = request.files['pds_back']
        if file and file.filename:
            filename = secure_filename(f"back_{uuid.uuid4()}_{file.filename}")
            filepath = os.path.join(PDS_CARDS_FOLDER, filename)
            file.save(filepath)
            pds_back_path = f"uploads/pds_cards/{filename}"



    new_user = User(
        name=data["name"],
        phone=data["phone"],
        email=data.get("email") if data.get("email") else None,
        pds_card_no=data["ration_card_no"],
        address=data.get("address"),
        age=int(data["age"]) if data.get("age") and str(data["age"]).isdigit() else None,
        gender=data.get("gender"),
        education=data.get("education"),
        employment=data.get("employment"),
        password_hash=bcrypt.generate_password_hash("welcome@123").decode("utf-8"),
        dealer_id=dealer.id,
        pds_linked_at=datetime.utcnow(),
        pds_verified=True,
        dealer_assigned_at=datetime.utcnow(),
        dealer_assignment_locked=True,
        created_by_type="ADMIN",
        pds_card_front=pds_front_path,
        pds_card_back=pds_back_path,
        email_verified=True,
        location_id=DealerLocation.query.filter_by(dealer_id=dealer.id).first().id if DealerLocation.query.filter_by(dealer_id=dealer.id).first() else None
    )

    try:
        db.session.add(new_user)
        db.session.flush() # Flush to get new_user.id before commit

        members = data.get("members", [])
        if isinstance(members, str):
            import json
            try:
                members = json.loads(members)
            except:
                members = []
        
        if members:
            for member in members:
                # Ensure age is passed as digit safely
                age_val = 0
                if member.get("age") and str(member.get("age")).isdigit():
                    age_val = int(member.get("age"))
                    
                new_member = FamilyMember(
                    user_id=new_user.id,
                    member_name=member.get("name", "Unknown"),
                    age=age_val,
                    relation=member.get("relation", "Other"),
                    brushing_target=14,
                    weekly_brush_count=0
                )
                db.session.add(new_member)

        db.session.commit()

        return jsonify({
            "message": "Beneficiary created successfully",
            "user_id": new_user.id,
            "name": new_user.name
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= DEALER HOUSEHOLD REGISTER ROUTE =================
@app.route("/dealer/register-household", methods=["POST"])
def dealer_register_household():
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received. Send JSON or form-data."}), 400

        required_fields = ["dealer_id", "name", "phone", "pds_card_no"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        dealer = Dealer.query.get(int(data["dealer_id"]))
        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404

        existing_phone = User.query.filter_by(phone=data["phone"]).first()
        if existing_phone:
            return jsonify({"error": "Phone already registered"}), 400

        if data.get("email"):
            existing_email = User.query.filter_by(email=data["email"]).first()
            if existing_email:
                return jsonify({"error": "Email already registered"}), 400

        existing_pds = User.query.filter_by(pds_card_no=data["pds_card_no"]).first()
        if existing_pds:
            return jsonify({"error": "PDS card already registered"}), 400

        # Handle PDS card images
        pds_front_path = None
        pds_back_path = None
        
        if 'pds_front' in request.files:
            file = request.files['pds_front']
            if file and file.filename:
                filename = secure_filename(f"front_{uuid.uuid4()}_{file.filename}")
                filepath = os.path.join(PDS_CARDS_FOLDER, filename)
                file.save(filepath)
                pds_front_path = f"uploads/pds_cards/{filename}"

        if 'pds_back' in request.files:
            file = request.files['pds_back']
            if file and file.filename:
                filename = secure_filename(f"back_{uuid.uuid4()}_{file.filename}")
                filepath = os.path.join(PDS_CARDS_FOLDER, filename)
                file.save(filepath)
                pds_back_path = f"uploads/pds_cards/{filename}"



        new_user = User(
            name=data["name"],
            email=data.get("email").strip().lower() if data.get("email") else None,
            phone=data["phone"],
            password_hash=bcrypt.generate_password_hash("welcome@123").decode("utf-8"),
            pds_card_no=data["pds_card_no"],
            pds_linked_at=datetime.utcnow(),
            pds_verified=True,
            
            # Additional fields from dealer registration
            age=int(data.get("age")) if data.get("age") and str(data.get("age")).isdigit() else None,
            gender=data.get("gender"),
            education=data.get("education"),
            employment=data.get("employment"),
            address=data.get("address"),

            dealer_id=int(data["dealer_id"]),
            dealer_assigned_at=datetime.utcnow(),
            dealer_assignment_locked=True,
            created_by_type="DEALER",
            pds_card_front=pds_front_path,
            pds_card_back=pds_back_path,
            email_verified=True,
            location_id=DealerLocation.query.filter_by(dealer_id=int(data["dealer_id"])).first().id if DealerLocation.query.filter_by(dealer_id=int(data["dealer_id"])).first() else None
        )

        db.session.add(new_user)
        db.session.flush()

        # Handle Family Members
        members = data.get("members", [])
        if isinstance(members, str):
            import json
            try:
                members = json.loads(members)
            except:
                members = []
        
        if members:
            for member in members:
                age_val = 0
                if member.get("age") and str(member.get("age")).isdigit():
                    age_val = int(member.get("age"))
                    
                new_member = FamilyMember(
                    user_id=new_user.id,
                    member_name=member.get("name", "Unknown"),
                    age=age_val,
                    relation=member.get("relation", "Other"),
                    brushing_target=14,
                    weekly_brush_count=0
                )
                db.session.add(new_member)

        db.session.commit()

        return jsonify({
            "message": "Household registered successfully",
            "user_id": new_user.id,
            "name": new_user.name
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= ADMIN LOGIN ROUTE =================
@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    admin = Admin.query.filter_by(email=email).first()
    
    if not admin or not admin.password_hash:
        return jsonify({"error": "Invalid credentials"}), 401

    is_valid = False
    password = data["password"]
    
    if admin.password_hash.startswith("$2b$"):
        is_valid = bcrypt.check_password_hash(admin.password_hash, password)
    else:
        # Legacy plain text migration
        if admin.password_hash == password:
            is_valid = True
            # Upgrade to hash
            admin.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
            db.session.commit()

    if not is_valid:
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(admin.id))
    return jsonify({
        "message": "Admin login successful",
        "access_token": access_token,
        "admin_id": admin.id,
        "name": admin.name,
        "email": admin.email,
        "phone": admin.phone
    }), 200


# ================= DEALER LOGIN ROUTE =================
@app.route("/dealer/login", methods=["POST"])
def dealer_login():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    dealer = Dealer.query.filter_by(email=email).first()

    if not dealer or not dealer.password_hash:
        return jsonify({"error": "Invalid credentials"}), 401

    is_valid = False
    if dealer.password_hash.startswith("$2b$"):
        is_valid = bcrypt.check_password_hash(dealer.password_hash, password)
    else:
        # Legacy plain text migration
        if dealer.password_hash == password:
            is_valid = True
            # Upgrade to hash
            dealer.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
            db.session.commit()

    if not is_valid:
        return jsonify({"error": "Invalid credentials"}), 401

    if not dealer.email_verified:
        return jsonify({"error": "Please verify your email before login"}), 403

    access_token = create_access_token(identity=str(dealer.id))
    return jsonify({
        "message": "Dealer login successful",
        "access_token": access_token,
        "dealer_id": dealer.id,
        "name": dealer.name,
        "email": dealer.email,
        "phone": dealer.phone,
        "dealer_qr_value": dealer.dealer_qr_value,
        "dealer_qr_image": dealer.dealer_qr_image
    }), 200


# ================= USER LOGIN ROUTE =================
@app.route("/user/login", methods=["POST"])
def user_login():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.password_hash:
        return jsonify({"error": "Invalid credentials"}), 401

    is_valid = False
    if user.password_hash.startswith("$2b$"):
        is_valid = bcrypt.check_password_hash(user.password_hash, password)
    else:
        # Legacy plain text migration
        if user.password_hash == password:
            is_valid = True
            # Upgrade to hash
            user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
            db.session.commit()

    if not is_valid:
        print(f">>> [DEBUG LOGIN] Password mismatch for: {email}")
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.email_verified:
        print(f">>> [DEBUG LOGIN] Email NOT verified for: {email}")
        return jsonify({"error": "Please verify your email before login"}), 403

    print(f">>> [DEBUG LOGIN] SUCCESS for: {email}")

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "User login successful",
        "access_token": access_token,
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "pds_verified": bool(user.pds_verified),
        "pds_card_no": user.pds_card_no,
        "profile_image": user.profile_image if user.profile_image else None,
        "created_by_type": user.created_by_type or "SELF"
    }), 200


# ================= USER FORGOT PASSWORD - SEND OTP =================
@app.route("/user/forgot-password/send-otp", methods=["POST"])
def user_send_forgot_password_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"error": "email is required"}), 400

        user = User.query.filter_by(email=email).first()

        # Do not reveal whether the email exists
        if not user:
            return jsonify({"message": "If the account exists, OTP has been sent"}), 200

        otp = str(random.randint(100000, 999999))

        user.reset_code = otp
        user.reset_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()

        # Send OTP email
        msg = Message(
            subject="Mukh Swasthya Password Reset OTP",
            recipients=[email]
        )
        msg.body = f"""
Hello {user.name or 'User'},

Welcome to Mukh Swasthya 🦷

Your OTP for password reset is: {otp}

This OTP is valid for 10 minutes.

Thank you,
Mukh Swasthya Team
"""
        mail.send(msg)

        # Optional for local testing
        print("USER RESET OTP:", otp)

        return jsonify({"message": "If the account exists, OTP has been sent"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Internal email error: {str(e)}"}), 500

# ================= USER FORGOT PASSWORD - VERIFY OTP =================
@app.route("/user/forgot-password/verify-otp", methods=["POST"])
def user_verify_forgot_password_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()
        otp = data.get("otp", "").strip()

        if not email or not otp:
            return jsonify({"error": "email and otp are required"}), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"error": "Invalid OTP"}), 400

        if not user.reset_code or user.reset_code != otp:
            return jsonify({"error": "Invalid OTP"}), 400

        if not user.reset_expiry or datetime.utcnow() > user.reset_expiry:
            return jsonify({"error": "OTP expired"}), 400

        return jsonify({"message": "OTP verified successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= USER FORGOT PASSWORD - RESET PASSWORD =================
@app.route("/user/forgot-password/reset", methods=["POST"])
def user_reset_password_with_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()
        otp = data.get("otp", "").strip()
        new_password = data.get("new_password", "").strip()
        confirm_password = data.get("confirm_password", "").strip()

        if not email or not otp or not new_password or not confirm_password:
            return jsonify({
                "error": "email, otp, new_password and confirm_password are required"
            }), 400

        if new_password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        if len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"error": "Invalid request"}), 400

        if not user.reset_code or user.reset_code != otp:
            return jsonify({"error": "Invalid OTP"}), 400

        if not user.reset_expiry or datetime.utcnow() > user.reset_expiry:
            return jsonify({"error": "OTP expired"}), 400

        # Keep this consistent with your CURRENT login logic
        user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")

        # Clear OTP after successful reset
        user.reset_code = None
        user.reset_expiry = None

        db.session.commit()

        return jsonify({"message": "Password reset successfully", "role": "user"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= DEALER FORGOT PASSWORD - SEND OTP =================
@app.route("/dealer/forgot-password/send-otp", methods=["POST"])
def dealer_send_forgot_password_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"error": "email is required"}), 400

        dealer = Dealer.query.filter_by(email=email).first()

        # do not reveal whether email exists
        if not dealer:
            return jsonify({"message": "If the account exists, OTP has been sent"}), 200

        otp = str(random.randint(100000, 999999))

        dealer.reset_code = otp
        dealer.reset_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()

        msg = Message(
            subject="Mukh Swasthya Dealer Password Reset OTP",
            recipients=[email]
        )
        msg.body = f"""
Hello {dealer.name or 'Dealer'},

Welcome to Mukh Swasthya.

Your OTP for dealer password reset is: {otp}

This OTP is valid for 10 minutes.

Thank you,
Mukh Swasthya Team
"""
        mail.send(msg)

        print("DEALER RESET OTP:", otp)

        return jsonify({"message": "If the account exists, OTP has been sent"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Internal dealer email error: {str(e)}"}), 500

# ================= DEALER FORGOT PASSWORD - VERIFY OTP =================
@app.route("/dealer/forgot-password/verify-otp", methods=["POST"])
def dealer_verify_forgot_password_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()
        otp = data.get("otp", "").strip()

        if not email or not otp:
            return jsonify({"error": "email and otp are required"}), 400

        dealer = Dealer.query.filter_by(email=email).first()

        if not dealer:
            return jsonify({"error": "Invalid OTP"}), 400

        if not dealer.reset_code or dealer.reset_code != otp:
            return jsonify({"error": "Invalid OTP"}), 400

        if not dealer.reset_expiry or datetime.utcnow() > dealer.reset_expiry:
            return jsonify({"error": "OTP expired"}), 400

        return jsonify({"message": "OTP verified successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= DEALER FORGOT PASSWORD - RESET PASSWORD =================
@app.route("/dealer/forgot-password/reset", methods=["POST"])
def dealer_reset_password_with_otp():
    try:
        data = get_request_data()
        email = data.get("email", "").strip().lower()
        otp = data.get("otp", "").strip()
        new_password = data.get("new_password", "").strip()
        confirm_password = data.get("confirm_password", "").strip()

        if not email or not otp or not new_password or not confirm_password:
            return jsonify({
                "error": "email, otp, new_password and confirm_password are required"
            }), 400

        if new_password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        if len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        dealer = Dealer.query.filter_by(email=email).first()

        if not dealer:
            return jsonify({"error": "Invalid request"}), 400

        if not dealer.reset_code or dealer.reset_code != otp:
            return jsonify({"error": "Invalid OTP"}), 400

        if not dealer.reset_expiry or datetime.utcnow() > dealer.reset_expiry:
            return jsonify({"error": "OTP expired"}), 400

        dealer.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
        dealer.reset_code = None
        dealer.reset_expiry = None

        db.session.commit()

        return jsonify({"message": "Dealer password reset successfully", "role": "dealer"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= GET USER PROFILE ROUTE =================
@app.route("/api/user/profile/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user_profile(user_id):
    try:
        # Join with Dealer to get name and location
        result = db.session.query(
            User,
            Dealer.name.label("dealer_name"),
            Dealer.location.label("dealer_loc"),
            Dealer.address.label("dealer_addr")
        ).outerjoin(
            Dealer, User.dealer_id == Dealer.id
        ).filter(User.id == user_id).first()

        if not result:
            return jsonify({"error": "User not found"}), 404

        user, d_name, d_loc, d_addr = result
        
        profile_image_url = None
        if user.profile_image:
            profile_image_url = f"{request.host_url}{user.profile_image}"

        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "age": user.age,
            "gender": user.gender,
            "education": user.education,
            "employment": user.employment,
            "address": user.address,
            "pds_card_no": user.pds_card_no,
            "pds_verified": bool(user.pds_verified),
            "pds_linked_at": str(user.pds_linked_at) if user.pds_linked_at else None,
            "profile_image": user.profile_image,
            "created_by_type": user.created_by_type or "SELF",
            "dealer_id": user.dealer_id,
            "dealer_name": d_name,
            "dealer_location": d_loc or d_addr
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= UPLOAD USER PROFILE PICTURE =================
@app.route("/api/user/upload-profile-picture/<int:user_id>", methods=["POST"])
@jwt_required()
def upload_user_profile_picture(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        if 'profile_image' not in request.files:
            return jsonify({"error": "profile_image file is required"}), 400

        image = request.files['profile_image']
        if image.filename == '':
            return jsonify({"error": "No file selected"}), 400

        filename = secure_filename(image.filename)
        unique_filename = f"user_{user_id}_{uuid.uuid4().hex[:8]}_{filename}"
        upload_folder = os.path.join(app.root_path, 'uploads', 'profile_pictures')
        os.makedirs(upload_folder, exist_ok=True)

        full_path = os.path.join(upload_folder, unique_filename)
        image.save(full_path)

        relative_path = f"uploads/profile_pictures/{unique_filename}"
        user.profile_image = relative_path
        db.session.commit()

        return jsonify({
            "message": "Profile picture uploaded successfully",
            "profile_image": f"{request.host_url}{relative_path}"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500




# ================= UPDATE BRUSHING COUNT ROUTE =================
@app.route("/user/update-brush-count/<int:member_id>", methods=["PUT"])
def update_brush_count(member_id):
    data = request.get_json()

    if "weekly_brush_count" not in data:
        return jsonify({"error": "weekly_brush_count is required"}), 400

    member = FamilyMember.query.get(member_id)

    if not member:
        return jsonify({"error": "Family member not found"}), 404

    member.weekly_brush_count = data["weekly_brush_count"]

    db.session.commit()

    return jsonify({"message": "Brush count updated successfully"}), 200


# ================= BRUSHING CHECK-IN ROUTE =================
@app.route("/user/checkin", methods=["POST"])
def brushing_checkin():
    try:
        data = request.get_json()

        user_id = data.get("user_id")
        member_id = data.get("member_id")
        session = data.get("session")

        if not user_id:
            return jsonify({"error": "user_id required"}), 400

        session = session.upper().strip()

        if session not in ["MORNING", "EVENING"]:
            return jsonify({"message": "Invalid session"}), 400

        today = datetime.utcnow().date()

        if member_id is not None:
            member = db.session.execute(text("""
                SELECT id, user_id
                FROM family_members
                WHERE id = :member_id
            """), {"member_id": member_id}).fetchone()

            if not member:
                return jsonify({"error": "Family member not found"}), 404

            if member.user_id != int(user_id):
                return jsonify({"error": "This member does not belong to the user"}), 403

            existing = BrushingCheckin.query.filter_by(
                user_id=user_id,
                member_id=member_id,
                checkin_date=today,
                session=session
            ).first()

        else:
            existing = BrushingCheckin.query.filter(
                BrushingCheckin.user_id == user_id,
                BrushingCheckin.member_id.is_(None),
                BrushingCheckin.checkin_date == today,
                BrushingCheckin.session == session
            ).first()

        if existing:
            return jsonify({
                "message": "Already checked in for this session"
            }), 400

        db.session.execute(text("""
            INSERT INTO brushing_checkins (user_id, member_id, checkin_date, session)
            VALUES (:user_id, :member_id, :today, :session)
        """), {
            "user_id": user_id,
            "member_id": member_id,
            "today": today,
            "session": session
        })

        db.session.commit()

        return jsonify({
            "message": "Check-in saved successfully",
            "user_id": user_id,
            "member_id": member_id,
            "session": session,
            "date": str(today)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/user/weekly-progress/<int:user_id>', methods=['GET'])
def get_weekly_progress(user_id):
    from datetime import date, timedelta

    member_id = request.args.get("member_id", type=int)

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    query = BrushingCheckin.query.filter(
        BrushingCheckin.user_id == user_id,
        BrushingCheckin.checkin_date >= start_of_week,
        BrushingCheckin.checkin_date <= end_of_week
    )

    if member_id is None:
        query = query.filter(BrushingCheckin.member_id.is_(None))
    else:
        member = FamilyMember.query.filter_by(id=member_id, user_id=user_id).first()
        if not member:
            return jsonify({"error": "Family member not found for this user"}), 404
        query = query.filter(BrushingCheckin.member_id == member_id)

    rows = query.all()

    session_map = {}
    for i in range(7):
        d = start_of_week + timedelta(days=i)
        session_map[str(d)] = {
            "morning": False,
            "evening": False
        }

    for row in rows:
        key = str(row.checkin_date)
        if key in session_map:
            if row.session == "MORNING":
                session_map[key]["morning"] = True
            elif row.session == "EVENING":
                session_map[key]["evening"] = True

    total_completed = sum(
        int(day["morning"]) + int(day["evening"])
        for day in session_map.values()
    )

    return jsonify({
        "week_start": str(start_of_week),
        "week_end": str(end_of_week),
        "total_completed": total_completed,
        "total_possible": 14,
        "sessions": [
            {
                "date": day,
                "morning": value["morning"],
                "evening": value["evening"]
            }
            for day, value in session_map.items()
        ]
    }), 200


@app.route('/api/user/monthly-usage/<int:user_id>', methods=['GET'])
def get_monthly_usage(user_id):
    from datetime import date, timedelta
    from calendar import monthrange

    member_id = request.args.get("member_id", type=int)
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    start_of_month = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_of_month = date(year, month, last_day)

    query = BrushingCheckin.query.filter(
        BrushingCheckin.user_id == user_id,
        BrushingCheckin.checkin_date >= start_of_month,
        BrushingCheckin.checkin_date <= end_of_month
    )

    if member_id is None:
        query = query.filter(BrushingCheckin.member_id.is_(None))
    else:
        member = FamilyMember.query.filter_by(id=member_id, user_id=user_id).first()
        if not member:
            return jsonify({"error": "Family member not found for this user"}), 404
        query = query.filter(BrushingCheckin.member_id == member_id)

    rows = query.all()

    session_map = {}
    for i in range(last_day):
        d = start_of_month + timedelta(days=i)
        session_map[str(d)] = {
            "morning": False,
            "evening": False
        }

    for row in rows:
        key = str(row.checkin_date)
        if key in session_map:
            if row.session == "MORNING":
                session_map[key]["morning"] = True
            elif row.session == "EVENING":
                session_map[key]["evening"] = True

    total_completed = sum(
        int(day["morning"]) + int(day["evening"])
        for day in session_map.values()
    )

    return jsonify({
        "month_start": str(start_of_month),
        "month_end": str(end_of_month),
        "total_completed": total_completed,
        "total_possible": last_day * 2,
        "sessions": [
            {
                "date": day,
                "morning": value["morning"],
                "evening": value["evening"]
            }
            for day, value in session_map.items()
        ]
    }), 200



# ================= GET DEALER PROFILE ROUTE =================
@app.route("/dealer/profile/<int:dealer_id>", methods=["GET"])
@jwt_required()
def get_dealer_profile(dealer_id):
    dealer = Dealer.query.get(dealer_id)
    if not dealer:
        return jsonify({"error": "Dealer not found"}), 404

    return jsonify({
        "id": dealer.id,
        "name": dealer.name,
        "email": dealer.email,
        "phone": dealer.phone,
        "company_name": dealer.company_name,
        "address": dealer.address,
        "city": dealer.city,
        "state": dealer.state,
        "dealer_qr_value": dealer.dealer_qr_value,
        "dealer_qr_image": dealer.dealer_qr_image
    }), 200


# ================= UPDATE DEALER PROFILE ROUTE =================
@app.route("/dealer/update-profile/<int:dealer_id>", methods=["PUT"])
@jwt_required()
def update_dealer_profile(dealer_id):
    data = get_request_data()

    dealer = Dealer.query.get(dealer_id)
    if not dealer:
        return jsonify({"error": "Dealer not found"}), 404

    if "name" in data:
        dealer.name = data["name"]

    if "phone" in data:
        dealer.phone = data["phone"]

    if "company_name" in data:
        dealer.company_name = data["company_name"]

    if "address" in data:
        dealer.address = data["address"]
        # Sync to dealer_locations
        loc = DealerLocation.query.filter_by(dealer_id=dealer_id).first()
        if loc:
            loc.location_name = data["address"]
        else:
            new_loc = DealerLocation(dealer_id=dealer_id, location_name=data["address"])
            db.session.add(new_loc)
        
        # Also sync to dealer.location field for redundancy
        dealer.location = data["address"]

    if "city" in data:
        dealer.city = data["city"]

    if "state" in data:
        dealer.state = data["state"]

    if "username" in data:
        dealer.username = data["username"]

    db.session.commit()

    return jsonify({"message": "Dealer updated successfully"}), 200


@app.route("/dealer/change-password", methods=["PUT"])
@jwt_required()
def change_dealer_password():
    from flask_jwt_extended import get_jwt_identity
    data = get_request_data()
    
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if not current_password or not new_password:
        return jsonify({"error": "current_password and new_password are required"}), 400
        
    dealer_id = get_jwt_identity()
    dealer = Dealer.query.get(dealer_id)
    
    if not dealer:
         return jsonify({"error": "Dealer not found"}), 404
         
    if dealer.password_hash != current_password:
         return jsonify({"error": "Incorrect current password"}), 401
         
    dealer.password_hash = new_password
    db.session.commit()
    
    return jsonify({"message": "Password changed successfully"}), 200


@app.route("/user/change-password", methods=["PUT"])
@jwt_required()
def change_user_password():
    from flask_jwt_extended import get_jwt_identity
    data = get_request_data()
    
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if not current_password or not new_password:
        return jsonify({"error": "current_password and new_password are required"}), 400
        
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
         return jsonify({"error": "User not found"}), 404
         
    if not bcrypt.check_password_hash(user.password_hash, current_password):
         return jsonify({"error": "Incorrect current password"}), 401
         
    user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    db.session.commit()
    
    return jsonify({"message": "Password changed successfully"}), 200


# ================= UPDATE USER PROFILE ROUTE =================
@app.route("/user/update-profile/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user_profile(user_id):
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    if "name" in data:
        user.name = data["name"]
    if "phone" in data:
        user.phone = data["phone"]
    if "email" in data:
        existing = User.query.filter_by(email=data["email"]).first()
        if existing and existing.id != user_id:
            return jsonify({"error": "Email already in use"}), 400
        user.email = data["email"]
    if "password" in data:
        user.password_hash = data["password"]
    if "age" in data:
        user.age = str(data["age"])
    if "gender" in data:
        user.gender = data["gender"]
    if "education" in data:
        user.education = data["education"]
    if "employment" in data:
        user.employment = data["employment"]
    if "address" in data:
        user.address = data["address"]

    db.session.commit()

    return jsonify({"message": "User profile updated successfully"}), 200


# ================= NEARBY CLINICS ROUTE (OpenStreetMap / Overpass) =================
@app.route("/user/nearby-clinics", methods=["GET"])
def get_nearby_clinics():
    lat = request.args.get("latitude", type=float)
    lng = request.args.get("longitude", type=float)
    max_km = request.args.get("max_km", default=15.0, type=float)

    if lat is None or lng is None:
        return jsonify({"error": "latitude and longitude are required"}), 400

    if not (-90 <= lat <= 90):
        return jsonify({"error": "latitude must be between -90 and 90"}), 400

    if not (-180 <= lng <= 180):
        return jsonify({"error": "longitude must be between -180 and 180"}), 400

    if max_km <= 0:
        return jsonify({"error": "max_km must be greater than 0"}), 400

    try:
        radius_m = int(max_km * 1000)

        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="dentist"](around:{radius_m},{lat},{lng});
          way["amenity"="dentist"](around:{radius_m},{lat},{lng});
          relation["amenity"="dentist"](around:{radius_m},{lat},{lng});

          node["healthcare"="dentist"](around:{radius_m},{lat},{lng});
          way["healthcare"="dentist"](around:{radius_m},{lat},{lng});
          relation["healthcare"="dentist"](around:{radius_m},{lat},{lng});

          node["clinic"="dental"](around:{radius_m},{lat},{lng});
          way["clinic"="dental"](around:{radius_m},{lat},{lng});
          relation["clinic"="dental"](around:{radius_m},{lat},{lng});
        );
        out center tags;
        """

        overpass_urls = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"
        ]

        session = build_requests_session()
        last_error = None

        for url in overpass_urls:
            try:
                response = session.post(
                    url,
                    data=overpass_query,
                    headers={
                        "User-Agent": "DigitalPDS/1.0 (nearby dental clinics lookup)"
                    },
                    timeout=(10, 30)
                )

                if response.status_code != 200:
                    last_error = response.text
                    continue

                data = response.json()
                elements = data.get("elements", [])

                seen = set()
                results = []

                for element in elements:
                    tags = element.get("tags", {})

                    place_lat = element.get("lat")
                    place_lng = element.get("lon")

                    if place_lat is None or place_lng is None:
                        center = element.get("center", {})
                        place_lat = center.get("lat")
                        place_lng = center.get("lon")

                    if place_lat is None or place_lng is None:
                        continue

                    name = tags.get("name", "Dental Clinic")

                    address_parts = [
                        tags.get("addr:housename"),
                        tags.get("addr:housenumber"),
                        tags.get("addr:street"),
                        tags.get("addr:suburb"),
                        tags.get("addr:city"),
                        tags.get("addr:district"),
                        tags.get("addr:state")
                    ]
                    address = ", ".join([part for part in address_parts if part])

                    district = tags.get("addr:district") or tags.get("addr:city") or ""

                    phone = (
                        tags.get("phone")
                        or tags.get("contact:phone")
                        or tags.get("mobile")
                        or tags.get("contact:mobile")
                    )

                    website = tags.get("website") or tags.get("contact:website")

                    distance_km = haversine(lat, lng, place_lat, place_lng)

                    unique_key = (name.strip().lower(), round(place_lat, 5), round(place_lng, 5))
                    if unique_key in seen:
                        continue
                    seen.add(unique_key)

                    results.append({
                        "id": str(element.get("id")),
                        "clinic_name": name,
                        "address": address,
                        "district": district,
                        "contact_number": phone,
                        "latitude": place_lat,
                        "longitude": place_lng,
                        "booking_available": False,
                        "distance_km": distance_km,
                        "website": website,
                        "google_maps_uri": f"https://www.google.com/maps/search/?api=1&query={place_lat},{place_lng}"
                    })

                results.sort(key=lambda x: x["distance_km"])
                return jsonify(results), 200

            except requests.exceptions.Timeout:
                last_error = "OpenStreetMap request timed out"
                continue
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                continue
            except ValueError:
                last_error = "Invalid JSON response from OpenStreetMap service"
                continue

        return jsonify({
            "error": "OpenStreetMap request failed",
            "status_code": 504,
            "details": last_error or "Nearby clinic service temporarily unavailable"
        }), 504

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= ADD DEALER STOCK ROUTE =================
@app.route("/dealer/add-stock", methods=["POST"])
def add_dealer_stock():
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received. Send JSON or form-data."}), 400

        dealer_id = data.get("dealer_id")
        item_name = normalize_stock_item_name(data.get("item_name"))
        quantity = int(data.get("quantity", 0) or 0)

        if not dealer_id:
            return jsonify({"error": "dealer_id is required"}), 400

        if not item_name:
            return jsonify({"error": "item_name is required or invalid"}), 400
        if quantity <= 0:
            return jsonify({"error": "quantity must be greater than 0"}), 400

        stock = DealerStock.query.filter_by(
            dealer_id=int(dealer_id),
            item_name=item_name
        ).first()

        if stock:
            stock.quantity += quantity
        else:
            stock = DealerStock(
                dealer_id=int(dealer_id),
                item_name=item_name,
                quantity=quantity
            )
            db.session.add(stock)

        db.session.commit()
        return jsonify({"message": "Stock added successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= VIEW DEALER STOCK ROUTE =================
@app.route("/dealer/view-stock/<int:dealer_id>", methods=["GET"])
def view_dealer_stock(dealer_id):
    stock = DealerStock.query.filter_by(dealer_id=dealer_id).all()

    result = []
    for item in stock:
        result.append({
            "id": item.id,
            "item_name": item.item_name,
            "quantity": item.quantity
        })

    return jsonify(result), 200


# ================= UPDATE DEALER STOCK ROUTE =================
@app.route("/dealer/update-stock", methods=["PUT"])
def update_dealer_stock():
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received. Send JSON or form-data."}), 400

        dealer_id = data.get("dealer_id")
        item_name = normalize_stock_item_name(data.get("item_name"))
        quantity = int(data.get("quantity", 0) or 0)

        if not dealer_id:
            return jsonify({"error": "dealer_id is required"}), 400
        if not item_name:
            return jsonify({"error": "item_name is required or invalid"}), 400
        if quantity < 0:
            return jsonify({"error": "quantity cannot be negative"}), 400

        stock = DealerStock.query.filter_by(
            dealer_id=int(dealer_id),
            item_name=item_name
        ).first()

        if not stock:
            return jsonify({"error": "Stock item not found"}), 404

        stock.quantity = quantity
        db.session.commit()

        return jsonify({
            "message": "Stock updated successfully",
            "dealer_id": stock.dealer_id,
            "item_name": stock.item_name,
            "new_quantity": stock.quantity
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= DEALER GENERATE KIT ROUTE =================
@app.route("/dealer/generate-kit", methods=["POST"])
def generate_kit():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    required_fields = ["dealer_id", "beneficiary_id"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    kit_id = str(uuid.uuid4())
    expiry_time = datetime.utcnow() + timedelta(hours=24)

    new_kit = KitDistribution(
        dealer_id=data["dealer_id"],
        beneficiary_id=data["beneficiary_id"],
        kit_unique_id=kit_id,
        expiry=expiry_time
    )

    db.session.add(new_kit)
    db.session.commit()

    return jsonify({
        "message": "Kit generated successfully",
        "kit_unique_id": kit_id,
        "expiry": expiry_time
    }), 201


@app.route("/dealer/request-stock", methods=["POST"])
def request_stock():
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received. Send JSON or form-data."}), 400

        dealer_id = data.get("dealer_id")
        total_kits = int(data.get("total_kits", 0) or 0)
        urgency = data.get("urgency", "Normal")

        if not dealer_id:
            return jsonify({"error": "dealer_id is required"}), 400

        if total_kits <= 0:
            return jsonify({"error": "Total kits must be greater than zero"}), 400

        dealer = Dealer.query.get(int(dealer_id))
        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404

        request_group_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"

        new_request = StockRequest(
            request_id=request_group_id,
            dealer_id=int(dealer_id),
            item_name="KIT",
            requested_quantity=total_kits,
            total_kits=total_kits,
            urgency=urgency,
            status="PENDING",
            dispatch_address=dealer.address,
            dispatch_city=dealer.city,
            dispatch_state=dealer.state
        )
        db.session.add(new_request)
        db.session.commit()

        return jsonify({
            "message": "Stock request sent successfully",
            "request_group_id": request_group_id,
            "total_kits": total_kits
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= ADMIN APPROVE STOCK ROUTE =================
@app.route("/admin/stock-requests", methods=["GET"])
def get_admin_stock_requests():
    requests_list = StockRequest.query.order_by(StockRequest.requested_at.desc()).all()

    result = []
    for req in requests_list:
        dealer = Dealer.query.get(req.dealer_id)

        normalized_item_name = normalize_stock_item_name(req.item_name)

        if normalized_item_name == "BRUSH":
            item_label = "Brush"
        elif normalized_item_name == "TOOTHPASTE":
            item_label = "Paste"
        elif normalized_item_name == "FLYER":
            item_label = "IEC Materials"
        else:
            item_label = "Unknown Item"

        result.append({
            "id": req.id,
            "request_id": req.request_id,
            "dealer_id": req.dealer_id,
            "dealer_name": dealer.name if dealer else f"Dealer #{req.dealer_id}",
            "location": dealer.company_name if dealer and dealer.company_name else "Not Available",
            "dealer_address": dealer.address if dealer else None,
            "contact_phone": dealer.phone if dealer else None,
            "kit_type": item_label,
            "item_name": req.item_name,
            "quantity": str(req.requested_quantity) + " Units",
            "total_kits": req.total_kits,
            "urgency": req.urgency,
            "status": req.status,
            "request_date": req.requested_at.strftime("%Y-%m-%d") if req.requested_at else "",
            "approved_at": str(req.reviewed_at) if req.status in ("APPROVED", "DISPATCHED", "DELIVERED") and req.reviewed_at else None,
            "rejected_at": str(req.reviewed_at) if req.status == "REJECTED" and req.reviewed_at else None,
            "dispatched_at": str(req.dispatched_at) if req.dispatched_at else None,
            "delivered_at": str(req.delivered_at) if req.delivered_at else None,
            "admin_note": req.admin_note,
            "courier_name": req.courier_name,
            "tracking_id": req.tracking_id,
            "dispatch_address": req.dispatch_address,
            "dispatch_city": req.dispatch_city,
            "dispatch_state": req.dispatch_state
        })

    return jsonify(result), 200


@app.route("/admin/stock-requests/<int:request_id>", methods=["GET"])
def get_admin_stock_request_detail(request_id):
    try:
        req = StockRequest.query.get(request_id)

        if not req:
            return jsonify({"error": "Stock request not found"}), 404

        dealer = Dealer.query.get(req.dealer_id)

        normalized_item_name = normalize_stock_item_name(req.item_name)
        if normalized_item_name == "BRUSH":
            item_label = "Brush"
        elif normalized_item_name == "TOOTHPASTE":
            item_label = "Paste"
        elif normalized_item_name == "FLYER":
            item_label = "IEC Materials"
        elif normalized_item_name == "KIT":
            item_label = "Kit"
        else:
            item_label = req.item_name or "Unknown Item"

        return jsonify({
            "id": req.id,
            "request_id": req.request_id,
            "dealer_id": req.dealer_id,
            "dealer_name": dealer.name if dealer else f"Dealer #{req.dealer_id}",
            "dealer_address": dealer.address if dealer else None,
            "dealer_username": dealer.username if dealer else None,
            "contact_phone": dealer.phone if dealer else None,
            "location": dealer.company_name if dealer and dealer.company_name else "Not Available",
            "kit_type": item_label,
            "item_name": req.item_name,
            "requested_quantity": req.requested_quantity,
            "quantity": f"{req.requested_quantity} Units",
            "total_kits": req.total_kits,
            "urgency": req.urgency,
            "status": req.status,
            "requested_at": req.requested_at.isoformat() if req.requested_at else None,
            "request_date": req.requested_at.strftime("%Y-%m-%d") if req.requested_at else "",
            "reviewed_at": req.reviewed_at.isoformat() if req.reviewed_at else None,
            "approved_at": req.reviewed_at.isoformat() if req.status in ("APPROVED", "DISPATCHED", "DELIVERED") and req.reviewed_at else None,
            "rejected_at": req.reviewed_at.isoformat() if req.status == "REJECTED" and req.reviewed_at else None,
            "dispatched_at": req.dispatched_at.isoformat() if req.dispatched_at else None,
            "delivered_at": req.delivered_at.isoformat() if req.delivered_at else None,
            "admin_note": None if req.admin_note == "null" else req.admin_note,
            "courier_name": req.courier_name,
            "tracking_id": req.tracking_id,
            "dispatch_address": req.dispatch_address,
            "dispatch_city": req.dispatch_city,
            "dispatch_state": req.dispatch_state
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/approve-stock/<int:request_id>", methods=["PUT"])
def approve_stock(request_id):
    stock_request = StockRequest.query.get(request_id)

    if not stock_request:
        return jsonify({"error": "Request not found"}), 404

    if stock_request.status != "PENDING":
        return jsonify({"error": "Only pending requests can be approved"}), 400

    stock_request.status = "APPROVED"
    stock_request.reviewed_at = datetime.utcnow()
    data = get_request_data()
    stock_request.admin_note = data.get("admin_note", stock_request.admin_note)

    db.session.commit()

    return jsonify({"message": "Stock request approved successfully"}), 200


# ================= ADMIN DISPATCH STOCK ROUTE =================
@app.route("/admin/dispatch-stock/<int:request_id>", methods=["PUT"])
def dispatch_stock(request_id):
    try:
        stock_request = StockRequest.query.get(request_id)

        if not stock_request:
            return jsonify({"error": "Request not found"}), 404

        if stock_request.status != "APPROVED":
            return jsonify({"error": "Only approved requests can be dispatched"}), 400

        data = get_request_data()

        courier_name = data.get("courier_name")
        tracking_id = data.get("tracking_id")

        if not courier_name:
            return jsonify({"error": "courier_name is required"}), 400

        if not tracking_id:
            return jsonify({"error": "tracking_id is required"}), 400

        dealer = Dealer.query.get(stock_request.dealer_id)
        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404

        normalized_item_name = normalize_stock_item_name(stock_request.item_name)

        if not normalized_item_name:
            return jsonify({"error": f"Invalid item_name: {stock_request.item_name}"}), 400

        stock_request.status = "DISPATCHED"
        stock_request.dispatched_at = datetime.utcnow()
        stock_request.item_name = normalized_item_name
        stock_request.courier_name = courier_name
        stock_request.tracking_id = tracking_id
        
        new_note = data.get("admin_note")
        if new_note and new_note.strip():
            stock_request.admin_note = new_note.strip()

        # snapshot from dealer profile
        stock_request.dispatch_address = dealer.address
        stock_request.dispatch_city = dealer.city
        stock_request.dispatch_state = dealer.state

        # NOTE: Stock is NOT updated here. It will be updated when dealer confirms delivery.

        db.session.commit()
        return jsonify({"message": "Stock dispatched successfully. Awaiting dealer confirmation."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= DEALER CONFIRM DELIVERY ROUTE =================
@app.route("/dealer/confirm-delivery/<request_group_id>", methods=["PUT"])
def confirm_delivery(request_group_id):
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received"}), 400

        dealer_id = data.get("dealer_id")
        if not dealer_id:
            return jsonify({"error": "dealer_id is required"}), 400

        dealer_id = int(dealer_id)

        # Find all items in this request group
        items = StockRequest.query.filter_by(request_id=request_group_id).all()

        if not items:
            return jsonify({"error": "Request group not found"}), 404

        # Validate dealer ownership
        if items[0].dealer_id != dealer_id:
            return jsonify({"error": "Unauthorized: This request belongs to another dealer"}), 403

        # Check all items are DISPATCHED
        non_dispatched = [i for i in items if i.status != "DISPATCHED"]
        if non_dispatched:
            already_delivered = any(i.status == "DELIVERED" for i in non_dispatched)
            if already_delivered:
                return jsonify({"error": "This shipment has already been confirmed as received"}), 400
            return jsonify({"error": "Only dispatched requests can be confirmed as delivered"}), 400

        # Update each item and add stock
        now = datetime.utcnow()
        stock_updates = []

        for item in items:
            item.status = "DELIVERED"
            item.delivered_at = now

            # Each kit corresponds to 1 BRUSH, 1 TOOTHPASTE, 1 FLYER
            num_kits = item.total_kits
            
            items_in_kit = ["BRUSH", "TOOTHPASTE", "FLYER"]
            
            for kit_item in items_in_kit:
                stock = DealerStock.query.filter_by(
                    dealer_id=dealer_id,
                    item_name=kit_item
                ).first()

                if stock:
                    stock.quantity += num_kits
                else:
                    db.session.add(DealerStock(
                        dealer_id=dealer_id,
                        item_name=kit_item,
                        quantity=num_kits
                    ))

                stock_updates.append({
                    "item": kit_item,
                    "quantity_added": num_kits
                })

        db.session.commit()

        return jsonify({
            "message": "Delivery confirmed successfully. Stock has been updated.",
            "request_group_id": request_group_id,
            "delivered_at": str(now),
            "stock_updates": stock_updates
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= ADMIN REJECT STOCK ROUTE =================
@app.route("/admin/reject-stock/<int:request_id>", methods=["PUT"])
def reject_stock(request_id):
    stock_request = StockRequest.query.get(request_id)

    if not stock_request:
        return jsonify({"error": "Request not found"}), 404

    if stock_request.status != "PENDING":
        return jsonify({"error": "Only pending requests can be rejected"}), 400

    data = get_request_data()
    reason = data.get("reason") if data else None

    stock_request.status = "REJECTED"
    stock_request.reviewed_at = datetime.utcnow()
    stock_request.admin_note = reason

    db.session.commit()

    return jsonify({"message": "Stock request rejected successfully"}), 200


# ================= USER CONFIRM KIT ROUTE =================
@app.route("/user/confirm-kit", methods=["POST"])
def confirm_kit():
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received. Send JSON or form-data."}), 400

        kit_unique_id = data.get("kit_unique_id")
        if not kit_unique_id:
            return jsonify({"error": "kit_unique_id is required"}), 400

        brush_received = int(data.get("brush_received", 0) or 0)
        paste_received = int(data.get("paste_received", 0) or 0)
        iec_received = int(data.get("iec_received", 0) or 0)
        old_kit_returned = to_bool(data.get("old_kit_returned", False))

        if brush_received < 0 or paste_received < 0 or iec_received < 0:
            return jsonify({"error": "Received item counts cannot be negative"}), 400

        kit = KitDistribution.query.filter_by(kit_unique_id=kit_unique_id).first()

        if not kit:
            return jsonify({"error": "Invalid kit ID"}), 404

        if kit.status == "CONFIRMED":
            return jsonify({"error": "Kit already confirmed"}), 400

        if kit.expiry and datetime.utcnow() > kit.expiry:
            return jsonify({"error": "Kit expired"}), 400

        brush_stock = DealerStock.query.filter_by(
            dealer_id=kit.dealer_id,
            item_name="BRUSH"
        ).first()

        paste_stock = DealerStock.query.filter_by(
            dealer_id=kit.dealer_id,
            item_name="TOOTHPASTE"
        ).first()

        iec_stock = DealerStock.query.filter_by(
            dealer_id=kit.dealer_id,
            item_name="FLYER"
        ).first()

        if brush_received > 0:
            if not brush_stock or brush_stock.quantity < brush_received:
                return jsonify({"error": "Insufficient BRUSH stock"}), 400

        if paste_received > 0:
            if not paste_stock or paste_stock.quantity < paste_received:
                return jsonify({"error": "Insufficient TOOTHPASTE stock"}), 400

        if iec_received > 0:
            if not iec_stock or iec_stock.quantity < iec_received:
                return jsonify({"error": "Insufficient IEC/FLYER stock"}), 400

        if brush_stock and brush_received > 0:
            brush_stock.quantity -= brush_received

        if paste_stock and paste_received > 0:
            paste_stock.quantity -= paste_received

        if iec_stock and iec_received > 0:
            iec_stock.quantity -= iec_received

        kit.status = "CONFIRMED"
        kit.confirmed_at = datetime.utcnow()
        kit.brush_received = brush_received
        kit.paste_received = paste_received
        kit.iec_received = iec_received
        kit.old_kit_returned = old_kit_returned

        db.session.commit()

        return jsonify({
            "message": "Kit confirmed successfully",
            "data": {
                "kit_unique_id": kit.kit_unique_id,
                "status": kit.status,
                "brush_received": kit.brush_received,
                "paste_received": kit.paste_received,
                "iec_received": kit.iec_received,
                "old_kit_returned": bool(kit.old_kit_returned),
                "old_kit_return_status": "RETURNED" if kit.old_kit_returned else "NOT_RETURNED",
                "show_red_alert": not bool(kit.old_kit_returned),
                "confirmed_at": str(kit.confirmed_at)
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= USER CONFIRM KIT BY DEALER QR =================
@app.route("/user/confirm-kit-by-dealer-qr", methods=["POST"])
def confirm_kit_by_dealer_qr():
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received"}), 400

        dealer_qr_value = data.get("dealer_qr_value")
        beneficiary_id = data.get("beneficiary_id")

        if not dealer_qr_value or not beneficiary_id:
            return jsonify({"error": "dealer_qr_value and beneficiary_id required"}), 400

        dealer_qr_value = normalize_dealer_qr_value(dealer_qr_value)

        dealer = Dealer.query.filter_by(dealer_qr_value=dealer_qr_value).first()
        if not dealer:
            return jsonify({"error": "Invalid dealer QR"}), 404

        dealer_id = dealer.id
        user = User.query.get(int(beneficiary_id))

        if not user:
            return jsonify({"error": "Beneficiary not found"}), 404

        if not user.pds_verified:
            return jsonify({"error": "PDS not linked"}), 400

        if user.dealer_id is None:
            return jsonify({
                "error": "Dealer not assigned",
                "message": "Complete dealer assignment first"
            }), 400
        elif user.dealer_id != dealer_id:
            return jsonify({
                "error": "Dealer mismatch",
                "message": "User already assigned to another dealer"
            }), 403
        else:
            dealer_assigned = False

        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        existing = KitDistribution.query.filter(
            KitDistribution.beneficiary_id == user.id,
            KitDistribution.status == "CONFIRMED",
            KitDistribution.confirmed_at >= month_start
        ).first()

        if existing:
            return jsonify({"error": "Kit already received this month"}), 400

        new_distribution = KitDistribution(
            beneficiary_id=user.id,
            dealer_id=dealer_id,
            kit_unique_id=str(uuid.uuid4()),
            status="PENDING",
            expiry=datetime.utcnow() + timedelta(hours=24),
            confirmation_mode="USER_QR_SCAN",
            old_kit_returned=False,
            brush_received=0,
            paste_received=0,
            iec_received=0
        )

        db.session.add(new_distribution)
        db.session.commit()

        return jsonify({
            "message": "Distribution created successfully. Please confirm kit receipt.",
            "dealer_assigned_now": dealer_assigned,
            "dealer_id": dealer_id,
            "distribution_id": new_distribution.id,
            "kit_unique_id": new_distribution.kit_unique_id,
            "status": new_distribution.status
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= DEALER MANUAL CONFIRM DISTRIBUTION ROUTE =================
@app.route("/dealer/confirm-distribution", methods=["POST"])
def dealer_confirm_distribution():
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received"}), 400

        dealer_id = data.get("dealer_id")
        beneficiary_id = data.get("beneficiary_id")
        brush_received = int(data.get("brush_received", 0) or 0)
        paste_received = int(data.get("paste_received", 0) or 0)
        iec_received = int(data.get("iec_received", 0) or 0)
        old_kit_returned = to_bool(data.get("old_kit_returned", False))

        if not dealer_id or not beneficiary_id:
            return jsonify({"error": "dealer_id and beneficiary_id are required"}), 400

        if brush_received < 0 or paste_received < 0 or iec_received < 0:
            return jsonify({"error": "Item counts cannot be negative"}), 400

        if brush_received == 0 and paste_received == 0 and iec_received == 0:
            return jsonify({"error": "At least one item quantity must be greater than zero"}), 400

        dealer_id = int(dealer_id)
        beneficiary_id = int(beneficiary_id)

        dealer = Dealer.query.get(dealer_id)
        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404

        user = User.query.get(beneficiary_id)
        if not user:
            return jsonify({"error": "Beneficiary not found"}), 404

        if not user.pds_verified:
            return jsonify({"error": "PDS not verified"}), 400

        if user.dealer_id is None:
            return jsonify({
                "error": "Dealer not assigned",
                "message": "Complete dealer assignment first"
            }), 400
        elif user.dealer_id != dealer_id:
            return jsonify({
                "error": "Dealer mismatch",
                "message": "User belongs to another dealer"
            }), 403

        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        confirmed_kit = KitDistribution.query.filter(
            KitDistribution.beneficiary_id == beneficiary_id,
            KitDistribution.status == "CONFIRMED",
            KitDistribution.confirmed_at >= month_start
        ).first()

        if confirmed_kit:
            return jsonify({
                "error": "Kit already distributed this month",
                "existing_kit_unique_id": confirmed_kit.kit_unique_id
            }), 400

        brush_stock = DealerStock.query.filter_by(
            dealer_id=dealer_id,
            item_name="BRUSH"
        ).first()

        paste_stock = DealerStock.query.filter_by(
            dealer_id=dealer_id,
            item_name="TOOTHPASTE"
        ).first()

        iec_stock = DealerStock.query.filter_by(
            dealer_id=dealer_id,
            item_name="FLYER"
        ).first()

        if brush_received > 0 and (not brush_stock or brush_stock.quantity < brush_received):
            return jsonify({"error": "Insufficient BRUSH stock"}), 400

        if paste_received > 0 and (not paste_stock or paste_stock.quantity < paste_received):
            return jsonify({"error": "Insufficient TOOTHPASTE stock"}), 400

        if iec_received > 0 and (not iec_stock or iec_stock.quantity < iec_received):
            return jsonify({"error": "Insufficient IEC/FLYER stock"}), 400

        if brush_received > 0:
            brush_stock.quantity -= brush_received
        if paste_received > 0:
            paste_stock.quantity -= paste_received
        if iec_received > 0:
            iec_stock.quantity -= iec_received

        new_distribution = KitDistribution(
            beneficiary_id=beneficiary_id,
            dealer_id=dealer_id,
            kit_unique_id=str(uuid.uuid4()),
            status="CONFIRMED",
            expiry=datetime.utcnow() + timedelta(hours=24),
            confirmed_at=datetime.utcnow(),
            confirmation_mode="DEALER_MANUAL",
            old_kit_returned=old_kit_returned,
            brush_received=brush_received,
            paste_received=paste_received,
            iec_received=iec_received
        )

        db.session.add(new_distribution)
        db.session.commit()

        return jsonify({
            "message": "Distribution completed successfully",
            "distribution_id": new_distribution.id,
            "kit_unique_id": new_distribution.kit_unique_id,
            "status": new_distribution.status,
            "old_kit_returned": bool(new_distribution.old_kit_returned),
            "brush_received": new_distribution.brush_received,
            "paste_received": new_distribution.paste_received,
            "iec_received": new_distribution.iec_received,
            "confirmed_at": str(new_distribution.confirmed_at)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= DEALER VERIFY BENEFICIARY ROUTE =================
@app.route("/dealer/verify-beneficiary", methods=["POST"])
def verify_beneficiary():
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received"}), 400

        dealer_id = data.get("dealer_id")
        pds_card_no = data.get("pds_card_no")

        if not dealer_id or not pds_card_no:
            return jsonify({"error": "dealer_id and pds_card_no are required"}), 400

        dealer = Dealer.query.get(int(dealer_id))
        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404

        user = User.query.filter_by(pds_card_no=pds_card_no.strip()).first()
        if not user:
            return jsonify({
                "valid": False,
                "linked": False,
                "message": "Invalid PDS card number"
            }), 404

        if not user.pds_verified:
            return jsonify({
                "valid": False,
                "linked": False,
                "message": "PDS card not linked"
            }), 400

        if user.dealer_id is not None and user.dealer_id != int(dealer_id):
            return jsonify({
                "valid": False,
                "linked": True,
                "message": "Beneficiary belongs to another dealer"
            }), 403

        return jsonify({
            "valid": True,
            "linked": True,
            "message": "Beneficiary verified successfully",
            "user_id": user.id,
            "beneficiary_id": user.id,
            "household_id": f"HH-{user.id}",
            "name": user.name,
            "pds_card_no": user.pds_card_no
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= DEALER HOUSEHOLD DETAILS ROUTE =================
@app.route("/dealer/household/<int:user_id>", methods=["GET"])
def get_dealer_household(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        members = FamilyMember.query.filter_by(user_id=user_id).all()

        return jsonify({
            "user_id": user.id,
            "household_id": f"HH-{user.id}",
            "head_name": user.name,
            "pds_card_no": user.pds_card_no,
            "category": "PHH",
            "members": [
                {
                    "id": m.id,
                    "member_name": m.member_name,
                    "age": m.age,
                    "relation": m.relation
                } for m in members
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= DEALER DISTRIBUTION HISTORY ROUTE =================
@app.route("/dealer/distribution-history/<int:dealer_id>", methods=["GET"])
def dealer_distribution_history(dealer_id):
    try:
        kits = KitDistribution.query.filter_by(
            dealer_id=dealer_id,
            status="CONFIRMED"
        ).order_by(KitDistribution.confirmed_at.desc()).all()

        result = []
        for kit in kits:
            user = User.query.get(kit.beneficiary_id)
            items_summary = []

            if kit.brush_received and kit.brush_received > 0:
                items_summary.append(f"{kit.brush_received}x Brush")
            if kit.paste_received and kit.paste_received > 0:
                items_summary.append(f"{kit.paste_received}x Paste")
            if kit.iec_received and kit.iec_received > 0:
                items_summary.append(f"{kit.iec_received}x IEC")

            result.append({
                "id": kit.id,
                "kit_unique_id": kit.kit_unique_id,
                "beneficiary_name": user.name if user else f"User #{kit.beneficiary_id}",
                "beneficiary_phone": user.phone if user else None,
                "beneficiary_email": user.email if user else None,
                "pds_card_no": user.pds_card_no if user else None,
                "status": kit.status,
                "time": kit.confirmed_at.strftime("%I:%M %p") if kit.confirmed_at else "",
                "date": kit.confirmed_at.strftime("%Y-%m-%d") if kit.confirmed_at else "",
                "confirmed_at": str(kit.confirmed_at) if kit.confirmed_at else None,
                "category": "PHH",
                "items_summary": ", ".join(items_summary),
                "old_kit_returned": bool(kit.old_kit_returned)
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= DEALER QR DATA ROUTE =================
@app.route("/dealer/qr/<int:dealer_id>", methods=["GET"])
def get_dealer_qr_data(dealer_id):
    dealer = Dealer.query.get(dealer_id)
    if not dealer:
        return jsonify({"error": "Dealer not found"}), 404

    if not dealer.dealer_qr_value:
        qr_value = generate_dealer_qr_value(dealer.id)
        qr_image = generate_dealer_qr_image(qr_value)
        dealer.dealer_qr_value = qr_value
        dealer.dealer_qr_image = qr_image
        db.session.commit()

    return jsonify({
        "type": "DEALER",
        "dealer_id": dealer.id,
        "dealer_name": dealer.name,
        "dealer_qr_value": dealer.dealer_qr_value,
        "dealer_qr_image": dealer.dealer_qr_image
    }), 200


# ================= DEALER KIT RECEIVED DATA ROUTE =================
@app.route("/dealer/kit-received/<string:kit_unique_id>", methods=["GET"])
def get_kit_received(kit_unique_id):
    try:
        kit = KitDistribution.query.filter_by(
            kit_unique_id=kit_unique_id
        ).first()

        if not kit:
            return jsonify({"error": "Kit distribution not found"}), 404

        if kit.status != "CONFIRMED":
            return jsonify({"error": "Kit has not been confirmed yet"}), 400

        beneficiary = User.query.get(kit.beneficiary_id)
        dealer = Dealer.query.get(kit.dealer_id)

        return jsonify({
            "kit_unique_id": kit.kit_unique_id,
            "beneficiary": {
                "id": beneficiary.id if beneficiary else None,
                "name": beneficiary.name if beneficiary else None,
                "phone": beneficiary.phone if beneficiary else None,
                "email": beneficiary.email if beneficiary else None,
            },
            "dealer": {
                "id": dealer.id if dealer else None,
                "name": dealer.name if dealer else None,
                "phone": dealer.phone if dealer else None,
                "company_name": dealer.company_name if dealer else None,
            },
            "status": kit.status,
            "confirmation_mode": kit.confirmation_mode,
            "brush_received": int(kit.brush_received or 0),
            "paste_received": int(kit.paste_received or 0),
            "iec_received": int(kit.iec_received or 0),
            "old_kit_returned": bool(kit.old_kit_returned),
            "old_kit_return_status": "RETURNED" if kit.old_kit_returned else "NOT_RETURNED",
            "show_red_alert": not bool(kit.old_kit_returned),
            "red_alert_message": "Old kit not returned" if not kit.old_kit_returned else "",
            "confirmed_at": str(kit.confirmed_at) if kit.confirmed_at else None,
            "created_at": str(kit.created_at) if kit.created_at else None
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= DEALER KIT RECEIVED LIST ROUTE =================
@app.route("/dealer/kit-received-list/<int:dealer_id>", methods=["GET"])
def get_kit_received_list(dealer_id):
    try:
        kits = KitDistribution.query.filter_by(
            dealer_id=dealer_id,
            status="CONFIRMED"
        ).order_by(KitDistribution.confirmed_at.desc()).all()

        result = []
        for kit in kits:
            user = User.query.get(kit.beneficiary_id)
            result.append({
                "kit_unique_id": kit.kit_unique_id,
                "beneficiary_id": kit.beneficiary_id,
                "beneficiary_name": user.name if user else None,
                "brush_received": int(kit.brush_received or 0),
                "paste_received": int(kit.paste_received or 0),
                "iec_received": int(kit.iec_received or 0),
                "old_kit_returned": bool(kit.old_kit_returned),
                "old_kit_return_status": "RETURNED" if kit.old_kit_returned else "NOT_RETURNED",
                "show_red_alert": not bool(kit.old_kit_returned),
                "status": kit.status,
                "confirmed_at": str(kit.confirmed_at) if kit.confirmed_at else None
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= DEALER QR VERIFY ROUTE =================
@app.route("/dealer/verify-qr", methods=["POST"])
def verify_dealer_qr():
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received. Send JSON or form-data."}), 400

        dealer_qr_value = data.get("dealer_qr_value")
        if not dealer_qr_value:
            return jsonify({"error": "dealer_qr_value is required"}), 400

        if dealer_qr_value.startswith("digitalpds://dealer/"):
            dealer_qr_value = dealer_qr_value.replace("digitalpds://dealer/", "", 1)

        dealer = Dealer.query.filter_by(dealer_qr_value=dealer_qr_value).first()
        if not dealer:
            return jsonify({
                "valid": False,
                "message": "Invalid dealer QR"
            }), 404

        return jsonify({
            "valid": True,
            "message": "Dealer QR verified successfully",
            "dealer": {
                "id": dealer.id,
                "name": dealer.name,
                "email": dealer.email,
                "phone": dealer.phone,
                "company_name": dealer.company_name,
                "dealer_qr_value": dealer.dealer_qr_value,
                "dealer_qr_image": dealer.dealer_qr_image
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GENERATE MISSING DEALER QRS ROUTE =================
@app.route("/admin/generate-missing-dealer-qrs", methods=["POST"])
def generate_missing_dealer_qrs():
    try:
        dealers = Dealer.query.all()
        updated = 0

        for dealer in dealers:
            if not dealer.dealer_qr_value:
                qr_value = generate_dealer_qr_value(dealer.id)
                qr_image = generate_dealer_qr_image(qr_value)
                dealer.dealer_qr_value = qr_value
                dealer.dealer_qr_image = qr_image
                updated += 1

        db.session.commit()

        return jsonify({
            "message": "Missing dealer QR values generated successfully",
            "updated_count": updated
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= SYNC EXISTING DEALER LOCATIONS ROUTE =================
@app.route("/admin/sync-existing-dealer-locations", methods=["POST"])
def sync_existing_dealer_locations():
    try:
        dealers = Dealer.query.all()
        updated = 0
        created = 0
        
        for dealer in dealers:
            if dealer.address:
                # Sync to dealer_locations table
                loc = DealerLocation.query.filter_by(dealer_id=dealer.id).first()
                if loc:
                    if loc.location_name != dealer.address:
                        loc.location_name = dealer.address
                        updated += 1
                else:
                    new_loc = DealerLocation(dealer_id=dealer.id, location_name=dealer.address)
                    db.session.add(new_loc)
                    created += 1
                
                # Also sync the dealer.location field itself
                dealer.location = dealer.address
                
        db.session.commit()
        
        return jsonify({
            "message": "Existing dealer locations synchronized successfully",
            "updated_count": updated,
            "created_count": created
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500




@app.route('/api/user/link-pds', methods=['POST'])
def link_pds():
    try:
        data = get_request_data()
        user_id = data.get("user_id")
        pds_card_no = data.get("pds_card_no")

        if not user_id or not pds_card_no:
            return jsonify({"error": "user_id and pds_card_no required"}), 400

        user = User.query.get(int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Lock PDS card linking if already verified
        if user.pds_card_no and user.pds_verified:
            return jsonify({
                "error": "This account is already linked to a PDS card and is locked.",
                "pds_card_no": user.pds_card_no
            }), 400

        # Format Validation: PDS-XXXXXX (e.g. PDS-584927)
        if not re.match(r"^PDS-\d+$", pds_card_no, re.IGNORECASE):
            return jsonify({"error": "Invalid PDS card format. Must be PDS-123456"}), 400

        existing = User.query.filter_by(pds_card_no=pds_card_no).first()

        if existing:
            return jsonify({"error": "This PDS card is already linked to another account"}), 400

        db.session.execute(text("""
            UPDATE users
            SET pds_card_no = :card,
                pds_linked_at = NOW(),
                pds_verified = 1
            WHERE id = :uid
        """), {"card": pds_card_no, "uid": int(user_id)})

        db.session.commit()

        user = User.query.get(int(user_id))
        if user.created_by_type in ["SELF", "ADMIN"]:
            return jsonify({
                "message": "PDS linked successfully",
                "user_id": int(user_id),
                "pds_card_no": pds_card_no,
                "next_step": "SELECT_DEALER"
            }), 200

        return jsonify({
            "message": "PDS linked successfully",
            "user_id": int(user_id),
            "pds_card_no": pds_card_no,
            "next_step": "NONE"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= FAMILY ROUTES =================
@app.route('/api/family-members', methods=['POST'])
def add_family_member():
    data = request.get_json()

    user_id = data.get("user_id")
    member_name = data.get("member_name")
    age = data.get("age")
    relation = data.get("relation")

    if not user_id or not member_name or not age or not relation:
        return jsonify({"error": "user_id, member_name, age, relation required"}), 400

    db.session.execute(text("""
        INSERT INTO family_members (user_id, member_name, age, relation, brushing_target, weekly_brush_count)
        VALUES (:uid, :name, :age, :relation, 14, 0)
    """), {
        "uid": user_id,
        "name": member_name,
        "age": age,
        "relation": relation
    })

    db.session.commit()

    return jsonify({"message": "Family member added successfully"}), 201


@app.route('/api/family-members/<int:user_id>', methods=['GET'])
@app.route('/api/user/family-members', methods=['GET'])
def get_family_members(user_id=None):
    if user_id is None:
        user_id = request.args.get("userId") or request.args.get("user_id")
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    rows = db.session.execute(text("""
        SELECT id, user_id, member_name, age, relation, brushing_target, weekly_brush_count
        FROM family_members
        WHERE user_id = :uid
    """), {"uid": int(user_id)}).mappings().all()

    return jsonify([dict(r) for r in rows]), 200


@app.route('/api/family-members/<int:member_id>', methods=['PUT'])
def update_family_member(member_id):
    try:
        data = request.get_json()

        member_name = data.get("member_name")
        age = data.get("age")
        relation = data.get("relation")

        if not member_name or not age or not relation:
            return jsonify({"error": "member_name, age, and relation are required"}), 400

        db.session.execute(
            text("""
                UPDATE family_members
                SET member_name = :name,
                    age = :age,
                    relation = :relation
                WHERE id = :member_id
            """),
            {
                "name": member_name,
                "age": age,
                "relation": relation,
                "member_id": member_id
            }
        )

        db.session.commit()

        return jsonify({
            "message": "Family member updated successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/family-members/<int:member_id>', methods=['DELETE'])
def delete_family_member(member_id):
    try:
        user_id = request.args.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id is required in query params"}), 400

        member = db.session.execute(text("""
            SELECT id, user_id FROM family_members
            WHERE id = :mid AND user_id = :uid
        """), {"mid": member_id, "uid": int(user_id)}).fetchone()

        if not member:
            return jsonify({"error": "Family member not found for this user"}), 404

        db.session.execute(text("""
            DELETE FROM family_members
            WHERE id = :mid AND user_id = :uid
        """), {"mid": member_id, "uid": int(user_id)})

        db.session.commit()

        return jsonify({
            "message": "Family member deleted successfully",
            "member_id": member_id,
            "user_id": int(user_id)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= ADMIN ADD CLINIC ROUTE =================
@app.route("/admin/add-clinic", methods=["POST"])
def add_clinic():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    required_fields = ["clinic_name"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    new_clinic = Clinic(
        clinic_name=data["clinic_name"],
        website=data.get("website")
    )

    db.session.add(new_clinic)
    db.session.commit()

    return jsonify({"message": "Clinic added successfully"}), 201






# ================= VIEW CLINICS ROUTE =================
@app.route("/user/view-clinics", methods=["GET"])
def view_clinics():
    clinics = Clinic.query.all()

    result = []
    for clinic in clinics:
        result.append({
            "id": clinic.id,
            "clinic_name": clinic.clinic_name,
            "address": clinic.address,
            "district": clinic.district,
            "contact_number": clinic.contact_number,
            "latitude": clinic.latitude,
            "longitude": clinic.longitude,
            "website": clinic.website,
            "booking_available": clinic.booking_available
        })

    return jsonify(result), 200


@app.route("/admin/delete-clinic/<int:clinic_id>", methods=["DELETE"])
def delete_clinic(clinic_id):
    try:
        clinic = Clinic.query.get(clinic_id)
        if not clinic:
            return jsonify({"error": "Clinic not found"}), 404

        db.session.delete(clinic)
        db.session.commit()
        return jsonify({"message": "Clinic deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= VIEW USER APPOINTMENTS ROUTE REMOVED =================


# ================= USER ADD TEETH REPORT ROUTE =================
@app.route("/user/add-teeth-report", methods=["POST"])
def add_teeth_report():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    required_fields = ["user_id", "image_path", "ai_result", "risk_level"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    new_report = TeethReport(
        user_id=data["user_id"],
        member_id=data.get("member_id"),
        image_path=data["image_path"],
        ai_result=data["ai_result"],
        risk_level=data["risk_level"],
        created_at=datetime.utcnow()
    )

    db.session.add(new_report)
    db.session.commit()

    return jsonify({"message": "Teeth report saved successfully"}), 201


# ================= VIEW TEETH REPORTS ROUTE =================
@app.route("/user/view-teeth-reports/<int:user_id>", methods=["GET"])
def view_teeth_reports(user_id):
    reports = TeethReport.query.filter_by(user_id=user_id).all()

    result = []
    for report in reports:
        image_path = report.image_path
        if image_path and ("uploads" in image_path):
            image_path = image_path[image_path.find("uploads"):]
        elif image_path and os.path.isabs(image_path):
            image_path = f"uploads/{os.path.basename(image_path)}"
            
        ai_result_json = None
        try:
            ai_result_json = json.loads(report.ai_result)
        except:
            # Fallback for old records: "Disease: {predicted_class}, Confidence: {confidence:.2f}"
            match = re.search(r"Disease: (.*), Confidence: (.*)", report.ai_result)
            detections = []
            if match:
                disease = match.group(1)
                conf = float(match.group(2))
                detections.append({
                    "class": disease.replace(" ", ""),
                    "confidence": conf,
                    "bbox": [0, 0, 0, 0]
                })
            
            ai_result_json = {
                "message": "Analysis successful (Legacy)",
                "reportId": report.id,
                "riskLevel": report.risk_level,
                "detections": detections
            }

        result.append({
            "id": report.id,
            "image_path": image_path,
            "ai_result": json.dumps(ai_result_json) if isinstance(ai_result_json, dict) else report.ai_result,
            "risk_level": report.risk_level,
            "created_at": str(report.created_at)
        })

    return jsonify(result), 200


# ================= GET LATEST MEMBER REPORT ROUTE =================
@app.route("/api/member/<int:member_id>/latest-report", methods=["GET"])
def get_latest_member_report(member_id):
    user_id = request.args.get("user_id", type=int)
    
    query = TeethReport.query.filter_by(member_id=member_id)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
        
    report = query.order_by(TeethReport.created_at.desc()).first()

    if not report:
        return jsonify({"message": "No report found"}), 404

    image_path = report.image_path
    if image_path and ("uploads" in image_path):
        image_path = image_path[image_path.find("uploads"):]
    elif image_path and os.path.isabs(image_path):
        image_path = f"uploads/{os.path.basename(image_path)}"

    ai_result_json = None
    try:
        import json
        ai_result_json = json.loads(report.ai_result)
    except:
        # Fallback for old records: "Disease: {predicted_class}, Confidence: {confidence:.2f}"
        import re
        match = re.search(r"Disease: (.*), Confidence: (.*)", report.ai_result)
        detections = []
        if match:
            disease = match.group(1)
            conf = float(match.group(2))
            detections.append({
                "class": disease.replace(" ", ""), # Remove spaces to match enum
                "confidence": conf,
                "bbox": [0, 0, 0, 0]
            })
        
        ai_result_json = {
            "message": "Analysis successful (Legacy)",
            "reportId": report.id,
            "riskLevel": report.risk_level,
            "detections": detections
        }

    return jsonify({
        "member_id": report.member_id,
        "ai_result": json.dumps(ai_result_json) if isinstance(ai_result_json, dict) else report.ai_result,
        "risk_level": report.risk_level,
        "image_path": image_path,
        "created_at": str(report.created_at)
    }), 200


# ================= AI PREDICTION ROUTE =================
@app.route('/user/teeth-ai', methods=['POST'])
def teeth_ai():
    try:
        if 'image' not in request.files:
            return jsonify({"message": "Image is required"}), 400

        image = request.files['image']
        user_id = request.form.get('user_id')
        member_id = request.form.get("member_id")

        if not user_id:
            return jsonify({"message": "user_id is required"}), 400

        if member_id is None:
            return jsonify({"error": "member_id is required"}), 400

        user_id = int(user_id)
        member_id = int(member_id)

        if member_id != 0:
            family_member = FamilyMember.query.filter_by(id=member_id, user_id=user_id).first()
            if not family_member:
                return jsonify({"message": "Invalid member_id for this user"}), 404

        filename = secure_filename(image.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        upload_folder = os.path.join(app.root_path, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        full_path = os.path.join(upload_folder, unique_filename)
        relative_path = f"uploads/{unique_filename}"
        
        image.save(full_path)
        
        result = model.predict(source=full_path, imgsz=640, conf=0.25, verbose=False)[0]

        detections = []
        for b in result.boxes:
            cls_id = int(b.cls[0])
            conf = float(b.conf[0])
            x1, y1, x2, y2 = [float(x) for x in b.xyxy[0]]
            detections.append({
                "class": model.names[cls_id],
                "confidence": conf,
                "bbox": [x1, y1, x2, y2]
            })

        predicted_class = "No Disease Detected"
        confidence = 0.0

        if detections:
            top_detection = detections[0]
            predicted_class = top_detection["class"]
            confidence = top_detection["confidence"]

        risk_level = "LOW"
        if confidence > 0.5:
            risk_level = "MEDIUM"
        if confidence > 0.7:
            risk_level = "HIGH"

        import json
        ai_response_json = json.dumps({
            "message": "Analysis successful",
            "reportId": 0,  # Placeholder, updated below
            "riskLevel": risk_level,
            "detections": detections
        })

        new_report = TeethReport(
            user_id=user_id,
            member_id=member_id,
            image_path=relative_path,
            ai_result=ai_response_json,
            risk_level=risk_level,
            created_at=datetime.utcnow()
        )
        db.session.add(new_report)
        db.session.commit()
        
        # Update reportId in the stored JSON
        updated_json = json.dumps({
            "message": "Analysis successful",
            "reportId": new_report.id,
            "riskLevel": risk_level,
            "detections": detections
        })
        new_report.ai_result = updated_json
        db.session.commit()

        return jsonify({
            "message": "Analysis successful",
            "reportId": new_report.id,
            "riskLevel": risk_level,
            "detections": detections
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500


# ================= ADMIN GET DEALERS ROUTE =================
@app.route("/admin/get-dealers", methods=["GET"])
@jwt_required()
def get_dealers():
    # Fetch dealers with their primary location if available
    dealers = Dealer.query.all()

    result = []
    for d in dealers:
        # Use the dealer's location field directly
        location_name = d.location or d.company_name or "Not Specified"

        result.append({
            "id": d.id,
            "name": d.name,
            "email": d.email,
            "phone": d.phone,
            "company_name": d.company_name,
            "address": d.address,
            "city": d.city,
            "state": d.state,
            "username": d.username,
            "location": location_name,
            "dealer_qr_value": d.dealer_qr_value,
            "dealer_qr_image": d.dealer_qr_image
        })

    return jsonify(result), 200


# ================= ADMIN DASHBOARD STATS ROUTE =================
@app.route("/admin/dashboard-stats", methods=["GET"])
def admin_dashboard_stats():
    try:
        total_dealers = Dealer.query.count()
        active_beneficiaries = User.query.count()
        total_distributions = KitDistribution.query.count()

        confirmed_count = KitDistribution.query.filter_by(status="CONFIRMED").count()
        pending_count = KitDistribution.query.filter_by(status="PENDING").count()
        # Align with dealer dashboard: only count confirmed kit returns
        returned_count = KitDistribution.query.filter_by(status="CONFIRMED", old_kit_returned=True).count()

        if total_distributions > 0:
            kit_given_percentage = int((confirmed_count / total_distributions) * 100)
            kit_pending_percentage = int((pending_count / total_distributions) * 100)
            kit_returned_percentage = int((returned_count / total_distributions) * 100)
        else:
            kit_given_percentage = 0
            kit_pending_percentage = 0
            kit_returned_percentage = 0

        return jsonify({
            "totalDealers": str(total_dealers),
            "totalDealersChange": "12%",
            "isDealersPositive": True,
            "activeBeneficiaries": str(active_beneficiaries),
            "activeBeneficiariesChange": "5%",
            "isBeneficiariesPositive": True,
            "totalDistributions": str(total_distributions),
            "totalDistributionsChange": "2%",
            "isDistributionsPositive": True,
            "returnRate": str(returned_count),
            "returnRateChange": "0%",
            "isReturnRatePositive": True if kit_returned_percentage > 0 else False,
            "kitGivenPercentage": kit_given_percentage,
            "kitReturnedPercentage": kit_returned_percentage,
            "kitPendingPercentage": kit_pending_percentage
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= DEALER DASHBOARD STATS ROUTE =================
@app.route("/dealer/dashboard-stats/<int:dealer_id>", methods=["GET"])
def dealer_dashboard_stats(dealer_id):
    try:
        print("Dealer dashboard called with dealer_id =", dealer_id)

        dealer = Dealer.query.get(dealer_id)
        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404

        stock_items = DealerStock.query.filter_by(dealer_id=dealer_id).all()
        kit_rows = KitDistribution.query.filter_by(dealer_id=dealer_id).all()

        # Calculate complete kits based on the minimum available of each item
        brushes = sum(int(item.quantity or 0) for item in stock_items if str(item.item_name).upper() == "BRUSH")
        pastes = sum(int(item.quantity or 0) for item in stock_items if str(item.item_name).upper() == "TOOTHPASTE")
        flyers = sum(int(item.quantity or 0) for item in stock_items if str(item.item_name).upper() == "FLYER")
        
        remaining_kits = min(brushes, pastes, flyers)
        distributed_kits = sum(1 for k in kit_rows if k.status == "CONFIRMED")
        returned_kits = sum(1 for k in kit_rows if k.status == "CONFIRMED" and k.old_kit_returned)
        
        # total_kits is the total of available kits plus distributed ones
        total_kits = remaining_kits + distributed_kits

        today = datetime.utcnow().date()
        today_distributions = sum(
            1 for k in kit_rows if k.created_at and k.created_at.date() == today
        )

        daily_target = 10
        performance_percentage = int((today_distributions / daily_target) * 100) if daily_target > 0 else 0

        grouped_counts = {
            "BRUSH": 0,
            "TOOTHPASTE": 0,
            "FLYER": 0
        }

        for item in stock_items:
            item_name = str(item.item_name) if item.item_name else ""
            if item_name in grouped_counts:
                grouped_counts[item_name] += int(item.quantity or 0)

        item_counts = [
            {"name": "BRUSH", "count": str(grouped_counts["BRUSH"])},
            {"name": "TOOTHPASTE", "count": str(grouped_counts["TOOTHPASTE"])},
            {"name": "FLYER", "count": str(grouped_counts["FLYER"])}
        ]

        sorted_kits = sorted(
            kit_rows,
            key=lambda x: x.created_at if x.created_at else datetime.min,
            reverse=True
        )

        recent_transactions = []
        confirmed_kits = [k for k in sorted_kits if k.status == "CONFIRMED"]

        for k in confirmed_kits[:5]:
            recent_transactions.append({
                "id": k.id,
                "name": f"Kit #{k.id}",
                "details": f"Beneficiary ID: {k.beneficiary_id} | Status: {k.status}",
                "quantity": "1",
                "timestamp": k.created_at.strftime("%d-%m-%Y %I:%M %p") if k.created_at else ""
            })

        return jsonify({
            "todayDistributions": str(today_distributions),
            "performancePercentage": performance_percentage,
            "totalKits": str(total_kits),
            "distributedKits": str(distributed_kits),
            "remainingKits": str(remaining_kits),
            "returnedKits": str(returned_kits),
            "itemCounts": item_counts,
            "recentTransactions": recent_transactions
        }), 200

    except Exception as e:
        print("DEALER DASHBOARD ERROR:", str(e))
        traceback.print_exc()
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500


@app.route("/admin/beneficiaries/<int:user_id>", methods=["GET"])
@app.route("/admin/beneficiary/<int:user_id>", methods=["GET"])
def get_admin_beneficiary_details(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Beneficiary not found"}), 404

        dealer = None
        if user.dealer_id:
            dealer = Dealer.query.get(user.dealer_id)

        distributions = KitDistribution.query.filter_by(beneficiary_id=user_id).order_by(KitDistribution.id.desc()).all()
        
        history = []
        for dist in distributions:
            dist_dealer = Dealer.query.get(dist.dealer_id)
            history.append({
                "id": dist.kit_unique_id or f"K-{dist.id}",
                "beneficiaryId": dist.beneficiary_id,
                "kitName": "Standard Dental Kit",
                "kitType": "Monthly Issue",
                "quantity": f"Brush: {dist.brush_received}, Paste: {dist.paste_received}",
                "status": "GIVEN" if dist.status == "CONFIRMED" else "PENDING",
                "date": str(dist.confirmed_at.date() if dist.confirmed_at else dist.created_at.date()),
                "givenBy": dist_dealer.name if dist_dealer else "Unknown",
                "notes": f"Confirmation Mode: {dist.confirmation_mode}"
            })

        family_members = FamilyMember.query.filter_by(user_id=user_id).all()
        family_list = []
        for member in family_members:
            family_list.append({
                "id": member.id,
                "user_id": member.user_id,
                "member_name": member.member_name,
                "age": member.age,
                "relation": member.relation,
                "brushing_target": member.brushing_target,
                "weekly_brush_count": member.weekly_brush_count
            })

        # Enrich location info
        location_display_name = "Not Assigned"
        if user.location_id:
            loc = DealerLocation.query.get(user.location_id)
            if loc:
                location_display_name = loc.location_name
        elif dealer:
            location_display_name = dealer.location or dealer.company_name or "Not Assigned"

        response = {
            "id": user.id,
            "name": user.name,
            "phone": user.phone or "N/A",
            "email": user.email,
            "age": user.age,
            "gender": user.gender,
            "education": user.education,
            "employment": user.employment,
            "location": location_display_name, # Real location name
            "pds_card_no": user.pds_card_no or "Not Linked",
            "household_id": f"HH-{user.id}",
            "category": "PHH", # Default for now
            "address": user.address or "N/A",
            "status": "GIVEN" if user.pds_verified else "PENDING",
            "createdAt": str(user.pds_linked_at.date() if user.pds_linked_at else "N/A"),
            "createdByRole": user.created_by_type,
            "createdById": str(dealer.id) if dealer else "ADMIN",
            "createdByName": dealer.name if dealer else "Admin",
            "history": history,
            "familyMembers": family_list,
            "pds_card_front": user.pds_card_front,
            "pds_card_back": user.pds_card_back,
            "profile_image": user.profile_image
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= ADMIN EDIT/DELETE BENEFICIARY =================
@app.route("/admin/update-beneficiary/<int:user_id>", methods=["PUT"])
def admin_update_beneficiary(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Beneficiary not found"}), 404

        data = get_request_data()
        
        if "name" in data and data["name"]:
            user.name = data["name"]
        if "phone" in data and data["phone"]:
            user.phone = data["phone"]
        if "pds_card_no" in data and data["pds_card_no"]:
            # Check for PDS overlap if changed
            if user.pds_card_no != data["pds_card_no"]:
                existing_pds = User.query.filter(User.pds_card_no == data["pds_card_no"], User.id != user_id).first()
                if existing_pds:
                    return jsonify({"error": "PDS card number already exists for another user"}), 400
                user.pds_card_no = data["pds_card_no"]
                
        if "status" in data and data["status"]:
            user.pds_verified = (data["status"].upper() == "GIVEN")

        if "email" in data:
            user.email = data["email"] if data["email"] else None
        if "age" in data:
            user.age = int(data["age"]) if data["age"] else None
        if "gender" in data:
            user.gender = data["gender"] if data["gender"] else None
        if "education" in data:
            user.education = data["education"] if data["education"] else None
        if "employment" in data:
            user.employment = data["employment"] if data["employment"] else None
        if "address" in data:
            user.address = data["address"] if data["address"] else None
                
        db.session.commit()
        return jsonify({"message": "Beneficiary updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/admin/delete-beneficiary/<int:user_id>", methods=["DELETE"])
def admin_delete_beneficiary(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Beneficiary not found"}), 404

        # Cascade clean up manually to prevent orphaned rows
        KitDistribution.query.filter_by(beneficiary_id=user_id).delete()
        BrushingCheckin.query.filter_by(user_id=user_id).delete()
        FamilyMember.query.filter_by(user_id=user_id).delete()
        TeethReport.query.filter_by(user_id=user_id).delete()

        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "Beneficiary and all associated records deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/user/delete-account/<int:user_id>", methods=["DELETE"])
@jwt_required()
def user_delete_account(user_id):
    try:
        from flask_jwt_extended import get_jwt_identity
        current_user_id = get_jwt_identity()

        # Security: only allow users to delete their own account
        if str(current_user_id) != str(user_id):
            return jsonify({"error": "Unauthorized to delete this account"}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Cascade clean up manually to prevent orphaned rows
        KitDistribution.query.filter_by(beneficiary_id=user_id).delete()
        BrushingCheckin.query.filter_by(user_id=user_id).delete()
        FamilyMember.query.filter_by(user_id=user_id).delete()
        TeethReport.query.filter_by(user_id=user_id).delete()

        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "Your account and all associated records have been deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= DEALER BENEFICIARIES ROUTE =================
@app.route("/dealer/<int:dealer_id>/beneficiaries", methods=["GET"])
def get_dealer_beneficiaries(dealer_id):
    try:
        dealer = Dealer.query.get(dealer_id)

        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404

        users = User.query.filter_by(dealer_id=dealer_id).order_by(User.id.desc()).all()

        result = []

        for user in users:
            result.append({
                "id": user.id,
                "name": user.name,
                "dealer_id": user.dealer_id,
                "ration_id": user.pds_card_no if user.pds_card_no else "Not Linked",
                "household_id": f"HH-{user.id}",
                "is_active": bool(user.pds_verified)
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/dealer/beneficiary/<int:id>", methods=["GET"])
def get_dealer_beneficiary_details(id):
    # Use the same rich logic as the admin details for the dealer panel
    return get_admin_beneficiary_details(id)


# ================= FORGOT PASSWORD ROUTE =================
# ================= OLD LINK-BASED FORGOT PASSWORD ROUTE =================
# @app.route('/api/forgot-password', methods=['POST'])
# def forgot_password():
#     data = request.get_json()
#     email = data.get('email')
#
#     if not email:
#         return jsonify({"error": "Email is required"}), 400
#
#     user = User.query.filter_by(email=email).first()
#
#     if not user:
#         return jsonify({"error": "User not found"}), 404
#
#     code = secrets.token_urlsafe(32)
#     user.reset_code = code
#     user.reset_expiry = datetime.utcnow() + timedelta(minutes=15)
#     db.session.commit()
#
#     reset_link = f"http://127.0.0.1:5000/api/reset-password/{code}"
#
#     msg = Message(
#         subject="Reset Your Password",
#         recipients=[email]
#     )
#     msg.body = f"""
# Hello,
#
# Click the link below to reset your password:
#
# {reset_link}
#
# This link is valid for 15 minutes.
# """
#     mail.send(msg)
#
#     return jsonify({"message": "Reset link sent to email"}), 200


# ================= OLD LINK-BASED RESET PASSWORD ROUTE =================
# @app.route('/api/reset-password/<code>', methods=['POST'])
# def reset_password(code):
#     user = User.query.filter_by(reset_code=code).first()
#
#     if not user:
#         return jsonify({"error": "Invalid reset link"}), 400
#
#     if not user.reset_expiry or user.reset_expiry < datetime.utcnow():
#         return jsonify({"error": "Reset link expired"}), 400
#
#     data = request.get_json()
#     new_password = data.get("password")
#     confirm_password = data.get("confirm_password")
#
#     if not new_password or not confirm_password:
#         return jsonify({"error": "Password and confirm password are required"}), 400
#
#     if new_password != confirm_password:
#         return jsonify({"error": "Passwords do not match"}), 400
#
#     user.password_hash = new_password
#     user.reset_code = None
#     user.reset_expiry = None
#     db.session.commit()
#
#     return jsonify({"message": "Password updated successfully"}), 200


# ================= REGENERATE DEALER QRS (TEMP) =================
@app.route("/admin/regenerate-all-dealer-qrs", methods=["POST"])
def regenerate_all_dealer_qrs():
    try:
        dealers = Dealer.query.all()
        updated = 0

        for dealer in dealers:
            if dealer.dealer_qr_value:
                dealer.dealer_qr_image = generate_dealer_qr_image(dealer.dealer_qr_value)
                updated += 1

        db.session.commit()

        return jsonify({
            "message": "All dealer QR images regenerated successfully",
            "updated_count": updated
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= DELETE DEALER ROUTE =================
@app.route("/admin/delete-dealer/<int:dealer_id>", methods=["DELETE"])
def admin_delete_dealer(dealer_id):
    try:
        dealer = Dealer.query.get(dealer_id)
        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404


        DealerStock.query.filter_by(dealer_id=dealer_id).delete()
        StockRequest.query.filter_by(dealer_id=dealer_id).delete()
        KitDistribution.query.filter_by(dealer_id=dealer_id).delete()

        User.query.filter_by(dealer_id=dealer_id).update({"dealer_id": None})

        db.session.delete(dealer)
        db.session.commit()

        return jsonify({"message": "Dealer deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= MAIN =================
@app.route('/debug-routes')
def debug_routes():
    return str([r.rule for r in app.url_map.iter_rules()])

# ================= HELPERS FOR PASSWORD RECOVERY =================
def process_forgot_password(email, allowed_role=None):
    try:
        if not email:
            return jsonify({"error": "Email is required"}), 400

        target = None
        if allowed_role == "user" or allowed_role is None:
            target = User.query.filter_by(email=email).first()
        
        if not target and (allowed_role == "dealer" or allowed_role is None):
            target = Dealer.query.filter_by(email=email).first()

        if not target:
            return jsonify({"error": "Account not found with this email"}), 404

        # Generate 6-digit numeric code
        import secrets
        code = str(secrets.randbelow(900000) + 100000)
        
        target.reset_code = code
        target.reset_expiry = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()

        # Try to send email
        mail_sent = False
        error_detail = ""
        try:
            msg = Message(
                subject="Your Password Reset Code",
                recipients=[email]
            )
            msg.body = f"""
Hello,

Your password reset code is: {code}

This code is valid for 15 minutes. Use it in the app to reset your password.

If you did not request this, please ignore this email.
"""
            mail.send(msg)
            mail_sent = True
        except Exception as e:
            print(f"MAIL ERROR: {str(e)}")
            error_detail = str(e)

        if mail_sent:
            return jsonify({"message": "Reset code sent to your email"}), 200
        else:
            db.session.rollback()
            return jsonify({
                "error": f"Email service failed: {error_detail}",
                "message": "Reset code could not be sent."
            }), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/user/forgot-password', methods=['POST'])
def user_forgot_password():
    data = get_request_data()
    return process_forgot_password(data.get('email'), allowed_role="user")

@app.route('/dealer/forgot-password', methods=['POST'])
def dealer_forgot_password():
    data = get_request_data()
    return process_forgot_password(data.get('email'), allowed_role="dealer")

# ================= HELPERS FOR PASSWORD RESET =================
def process_reset_password(code, allowed_role=None):
    try:
        target = None
        if allowed_role == "user" or allowed_role is None:
            target = User.query.filter_by(reset_code=code).first()
        
        if not target and (allowed_role == "dealer" or allowed_role is None):
            target = Dealer.query.filter_by(reset_code=code).first()

        if not target:
            return jsonify({"error": "Invalid or expired reset code"}), 400

        if not target.reset_expiry or target.reset_expiry < datetime.utcnow():
            return jsonify({"error": "Reset code expired"}), 400

        data = get_request_data()
        new_password = data.get("password")
        confirm_password = data.get("confirm_password")

        if not new_password or not confirm_password:
            return jsonify({"error": "Password and confirm password are required"}), 400

        if new_password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        target.password_hash = new_password
        target.reset_code = None
        target.reset_expiry = None
        db.session.commit()

        return jsonify({"message": "Password updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/user/reset-password/<code>', methods=['POST'])
def user_reset_password(code):
    return process_reset_password(code, allowed_role="user")

@app.route('/dealer/reset-password/<code>', methods=['POST'])
def dealer_reset_password(code):
    return process_reset_password(code, allowed_role="dealer")
def create_default_admin():
    admin_email = "admin@gmail.com"
    existing_admin = Admin.query.filter_by(email=admin_email).first()
    if not existing_admin:
        password_hash = "admin123"
        new_admin = Admin(
            name="Super Admin",
            email=admin_email,
            phone="9876543210",
            password_hash=password_hash,
            office_location="Central Headquarters"
        )
        db.session.add(new_admin)  
        db.session.commit()
        print("Default admin created successfully.")
    else:
        print("Default admin already exists.")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_default_admin()

    app.run(host="0.0.0.0", port=5050, debug=True)
