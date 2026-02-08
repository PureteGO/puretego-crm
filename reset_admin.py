from app import create_app
from app.models import User
from config.database import db_session

app = create_app()

def reset_password():
    with app.app_context():
        admin_email = 'admin@puretego.online'
        user = User.query.filter_by(email=admin_email).first()
        if user:
            print(f"User {admin_email} found. Resetting password...")
            user.set_password('admin123')
            db_session.commit()
            print("Password reset to 'admin123'")
        else:
            print(f"User {admin_email} not found. Creating...")
            # Providing a dummy password to satisfy __init__
            user = User(name='Administrador', email=admin_email, password='temp_password')
            user.set_password('admin123')
            db_session.add(user)
            db_session.commit()
            print("User created with password 'admin123'")

if __name__ == '__main__':
    reset_password()
