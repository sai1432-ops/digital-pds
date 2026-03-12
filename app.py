from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from datetime import datetime, timedelta
import secrets
import uuid
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ultralytics import YOLO
from werkzeug.utils import secure_filename
from sqlalchemy import text
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret-key")
app.config["GOOGLE_PLACES_API_KEY"] = os.environ.get("GOOGLE_PLACES_API_KEY", "")

print("GOOGLE_PLACES_API_KEY =", app.config["GOOGLE_PLACES_API_KEY"][:12] if app.config["GOOGLE_PLACES_API_KEY"] else "EMPTY")

jwt = JWTManager(app)

# ================= DATABASE CONFIG =================
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/digitalpds"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ================= FLASK-MAIL CONFIG =================
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = 'appanagirisai7569@gmail.com'
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = 'yourmail@gmail.com'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "best.pt")
model = YOLO(MODEL_PATH)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ================= HELPER FUNCTION =================
def get_request_data():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict() or {}


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


# ================= HOME ROUTE =================
@app.route("/")
def home():
    return "Server is working"


# ================= MODELS =================
class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255))


class Dealer(db.Model):
    __tablename__ = "dealers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    company_name = db.Column(db.String(150))
    password_hash = db.Column(db.String(255))


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255))
    pds_card_no = db.Column(db.String(50), unique=True)
    pds_linked_at = db.Column(db.DateTime)
    pds_verified = db.Column(db.Boolean, default=False)
    reset_code = db.Column(db.String(255), nullable=True)
    reset_expiry = db.Column(db.DateTime, nullable=True)


class DealerStock(db.Model):
    __tablename__ = "dealer_stock"

    id = db.Column(db.Integer, primary_key=True)
    dealer_id = db.Column(db.Integer, db.ForeignKey("dealers.id"), nullable=False)
    item_name = db.Column(
        db.Enum("ADULT_BRUSH", "CHILD_BRUSH", "TOOTHPASTE", "FLYER"),
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
    urgency = db.Column(db.String(50), default="Normal")
    status = db.Column(db.Enum("PENDING", "APPROVED", "DISPATCHED", "REJECTED"), default="PENDING")
    requested_at = db.Column(db.DateTime, server_default=db.func.now())
    reviewed_at = db.Column(db.DateTime)
    dispatched_at = db.Column(db.DateTime)
    admin_note = db.Column(db.Text)
    courier_name = db.Column(db.String(120))
    tracking_id = db.Column(db.String(120))


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
    brush_received = db.Column(db.Boolean, default=False)
    paste_received = db.Column(db.Boolean, default=False)
    iec_received = db.Column(db.Boolean, default=False)


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
    booking_available = db.Column(db.Boolean, default=True)


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("family_members.id"), nullable=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(50))
    status = db.Column(db.Enum("BOOKED", "COMPLETED", "CANCELLED"), default="BOOKED")
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class TeethReport(db.Model):
    __tablename__ = "teeth_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    member_id = db.Column(db.Integer)
    image_path = db.Column(db.String(255))
    ai_result = db.Column(db.Text)
    risk_level = db.Column(db.String(20))
    created_at = db.Column(db.DateTime)


# ================= ADMIN REGISTER ROUTE =================
@app.route("/admin/register", methods=["POST"])
def admin_register():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    required_fields = ["name", "email", "password", "phone"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if Admin.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    new_admin = Admin(
        name=data["name"],
        email=data["email"],
        phone=data["phone"],
        password_hash=hashed_password
    )

    db.session.add(new_admin)
    db.session.commit()

    return jsonify({"message": "Admin registered successfully"}), 201


# ================= DEALER REGISTER ROUTE =================
@app.route("/dealer/register", methods=["POST"])
def dealer_register():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    required_fields = ["name", "email", "password", "phone", "company_name"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if Dealer.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    new_dealer = Dealer(
        name=data["name"],
        email=data["email"],
        phone=data["phone"],
        company_name=data["company_name"],
        password_hash=hashed_password
    )

    db.session.add(new_dealer)
    db.session.commit()

    return jsonify({"message": "Dealer registered successfully"}), 201


# ================= USER REGISTER ROUTE =================
@app.route("/user/register", methods=["POST"])
def user_register():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    required_fields = ["name", "email", "password", "phone"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    new_user = User(
        name=data["name"],
        email=data["email"],
        phone=data["phone"],
        password_hash=hashed_password
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "user_id": new_user.id,
        "name": new_user.name
    }), 201


# ================= ADMIN LOGIN ROUTE =================
@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "email and password are required"}), 400

    admin = Admin.query.filter_by(email=data["email"]).first()

    if not admin or not bcrypt.check_password_hash(admin.password_hash, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=admin.id)
    return jsonify({
        "message": "Admin login successful",
        "access_token": access_token,
        "admin_id": admin.id,
        "name": admin.name
    }), 200


