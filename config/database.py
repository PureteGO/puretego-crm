"""
PURETEGO CRM - Database Configuration
Configuração da conexão com MySQL usando SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

# Configurações do banco de dados
import os
from dotenv import load_dotenv

load_dotenv()

USE_SQLITE = os.environ.get('USE_SQLITE') == 'True'

if USE_SQLITE:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'app.db')
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    
    # Criar engine do SQLAlchemy para SQLite
    engine = create_engine(
        DATABASE_URL,
        connect_args={'check_same_thread': False}, # Necessário para SQLite com Flask
        echo=False
    )
else:
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', 3306)),
        'database': os.environ.get('DB_NAME', 'puretego_crm'),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASS', ''),
        'charset': 'utf8mb4'
    }

    # Criar URL de conexão
    DATABASE_URL = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset={DB_CONFIG['charset']}"
    )

    # Criar engine do SQLAlchemy
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False  # Mude para True para debug SQL
    )

# Criar session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar scoped session para thread-safety
db_session = scoped_session(SessionLocal)

# Base para os modelos
Base = declarative_base()
Base.query = db_session.query_property()


@contextmanager
def get_db():
    """
    Context manager para obter uma sessão do banco de dados.
    Uso:
        with get_db() as db:
            db.query(Model).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas.
    """
    Base.metadata.create_all(bind=engine)


def close_db():
    """
    Fecha a sessão do banco de dados.
    """
    db_session.remove()
