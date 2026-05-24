
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import engine, Base, SessionLocal
from app.models.interaction import InteractionType, CadenceRule, Interaction
# Import other models to ensure they are registered if needed, though here we just need to create these specific ones
from app.models.client import Client
from app.models.user import User
from app.models.deal import Deal

def migrate():
    print("Creating interaction tables...")
    # This will only create tables that don't exist
    Base.metadata.create_all(bind=engine, tables=[
        InteractionType.__table__,
        CadenceRule.__table__,
        Interaction.__table__
    ])
    print("Tables created successfully.")

    db = SessionLocal()
    try:
        # 1. Seed Interaction Types
        types_data = [
            # Calls
            {'name': 'Exploratory Call', 'icon': 'fas fa-phone-alt', 'is_call': True},
            {'name': 'Follow-up Call', 'icon': 'fas fa-phone-volume', 'is_call': True},
            {'name': 'Negotiation Call', 'icon': 'fas fa-comments-dollar', 'is_call': True},
            {'name': 'Closing Call', 'icon': 'fas fa-file-signature', 'is_call': True},
            # Visits
            {'name': 'Cold Visit (Door Knocking)', 'icon': 'fas fa-walking', 'is_call': False},
            {'name': 'Presentation Visit', 'icon': 'fas fa-chalkboard-teacher', 'is_call': False},
            {'name': 'Technical Visit', 'icon': 'fas fa-tools', 'is_call': False},
            {'name': 'Closing Visit', 'icon': 'fas fa-handshake', 'is_call': False},
        ]

        print("Seeding interaction types...")
        created_types = {}
        for t in types_data:
            existing = db.query(InteractionType).filter_by(name=t['name']).first()
            if not existing:
                new_type = InteractionType(**t)
                db.add(new_type)
                db.flush() # Get ID
                created_types[t['name']] = new_type
                print(f"  Created type: {t['name']}")
            else:
                created_types[t['name']] = existing
                print(f"  Type already exists: {t['name']}")

        # 2. Seed Cadence Rules
        rules_data = [
            ('Cold Visit (Door Knocking)', 'Follow-up Call', 2),
            ('Exploratory Call', 'Presentation Visit', 3),
            ('Presentation Visit', 'Follow-up Call', 2),
            ('Technical Visit', 'Presentation Visit', 1),
            ('Negotiation Call', 'Closing Call', 1),
        ]

        print("Seeding cadence rules...")
        for trigger_name, suggest_name, delay in rules_data:
            trigger = created_types.get(trigger_name)
            suggest = created_types.get(suggest_name)
            
            if trigger and suggest:
                existing = db.query(CadenceRule).filter_by(
                    trigger_type_id=trigger.id, 
                    suggested_next_type_id=suggest.id
                ).first()
                if not existing:
                    new_rule = CadenceRule(
                        trigger_type_id=trigger.id,
                        suggested_next_type_id=suggest.id,
                        delay_days=delay
                    )
                    db.add(new_rule)
                    print(f"  Created rule: {trigger_name} -> {suggest_name} (+{delay}d)")
            else:
                print(f"  Warning: Could not find types for rule: {trigger_name} or {suggest_name}")

        db.commit()
        print("Seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