# ================= DEALER LOGIN ROUTE =================
@app.route("/dealer/login", methods=["POST"])
def dealer_login():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "email and password are required"}), 400

    dealer = Dealer.query.filter_by(email=data["email"]).first()

    if not dealer or not bcrypt.check_password_hash(dealer.password_hash, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=dealer.id)
    return jsonify({
        "message": "Dealer login successful",
        "access_token": access_token,
        "dealer_id": dealer.id,
        "name": dealer.name
    }), 200


# ================= USER LOGIN ROUTE =================
@app.route("/user/login", methods=["POST"])
def user_login():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=data["email"]).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.id)

    return jsonify({
        "message": "User login successful",
        "access_token": access_token,
        "user_id": user.id,
        "name": user.name,
        "pds_verified": bool(user.pds_verified),
        "pds_card_no": user.pds_card_no
    }), 200


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


# ================= UPDATE ADMIN PROFILE ROUTE =================
@app.route("/admin/update-profile/<int:admin_id>", methods=["PUT"])
@jwt_required()
def update_admin_profile(admin_id):
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    admin = Admin.query.get(admin_id)

    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    if "name" in data:
        admin.name = data["name"]
    if "phone" in data:
        admin.phone = data["phone"]
    if "email" in data:
        existing = Admin.query.filter_by(email=data["email"]).first()
        if existing and existing.id != admin_id:
            return jsonify({"error": "Email already in use"}), 400
        admin.email = data["email"]
    if "password" in data:
        admin.password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    db.session.commit()

    return jsonify({"message": "Admin profile updated successfully"}), 200


