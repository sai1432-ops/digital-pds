import sys
import os

# Assume app.py is in the current directory (c:/xampp/htdocs/pdssystem/)
sys.path.append(os.path.abspath("c:/xampp/htdocs/pdssystem"))

from app import app, db, Clinic

def populate_clinics():
    with app.app_context():
        clove = Clinic.query.filter_by(clinic_name="Clove Dental").first()
        if not clove:
            clove = Clinic(
                clinic_name="Clove Dental",
                address="Multiple Locations - Chennai",
                district="Chennai",
                contact_number="18001200032",
                website="https://clovedental.in/",
                booking_available=True
            )
            db.session.add(clove)
            print("Added Clove Dental")

        dental32 = Clinic.query.filter_by(clinic_name="32 Dental Care").first()
        if not dental32:
            dental32 = Clinic(
                clinic_name="32 Dental Care",
                address="Multiple Locations - Chennai & Salem",
                district="Tamil Nadu",
                contact_number="9840222111",
                website="https://www.32dentalcare.org/",
                booking_available=True
            )
            db.session.add(dental32)
            print("Added 32 Dental Care")

        db.session.commit()
        print("Clinics populated successfully")

if __name__ == "__main__":
    populate_clinics()
