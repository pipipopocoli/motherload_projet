"""SQLAlchemy ORM models for Motherload acquisition system."""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.paths import get_db_path


Base = declarative_base()


class Journal(Base):
    """Journal metadata table."""
    
    __tablename__ = "journals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    issn = Column(String(20), unique=True)
    publisher = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Journal(id={self.id}, name='{self.name}', issn='{self.issn}')>"


class Article(Base):
    """Article metadata table for acquisition tracking."""
    
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    doi = Column(String(200), unique=True)
    title = Column(Text, nullable=False)
    authors = Column(Text)  # Stored as semicolon-separated string
    year = Column(Integer)
    journal = Column(String(500))
    abstract = Column(Text)
    url = Column(String(1000))
    pdf_url = Column(String(1000))
    source = Column(String(100))  # e.g., "unpaywall", "scihub", "manual"
    confidence = Column(Float)  # Confidence score for metadata quality (0.0-1.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Article(id={self.id}, doi='{self.doi}', title='{self.title[:50]}...')>"


def get_engine():
    """Create and return SQLAlchemy engine."""
    db_path = get_db_path()
    return create_engine(f"sqlite:///{db_path}", echo=False)


def get_session():
    """Create and return a new database session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """
    Initialize the database by creating all tables.
    
    This is idempotent - safe to call multiple times.
    """
    db_path = get_db_path()
    engine = get_engine()
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    print(f"✓ Database initialized at: {db_path}")
    print(f"✓ Tables created: {', '.join(Base.metadata.tables.keys())}")
    
    return db_path
