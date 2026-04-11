from app import app, db, User

with app.app_context():
    # Update managed users who are not verified
    # Admins and Dealers create users with SELF or DEALER/ADMIN created_by_type
    unverified_managed_users = User.query.filter(
        User.created_by_type.in_(["ADMIN", "DEALER"]),
        User.email_verified == False
    ).all()
    
    print(f"Found {len(unverified_managed_users)} unverified managed users.")
    
    for user in unverified_managed_users:
        user.email_verified = True
        print(f"Verified user: {user.email}")
        
    db.session.commit()
    print("Database updated successfully.")
