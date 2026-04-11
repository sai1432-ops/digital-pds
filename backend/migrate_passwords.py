from app import app, db, Admin, Dealer, User

def migrate():
    with app.app_context():
        print("Starting migration...")
        
        # Update Admins
        admins = Admin.query.all()
        for admin in admins:
            admin.password_hash = "welcome@123"
        print(f"Updated {len(admins)} admins.")
        
        # Update Dealers
        dealers = Dealer.query.all()
        for dealer in dealers:
            dealer.password_hash = "welcome@123"
        print(f"Updated {len(dealers)} dealers.")
        
        # Update Users (Beneficiaries)
        users = User.query.all()
        for user in users:
            user.password_hash = "welcome@123"
        print(f"Updated {len(users)} users.")
        
        db.session.commit()
        print("Migration completed successfully. All passwords set to 'welcome@123'")

if __name__ == "__main__":
    migrate()