# ================= UPDATE DEALER PROFILE ROUTE =================
@app.route("/dealer/update-profile/<int:dealer_id>", methods=["PUT"])
@jwt_required()
def update_dealer_profile(dealer_id):
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    dealer = Dealer.query.get(dealer_id)

    if not dealer:
        return jsonify({"error": "Dealer not found"}), 404

    if "name" in data:
        dealer.name = data["name"]
    if "phone" in data:
        dealer.phone = data["phone"]
    if "company_name" in data:
        dealer.company_name = data["company_name"]
    if "email" in data:
        existing = Dealer.query.filter_by(email=data["email"]).first()
        if existing and existing.id != dealer_id:
            return jsonify({"error": "Email already in use"}), 400
        dealer.email = data["email"]
    if "password" in data:
        dealer.password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    db.session.commit()

    return jsonify({"message": "Dealer profile updated successfully"}), 200


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
        user.password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

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
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    required_fields = ["dealer_id", "item_name", "quantity"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    new_stock = DealerStock(
        dealer_id=data["dealer_id"],
        item_name=data["item_name"],
        quantity=data["quantity"]
    )

    db.session.add(new_stock)
    db.session.commit()

    return jsonify({"message": "Stock added successfully"}), 201


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
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    required_fields = ["dealer_id", "item_name", "quantity"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    stock = DealerStock.query.filter_by(
        dealer_id=data["dealer_id"],
        item_name=data["item_name"]
    ).first()

    if not stock:
        return jsonify({"error": "Stock item not found"}), 404

    stock.quantity = data["quantity"]

    db.session.commit()

    return jsonify({
        "message": "Stock updated successfully",
        "dealer_id": stock.dealer_id,
        "item_name": stock.item_name,
        "new_quantity": stock.quantity
    }), 200


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
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    dealer_id = data.get("dealer_id")
    adult_brush_qty = int(data.get("adult_brush_qty", 0) or 0)
    child_brush_qty = int(data.get("child_brush_qty", 0) or 0)
    paste_qty = int(data.get("paste_qty", 0) or 0)
    iec_qty = int(data.get("iec_qty", 0) or 0)
    urgency = data.get("urgency", "Normal")

    if not dealer_id:
        return jsonify({"error": "dealer_id is required"}), 400

    if adult_brush_qty + child_brush_qty + paste_qty + iec_qty <= 0:
        return jsonify({"error": "At least one quantity must be greater than zero"}), 400

    dealer = Dealer.query.get(int(dealer_id))
    if not dealer:
        return jsonify({"error": "Dealer not found"}), 404

    request_group_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"

    items_to_add = []

    if adult_brush_qty > 0:
        items_to_add.append(("ADULT_BRUSH", adult_brush_qty))
    if child_brush_qty > 0:
        items_to_add.append(("CHILD_BRUSH", child_brush_qty))
    if paste_qty > 0:
        items_to_add.append(("TOOTHPASTE", paste_qty))
    if iec_qty > 0:
        items_to_add.append(("FLYER", iec_qty))

    for item_name, qty in items_to_add:
        new_request = StockRequest(
            request_id=request_group_id,
            dealer_id=int(dealer_id),
            item_name=item_name,
            requested_quantity=qty,
            urgency=urgency,
            status="PENDING"
        )
        db.session.add(new_request)

    db.session.commit()

    return jsonify({
        "message": "Stock request sent successfully",
        "request_group_id": request_group_id
    }), 201


# ================= ADMIN APPROVE STOCK ROUTE =================
@app.route("/admin/stock-requests", methods=["GET"])
def get_admin_stock_requests():
    requests_list = StockRequest.query.order_by(StockRequest.requested_at.desc()).all()

    result = []
    for req in requests_list:
        dealer = Dealer.query.get(req.dealer_id)

        item_label = req.item_name
        if req.item_name == "ADULT_BRUSH":
            item_label = "Adult Brush"
        elif req.item_name == "CHILD_BRUSH":
            item_label = "Child Brush"
        elif req.item_name == "TOOTHPASTE":
            item_label = "Paste"
        elif req.item_name == "FLYER":
            item_label = "IEC Materials"

        result.append({
            "id": req.id,
            "request_id": req.request_id,
            "dealer_id": req.dealer_id,
            "dealer_name": dealer.name if dealer else f"Dealer #{req.dealer_id}",
            "location": dealer.company_name if dealer and dealer.company_name else "Not Available",
            "kit_type": item_label,
            "quantity": f"{req.requested_quantity} Units",
            "status": req.status,
            "request_date": str(req.requested_at) if req.requested_at else "",
            "approved_at": str(req.reviewed_at) if req.status == "APPROVED" and req.reviewed_at else None,
            "rejected_at": str(req.reviewed_at) if req.status == "REJECTED" and req.reviewed_at else None,
            "dispatched_at": str(req.dispatched_at) if req.dispatched_at else None,
            "admin_note": req.admin_note,
            "courier_name": req.courier_name,
            "tracking_id": req.tracking_id
        })

    return jsonify(result), 200


@app.route("/admin/approve-stock/<int:request_id>", methods=["PUT"])
def approve_stock(request_id):
    stock_request = StockRequest.query.get(request_id)

    if not stock_request:
        return jsonify({"error": "Request not found"}), 404

    if stock_request.status != "PENDING":
        return jsonify({"error": "Only pending requests can be approved"}), 400

    stock_request.status = "APPROVED"
    stock_request.reviewed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({"message": "Stock request approved successfully"}), 200


# ================= ADMIN DISPATCH STOCK ROUTE =================
@app.route("/admin/dispatch-stock/<int:request_id>", methods=["PUT"])
def dispatch_stock(request_id):
    stock_request = StockRequest.query.get(request_id)

    if not stock_request:
        return jsonify({"error": "Request not found"}), 404

    if stock_request.status != "APPROVED":
        return jsonify({"error": "Only approved requests can be dispatched"}), 400

    stock_request.status = "DISPATCHED"
    stock_request.dispatched_at = datetime.utcnow()

    stock = DealerStock.query.filter_by(
        dealer_id=stock_request.dealer_id,
        item_name=stock_request.item_name
    ).first()

    if stock:
        stock.quantity += stock_request.requested_quantity
    else:
        new_stock = DealerStock(
            dealer_id=stock_request.dealer_id,
            item_name=stock_request.item_name,
            quantity=stock_request.requested_quantity
        )
        db.session.add(new_stock)

    db.session.commit()

    return jsonify({"message": "Stock dispatched successfully"}), 200


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
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    if not data.get("kit_unique_id"):
        return jsonify({"error": "kit_unique_id is required"}), 400

    kit = KitDistribution.query.filter_by(
        kit_unique_id=data["kit_unique_id"]
    ).first()

    if not kit:
        return jsonify({"error": "Invalid kit ID"}), 404

    if kit.status == "CONFIRMED":
        return jsonify({"error": "Kit already confirmed"}), 400

    if datetime.utcnow() > kit.expiry:
        return jsonify({"error": "Kit expired"}), 400

    for item in ["TOOTHBRUSH", "TOOTHPASTE"]:
        stock = DealerStock.query.filter_by(
            dealer_id=kit.dealer_id,
            item_name=item
        ).first()

        if stock and stock.quantity > 0:
            stock.quantity -= 1

    kit.status = "CONFIRMED"
    kit.confirmed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({"message": "Kit confirmed successfully"}), 200


# ================= USER CONFIRM KIT BY STATIC DEALER QR =================
@app.route("/user/confirm-kit-by-dealer-qr", methods=["POST"])
def confirm_kit_by_dealer_qr():
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received. Send JSON or form-data."}), 400

        required_fields = ["dealer_id", "beneficiary_id"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        dealer_id = int(data["dealer_id"])
        beneficiary_id = int(data["beneficiary_id"])

        old_kit_returned = str(data.get("old_kit_returned", "false")).lower() == "true"
        brush_received = str(data.get("brush_received", "false")).lower() == "true"
        paste_received = str(data.get("paste_received", "false")).lower() == "true"
        iec_received = str(data.get("iec_received", "false")).lower() == "true"

        dealer = Dealer.query.get(dealer_id)
        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404

        user = User.query.get(beneficiary_id)
        if not user:
            return jsonify({"error": "Beneficiary not found"}), 404

        if not user.pds_verified:
            return jsonify({"error": "User PDS is not linked/verified"}), 400

        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        existing = KitDistribution.query.filter(
            KitDistribution.beneficiary_id == beneficiary_id,
            KitDistribution.status == "CONFIRMED",
            KitDistribution.confirmed_at >= month_start
        ).first()

        if existing:
            return jsonify({"error": "Kit already received this month"}), 400

        for item_name, received in [
            ("TOOTHBRUSH", brush_received),
            ("TOOTHPASTE", paste_received),
            ("FLYER", iec_received)
        ]:
            if received:
                stock = DealerStock.query.filter_by(
                    dealer_id=dealer_id,
                    item_name=item_name
                ).first()

                if not stock or stock.quantity <= 0:
                    return jsonify({"error": f"Insufficient stock for {item_name}"}), 400

        for item_name, received in [
            ("TOOTHBRUSH", brush_received),
            ("TOOTHPASTE", paste_received),
            ("FLYER", iec_received)
        ]:
            if received:
                stock = DealerStock.query.filter_by(
                    dealer_id=dealer_id,
                    item_name=item_name
                ).first()
                stock.quantity -= 1

        new_distribution = KitDistribution(
            beneficiary_id=beneficiary_id,
            dealer_id=dealer_id,
            kit_unique_id=str(uuid.uuid4()),
            status="CONFIRMED",
            expiry=datetime.utcnow() + timedelta(hours=24),
            confirmed_at=datetime.utcnow(),
            confirmation_mode="USER_QR_SCAN",
            old_kit_returned=old_kit_returned,
            brush_received=brush_received,
            paste_received=paste_received,
            iec_received=iec_received
        )

        db.session.add(new_distribution)
        db.session.commit()

        return jsonify({
            "message": "Kit confirmed successfully",
            "distribution_id": new_distribution.id,
            "dealer_id": dealer_id,
            "beneficiary_id": beneficiary_id,
            "status": new_distribution.status
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= DEALER MANUAL CONFIRM DISTRIBUTION ROUTE =================
@app.route("/dealer/confirm-distribution", methods=["POST"])
def dealer_confirm_distribution():
    try:
        data = get_request_data()
        if not data:
            return jsonify({"error": "No data received. Send JSON or form-data."}), 400

        required_fields = ["dealer_id", "beneficiary_id"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        dealer_id = int(data["dealer_id"])
        beneficiary_id = int(data["beneficiary_id"])

        old_kit_returned = str(data.get("old_kit_returned", "false")).lower() == "true"
        brush_received = str(data.get("brush_received", "false")).lower() == "true"
        paste_received = str(data.get("paste_received", "false")).lower() == "true"
        iec_received = str(data.get("iec_received", "false")).lower() == "true"

        dealer = Dealer.query.get(dealer_id)
        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404

        user = User.query.get(beneficiary_id)
        if not user:
            return jsonify({"error": "Beneficiary not found"}), 404

        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        existing = KitDistribution.query.filter(
            KitDistribution.beneficiary_id == beneficiary_id,
            KitDistribution.status == "CONFIRMED",
            KitDistribution.confirmed_at >= month_start
        ).first()

        if existing:
            return jsonify({"error": "Kit already distributed to this beneficiary this month"}), 400

        for item_name, received in [
            ("TOOTHBRUSH", brush_received),
            ("TOOTHPASTE", paste_received),
            ("FLYER", iec_received)
        ]:
            if received:
                stock = DealerStock.query.filter_by(
                    dealer_id=dealer_id,
                    item_name=item_name
                ).first()

                if not stock or stock.quantity <= 0:
                    return jsonify({"error": f"Insufficient stock for {item_name}"}), 400

        for item_name, received in [
            ("TOOTHBRUSH", brush_received),
            ("TOOTHPASTE", paste_received),
            ("FLYER", iec_received)
        ]:
            if received:
                stock = DealerStock.query.filter_by(
                    dealer_id=dealer_id,
                    item_name=item_name
                ).first()
                stock.quantity -= 1

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
            "message": "Dealer distribution confirmed successfully",
            "distribution_id": new_distribution.id,
            "dealer_id": dealer_id,
            "beneficiary_id": beneficiary_id,
            "status": new_distribution.status,
            "confirmation_mode": new_distribution.confirmation_mode
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ================= DEALER QR DATA ROUTE =================
@app.route("/dealer/qr/<int:dealer_id>", methods=["GET"])
def get_dealer_qr_data(dealer_id):
    dealer = Dealer.query.get(dealer_id)
    if not dealer:
        return jsonify({"error": "Dealer not found"}), 404

    return jsonify({
        "type": "DEALER",
        "dealer_id": dealer.id,
        "dealer_name": dealer.name
    }), 200


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

        existing = db.session.execute(
            text("SELECT id FROM users WHERE pds_card_no = :card"),
            {"card": pds_card_no}
        ).fetchone()

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

        return jsonify({
            "message": "PDS linked successfully",
            "user_id": int(user_id),
            "pds_card_no": pds_card_no
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
def get_family_members(user_id):
    rows = db.session.execute(text("""
        SELECT id, user_id, member_name, age, relation, brushing_target, weekly_brush_count
        FROM family_members
        WHERE user_id = :uid
    """), {"uid": user_id}).mappings().all()

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

    required_fields = ["clinic_name", "address", "district", "contact_number"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    booking_available_raw = data.get("booking_available", True)
    if isinstance(booking_available_raw, str):
        booking_available = booking_available_raw.lower() in ["true", "1", "yes"]
    else:
        booking_available = bool(booking_available_raw)

    new_clinic = Clinic(
        clinic_name=data["clinic_name"],
        address=data["address"],
        district=data["district"],
        contact_number=data["contact_number"],
        latitude=float(data["latitude"]) if data.get("latitude") not in [None, ""] else None,
        longitude=float(data["longitude"]) if data.get("longitude") not in [None, ""] else None,
        booking_available=booking_available
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
            "booking_available": clinic.booking_available
        })

    return jsonify(result), 200


# ================= USER BOOK APPOINTMENT ROUTE =================
@app.route("/user/book-appointment", methods=["POST"])
def book_appointment():
    data = get_request_data()
    if not data:
        return jsonify({"error": "No data received. Send JSON or form-data."}), 400

    required_fields = ["user_id", "clinic_id", "appointment_date", "time_slot"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    appointment_date = datetime.strptime(data["appointment_date"], "%Y-%m-%d").date()
    member_id = data.get("member_id")

    if member_id not in [None, ""]:
        member = FamilyMember.query.filter_by(id=int(member_id), user_id=int(data["user_id"])).first()
        if not member:
            return jsonify({"error": "Invalid member_id for this user"}), 400
        member_id = int(member_id)
    else:
        member_id = None

    clinic = Clinic.query.get(int(data["clinic_id"]))
    if not clinic:
        return jsonify({"error": "Clinic not found"}), 404

    if clinic.booking_available is False:
        return jsonify({"error": "Booking is not available for this clinic"}), 400

    new_appointment = Appointment(
        user_id=int(data["user_id"]),
        member_id=member_id,
        clinic_id=int(data["clinic_id"]),
        appointment_date=appointment_date,
        time_slot=data["time_slot"],
        status="BOOKED"
    )

    db.session.add(new_appointment)
    db.session.commit()

    return jsonify({"message": "Appointment booked successfully"}), 201


# ================= VIEW USER APPOINTMENTS ROUTE =================
@app.route("/user/view-appointments/<int:user_id>", methods=["GET"])
def view_appointments(user_id):
    appointments = Appointment.query.filter_by(user_id=user_id).order_by(
        Appointment.appointment_date.desc(),
        Appointment.created_at.desc()
    ).all()

    result = []
    for appo in appointments:
        clinic = Clinic.query.get(appo.clinic_id)

        result.append({
            "id": appo.id,
            "clinic_id": appo.clinic_id,
            "clinic_name": clinic.clinic_name if clinic else None,
            "address": clinic.address if clinic else None,
            "district": clinic.district if clinic else None,
            "member_id": appo.member_id,
            "appointment_date": str(appo.appointment_date),
            "time_slot": appo.time_slot,
            "status": appo.status
        })

    return jsonify(result), 200


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
        result.append({
            "id": report.id,
            "image_path": report.image_path,
            "ai_result": report.ai_result,
            "risk_level": report.risk_level,
            "created_at": str(report.created_at)
        })

    return jsonify(result), 200


# ================= AI PREDICTION ROUTE =================
@app.route('/user/teeth-ai', methods=['POST'])
def teeth_ai():
    try:
        if 'image' not in request.files:
            return jsonify({"message": "Image is required"}), 400

        image = request.files['image']
        user_id = request.form.get('user_id')
        member_id = request.form.get('member_id')

        if not user_id:
            return jsonify({"message": "user_id is required"}), 400

        user_id = int(user_id)
        member_id = int(member_id) if member_id not in [None, ""] else None

        if member_id is not None:
            family_member = FamilyMember.query.filter_by(id=member_id, user_id=user_id).first()
            if not family_member:
                return jsonify({"message": "Invalid member_id for this user"}), 404

        filename = secure_filename(image.filename)
        upload_folder = os.path.join(app.root_path, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        saved_path = os.path.join(upload_folder, f"{uuid.uuid4()}_{filename}")
        image.save(saved_path)

        result = model.predict(source=saved_path, imgsz=640, conf=0.25, verbose=False)[0]

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

        ai_result = f"Disease: {predicted_class}, Confidence: {confidence:.2f}"

        new_report = TeethReport(
            user_id=user_id,
            member_id=member_id,
            image_path=saved_path,
            ai_result=ai_result,
            risk_level=risk_level,
            created_at=datetime.utcnow()
        )
        db.session.add(new_report)
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
def get_dealers():
    dealers = Dealer.query.all()

    result = []
    for d in dealers:
        result.append({
            "id": d.id,
            "name": d.name,
            "email": d.email,
            "phone": d.phone,
            "company_name": d.company_name
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

        if total_distributions > 0:
            kit_given_percentage = int((confirmed_count / total_distributions) * 100)
            kit_pending_percentage = int((pending_count / total_distributions) * 100)
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
            "returnRate": "0%",
            "returnRateChange": "0%",
            "isReturnRatePositive": False,
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
        dealer = Dealer.query.get(dealer_id)
        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404

        stock_items = DealerStock.query.filter_by(dealer_id=dealer_id).all()
        kit_rows = KitDistribution.query.filter_by(dealer_id=dealer_id).all()

        total_stock_quantity = sum(item.quantity for item in stock_items)
        distributed_kits = sum(1 for k in kit_rows if k.status == "CONFIRMED")
        returned_kits = 0
        remaining_kits = total_stock_quantity

        today = datetime.utcnow().date()
        today_distributions = 0
        for k in kit_rows:
            if k.created_at and k.created_at.date() == today:
                today_distributions += 1

        daily_target = 10
        performance_percentage = int((today_distributions / daily_target) * 100) if daily_target > 0 else 0

        item_counts = []
        for item in stock_items:
            item_counts.append({
                "name": item.item_name,
                "count": str(item.quantity)
            })

        sorted_kits = sorted(
            kit_rows,
            key=lambda x: x.created_at if x.created_at else datetime.min,
            reverse=True
        )

        recent_transactions = []
        for k in sorted_kits[:5]:
            recent_transactions.append({
                "name": f"Kit #{k.id}",
                "details": f"Beneficiary ID: {k.beneficiary_id} | Status: {k.status}",
                "quantity": "1 Kit"
            })

        return jsonify({
            "todayDistributions": str(today_distributions),
            "performancePercentage": performance_percentage,
            "totalKits": str(total_stock_quantity),
            "totalKitsChange": "+0%",
            "isTotalKitsPositive": True,
            "distributedKits": str(distributed_kits),
            "distributedKitsChange": "+0%",
            "isDistributedPositive": True,
            "remainingKits": str(remaining_kits),
            "remainingKitsChange": "+0%",
            "isRemainingPositive": True,
            "returnedKits": str(returned_kits),
            "returnedKitsChange": "+0%",
            "isReturnedPositive": False,
            "itemCounts": item_counts,
            "recentTransactions": recent_transactions
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= ADMIN BENEFICIARIES ROUTE =================
@app.route("/admin/beneficiaries", methods=["GET"])
def get_admin_beneficiaries():
    try:
        users = User.query.order_by(User.id.desc()).all()

        result = []
        for user in users:
            result.append({
                "id": user.id,
                "name": user.name,
                "pds_card_no": user.pds_card_no,
                "pds_verified": bool(user.pds_verified),
                "pds_linked_at": str(user.pds_linked_at) if user.pds_linked_at else None,
                "phone": user.phone,
                "email": user.email
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= DEALER BENEFICIARIES ROUTE =================
@app.route("/dealer/beneficiaries/<int:dealer_id>", methods=["GET"])
def get_dealer_beneficiaries(dealer_id):
    try:
        dealer = Dealer.query.get(dealer_id)

        if not dealer:
            return jsonify({"error": "Dealer not found"}), 404

        users = User.query.order_by(User.id.desc()).all()

        result = []

        for user in users:
            result.append({
                "name": user.name,
                "ration_id": user.pds_card_no if user.pds_card_no else "Not Linked",
                "household_id": f"HH-{user.id}",
                "is_active": bool(user.pds_verified)
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= FORGOT PASSWORD ROUTE =================
@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    code = secrets.token_urlsafe(32)
    user.reset_code = code
    user.reset_expiry = datetime.utcnow() + timedelta(minutes=15)
    db.session.commit()

    reset_link = f"http://127.0.0.1:5000/api/reset-password/{code}"

    msg = Message(
        subject="Reset Your Password",
        recipients=[email]
    )
    msg.body = f"""
Hello,

Click the link below to reset your password:

{reset_link}

This link is valid for 15 minutes.
"""
    mail.send(msg)

    return jsonify({"message": "Reset link sent to email"}), 200


# ================= RESET PASSWORD ROUTE =================
@app.route('/api/reset-password/<code>', methods=['POST'])
def reset_password(code):
    user = User.query.filter_by(reset_code=code).first()

    if not user:
        return jsonify({"error": "Invalid reset link"}), 400

    if not user.reset_expiry or user.reset_expiry < datetime.utcnow():
        return jsonify({"error": "Reset link expired"}), 400

    data = request.get_json()
    new_password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not new_password or not confirm_password:
        return jsonify({"error": "Password and confirm password are required"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.reset_code = None
    user.reset_expiry = None
    db.session.commit()

    return jsonify({"message": "Password updated successfully"}), 200


# ================= MAIN =================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True)