
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, joinedload
from sqlalchemy import or_

# Setup environment
sys.path.append(os.getcwd())
from config.database import Base, get_db
from app.models import Interaction, InteractionType, Client, Visit, Task, Project, ProjectTicket, User

# Mock session context
class MockSession:
    def get(self, key):
        if key == 'user_id': return 1 # Taking a guess at admin ID
        if key == 'role': return 'owner'
        if key == 'company_id': return 1
        return None

session = MockSession()

def debug_agenda():
    print("Starting Agenda Debug...")
    
    # Setup DB
    # Setup DB
    from config.database import engine, SessionLocal
    db = SessionLocal()
    
    try:
        now = datetime.now()
        end_of_today = now.replace(hour=23, minute=59, second=59)
        end_of_7_days = (now + timedelta(days=7)).replace(hour=23, minute=59, second=59)
        
        user_id = session.get('user_id')
        user_role = session.get('role')
        company_id = session.get('company_id')
        
        print(f"User ID: {user_id}, Role: {user_role}, Company: {company_id}")

        # 1. Test Interactions Query
        print("\n--- Testing Interactions Query ---")
        try:
            interaction_query = db.query(Interaction).options(joinedload(Interaction.client), joinedload(Interaction.type))\
                .join(Client).filter(
                    Interaction.status == 'scheduled',
                    Client.company_id == company_id
                )
            
            urgent_tasks = interaction_query.filter(Interaction.date <= end_of_today).all()
            print(f"Urgent Interactions Found: {len(urgent_tasks)}")
            for i in urgent_tasks:
                print(f" - ID: {i.id}, Date: {i.date}, Client: {i.client.name if i.client else 'None'}")
                
        except Exception as e:
            print(f"!!! ERROR in Interactions Query: {e}")

        # 2. Test Visits Query
        print("\n--- Testing Visits Query ---")
        try:
            visits_today = db.query(Visit).options(joinedload(Visit.client)).join(Client).filter(
                Visit.visit_date <= end_of_today,
                Visit.visit_date >= now.replace(hour=0, minute=0, second=0),
                Client.company_id == company_id
            ).all()
            print(f"Visits Today Found: {len(visits_today)}")
            
        except Exception as e:
            print(f"!!! ERROR in Visits Query: {e}")
            import traceback
            traceback.print_exc()

        # 3. Test Tasks Query
        print("\n--- Testing Tasks Query ---")
        try:
            task_query = db.query(Task).options(joinedload(Task.client)).filter(
                Task.status.in_(['open', 'in_progress', 'pending_approval']),
                Task.company_id == company_id
            )
            tasks_today = task_query.filter(Task.due_date <= end_of_today).all()
            print(f"Tasks Today Found: {len(tasks_today)}")
             # Inspect the first one to check columns
            if tasks_today:
                print(f" - First Task: {tasks_today[0].title}, Due: {tasks_today[0].due_date}")

        except Exception as e:
            print(f"!!! ERROR in Tasks Query: {e}")
            import traceback
            traceback.print_exc()
            
        # 4. Test Project Tickets Query
        print("\n--- Testing Project Tickets Query ---")
        try:
            ticket_query = db.query(ProjectTicket).join(Project).options(joinedload(ProjectTicket.project)).filter(
                ProjectTicket.status.in_(['pending', 'in_progress', 'pending_approval']),
                Project.status == 'active',
                Project.company_id == company_id
            )
            ticket_query = ticket_query.filter(ProjectTicket.assigned_to == user_id)
            tickets_today = ticket_query.filter(or_(ProjectTicket.due_date <= end_of_today, ProjectTicket.due_date.is_(None))).all()
            print(f"Tickets Today Found: {len(tickets_today)}")

        except Exception as e:
            print(f"!!! ERROR in Project Tickets Query: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"Global Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_agenda()
