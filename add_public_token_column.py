import os
from flask import Flask
from app import create_app, db
from sqlalchemy import text

app = create_app()

def add_column():
    with app.app_context():
        try:
            # Check if column exists
            result = db.session.execute(text("SHOW COLUMNS FROM proposals LIKE 'public_token'")).fetchone()
            if not result:
                print("Adding 'public_token' column to 'proposals' table...")
                db.session.execute(text("ALTER TABLE proposals ADD COLUMN public_token VARCHAR(100) NULL"))
                db.session.execute(text("CREATE UNIQUE INDEX ix_proposals_public_token ON proposals (public_token)"))
                db.session.commit()
                print("Successfully added public_token column with unique index.")
            else:
                print("Column 'public_token' already exists in 'proposals' table.")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_column()
