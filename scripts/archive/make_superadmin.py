from app import create_app
from app.models import User
from config.database import get_db

app = create_app()

def make_user_superadmin(email):
    print(f"Setting superadmin privileges for {email}...")
    with app.app_context():
        with get_db() as db:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.is_superadmin = True
                db.commit()
                print(f"Success! User {user.name} ({user.email}) is now a Super Admin.")
            else:
                print(f"Error: User with email {email} not found.")

if __name__ == "__main__":
    # Using the email from the screenshot
    make_user_superadmin('janae@puretego.online')
