#!/usr/bin/env python3
"""
Database models and setup for GymIntel web application
Using SQLite for development (zero cost, zero setup)
"""

import os
import sys
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import JSON

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

Base = declarative_base()


class Gym(Base):
    """Gym data model - stores results from our existing CLI searches"""

    __tablename__ = "gyms"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(Text)
    phone = Column(String(20))
    website = Column(String(500))

    # Location data
    latitude = Column(Float)
    longitude = Column(Float)
    zipcode = Column(String(10), index=True)

    # Ratings and reviews
    rating = Column(Float)
    review_count = Column(Integer)
    price_level = Column(Integer)

    # GymIntel-specific data
    confidence_score = Column(Float)  # Our confidence scoring
    data_sources = Column(JSON)  # ["Yelp", "Google Places", "Merged"]
    source = Column(String(50))  # Primary source

    # Metadata
    raw_data = Column(JSON)  # Original API response
    instagram = Column(String(100))
    membership_fee = Column(String(50))

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Gym(name='{self.name}', confidence={self.confidence_score})>"


class Search(Base):
    """Search history - track API usage and performance"""

    __tablename__ = "searches"

    id = Column(Integer, primary_key=True)
    search_type = Column(String(20))  # 'zipcode', 'metro', 'batch'
    query = Column(String(100))  # ZIP code or metro code
    radius = Column(Integer)

    # Results
    results_count = Column(Integer)
    execution_time_ms = Column(Integer)

    # Metadata
    parameters = Column(JSON)  # Full search parameters
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Search(type='{self.search_type}', query='{self.query}')>"


class MetropolitanArea(Base):
    """Metropolitan area definitions from our Phase 2 work"""

    __tablename__ = "metropolitan_areas"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    state = Column(String(5))

    # Demographics
    population = Column(Integer)
    density_category = Column(String(20))  # low, medium, high, very_high

    # Market data
    zip_codes = Column(JSON)  # List of ZIP codes
    market_characteristics = Column(JSON)  # List of characteristics

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MetropolitanArea(code='{self.code}', name='{self.name}')>"


# Database setup
DATABASE_URL = "sqlite:///./gymintel.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def get_db():
    """Get database session for FastAPI dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_metro_data():
    """Initialize metropolitan area data from our Phase 2 definitions"""
    from metro_areas import METROPOLITAN_AREAS

    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(MetropolitanArea).count() > 0:
            print("📊 Metropolitan data already exists")
            return

        # Add all metro areas from our Phase 2 work
        for code, metro in METROPOLITAN_AREAS.items():
            db_metro = MetropolitanArea(
                code=code,
                name=metro.name,
                description=metro.description,
                state=metro.state,
                population=metro.population,
                density_category=metro.density_category,
                zip_codes=metro.zip_codes,
                market_characteristics=metro.market_characteristics,
            )
            db.add(db_metro)

        db.commit()
        print(f"✅ Initialized {len(METROPOLITAN_AREAS)} metropolitan areas")

    except Exception as e:
        print(f"❌ Error initializing metro data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Create database and initialize with metro data
    create_tables()
    init_metro_data()

    # Quick test
    db = SessionLocal()
    metro_count = db.query(MetropolitanArea).count()
    print(f"📊 Database ready with {metro_count} metropolitan areas")
    db.close()
