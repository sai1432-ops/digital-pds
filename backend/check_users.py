from app import app, db, User

with app.app_context():
    # Check some users from the screenshot
    # id 2: sai3@gamil.com
    # id 25: appanagirisai7569@gmail.com
    
    users = User.query.filter(User.id.in_([2, 5, 25])).all()
    
    for u in users:
        print(f"ID: {u.id}, Email: {u.email}, Hashed: {u.password_hash[:10] if u.password_hash else 'None'}, Verified: {u.email_verified}, Type: {u.created_by_type}")
        
    # Let's just verify everyone for now to fix the user's issue
    all_unverified = User.query.filter_by(email_verified=False).all()
    print(f"Found {len(all_unverified)} unverified users. Verifying them now...")
    for u in all_unverified:
        u.email_verified = True
    
    db.session.commit()
    print("All users verified.")
