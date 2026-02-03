from app import create_app
from app.models import InteractionType, CadenceRule, Interaction, Visit, User
from config.database import db_session, engine, Base

app = create_app()

def seed_interactions():
    with app.app_context():
        print("Initializing Interaction Tables...")
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        
        # 1. Define Standard Types
        # Calls
        call_types = [
            ('Exploratory Call', 'fas fa-phone', True),
            ('Follow-up Call', 'fas fa-phone-volume', True),
            ('Negotiation Call', 'fas fa-hand-holding-usd', True),
            ('Closing Call', 'fas fa-check-circle', True),
        ]
        
        # Visits
        visit_types = [
            ('Cold Visit', 'fas fa-walking', False),
            ('Presentation Visit', 'fas fa-laptop', False),
            ('Technical Visit', 'fas fa-tools', False),
            ('Closing Visit', 'fas fa-signature', False),
        ]
        
        type_map = {} # Name -> ID
        
        print("Seeding Types...")
        for name, icon, is_call in call_types + visit_types:
            existing = InteractionType.query.filter_by(name=name).first()
            if not existing:
                it = InteractionType(name=name, icon=icon, is_call=is_call)
                db_session.add(it)
                db_session.flush() # Get ID
                type_map[name] = it.id
                print(f"Created: {name}")
            else:
                type_map[name] = existing.id
                print(f"Exists: {name}")

        # 2. Define Cadence Rules
        print("Seeding Rules...")
        rules = [
            ('Cold Visit', 'Follow-up Call', 2),
            ('Presentation Visit', 'Negotiation Call', 3),
            ('Exploratory Call', 'Presentation Visit', 5),
            ('Negotiation Call', 'Closing Call', 2),
        ]
        
        for trigger, next_step, days in rules:
            t_id = type_map.get(trigger)
            n_id = type_map.get(next_step)
            
            if t_id and n_id:
                existing = CadenceRule.query.filter_by(trigger_type_id=t_id, suggested_next_type_id=n_id).first()
                if not existing:
                    rule = CadenceRule(trigger_type_id=t_id, suggested_next_type_id=n_id, delay_days=days)
                    db_session.add(rule)
                    print(f"Rule: {trigger} -> {next_step} (+{days}d)")
        
        # 3. Migrate Existing Visits
        print("Migrating Legacy Visits...")
        old_visits = Visit.query.all()
        migrated_count = 0
        
        # Default fallback type
        default_type_id = type_map['Cold Visit']
        
        for v in old_visits:
            # Check if this visit is already migrated (simple check: if interaction exists with same date/client)
            # This is not perfect but prevents double seeding on re-runs
            exists = Interaction.query.filter_by(
                client_id=v.client_id, 
                date=v.visit_date
            ).first()
            
            if not exists:
                # Try to guess type from content
                interaction_type_id = default_type_id
                content = (v.notes or "").lower()
                
                if "technic" in content or "check" in content:
                    interaction_type_id = type_map['Technical Visit']
                elif "propos" in content:
                    interaction_type_id = type_map['Presentation Visit']
                
                new_interaction = Interaction(
                    client_id=v.client_id,
                    user_id=v.user_id,
                    type_id=interaction_type_id,
                    date=v.visit_date,
                    status='done',
                    notes=f"{v.notes} (Legacy Visit ID: {v.id})"
                )
                db_session.add(new_interaction)
                migrated_count += 1
        
        try:
            db_session.commit()
            print(f"Seeding Complete! Migrated {migrated_count} visits.")
        except Exception as e:
            db_session.rollback()
            print(f"Error during seeding: {e}")
        finally:
            db_session.remove()

if __name__ == '__main__':
    seed_interactions()
