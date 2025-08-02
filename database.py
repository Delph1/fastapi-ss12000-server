# database.py
import os
from datetime import datetime

from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from sqlalchemy import desc, asc

# --- Databas configuration ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL-miljövariabeln är inte inställd")

engine = create_engine(DATABASE_URL)

Base = declarative_base()

# --- SQLAlchemy models ---

class Organisation(Base):
    """Mappar mot tabellen 'organisations'."""
    __tablename__ = "organisations"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    placements = relationship("Placement", back_populates="organisation")

class Person(Base):
    """Mappar mot tabellen 'persons'."""
    __tablename__ = "persons"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    securityMarking = Column(String(50), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    placements = relationship("Placement", back_populates="person")
    attendance = relationship("Attendance", back_populates="person")
    grades = relationship("Grade", back_populates="person")
    aggregated_attendance = relationship("AggregatedAttendance", back_populates="person")

class Placement(Base):
    """Mappar mot tabellen 'placements'."""
    __tablename__ = "placements"
    id = Column(String(36), primary_key=True)
    organisation_id = Column(String(36), ForeignKey("organisations.id"))
    person_id = Column(String(36), ForeignKey("persons.id"))
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    organisation = relationship("Organisation", back_populates="placements")
    person = relationship("Person", back_populates="placements")

class Duty(Base):
    """Mappar mot tabellen 'duties'."""
    __tablename__ = "duties"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

class Group(Base):
    """Mappar mot tabellen 'groups'."""
    __tablename__ = "groups"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

class Programme(Base):
    """Mappar mot tabellen 'programmes'."""
    __tablename__ = "programmes"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

class StudyPlan(Base):
    """Mappar mot tabellen 'studyPlans'."""
    __tablename__ = "studyPlans"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

class Syllabus(Base):
    """Mappar mot tabellen 'syllabuses'."""
    __tablename__ = "syllabuses"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

class SchoolUnitOffering(Base):
    """Mappar mot tabellen 'schoolUnitOfferings'."""
    __tablename__ = "schoolUnitOfferings"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

class Activity(Base):
    """Mappar mot tabellen 'activities'."""
    __tablename__ = "activities"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    calendar_events = relationship("CalendarEvent", back_populates="activity")
    attendance_records = relationship("Attendance", back_populates="activity")

class CalendarEvent(Base):
    """Mappar mot tabellen 'calendarEvents'."""
    __tablename__ = "calendarEvents"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    activity_id = Column(String(36), ForeignKey("activities.id"))
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    activity = relationship("Activity", back_populates="calendar_events")

class Attendance(Base):
    """Mappar mot tabellen 'attendance'."""
    __tablename__ = "attendance"
    id = Column(String(36), primary_key=True)
    person_id = Column(String(36), ForeignKey("persons.id"))
    activity_id = Column(String(36), ForeignKey("activities.id"))
    attendance_event_id = Column(String(36), ForeignKey("attendanceEvents.id"))
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    person = relationship("Person", back_populates="attendance")
    activity = relationship("Activity", back_populates="attendance_records")
    attendance_event = relationship("AttendanceEvent", back_populates="attendance_records")

class AttendanceEvent(Base):
    """Mappar mot tabellen 'attendanceEvents'."""
    __tablename__ = "attendanceEvents"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    attendance_records = relationship("Attendance", back_populates="attendance_event")

class AttendanceSchedule(Base):
    """Mappar mot tabellen 'attendanceSchedules'."""
    __tablename__ = "attendanceSchedules"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

class Grade(Base):
    """Mappar mot tabellen 'grades'."""
    __tablename__ = "grades"
    id = Column(String(36), primary_key=True)
    person_id = Column(String(36), ForeignKey("persons.id"))
    grade_value = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    # Relation till Person
    person = relationship("Person", back_populates="grades")

class AggregatedAttendance(Base):
    """Mappar mot tabellen 'aggregatedAttendance'."""
    __tablename__ = "aggregatedAttendance"
    id = Column(String(36), primary_key=True)
    person_id = Column(String(36), ForeignKey("persons.id"))
    attendance_percentage = Column(Float, nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    # Relation till Person
    person = relationship("Person", back_populates="aggregated_attendance")

class Resource(Base):
    """Mappar mot tabellen 'resources'."""
    __tablename__ = "resources"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

class Room(Base):
    """Mappar mot tabellen 'rooms'."""
    __tablename__ = "rooms"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

class Subscription(Base):
    """Mappar mot tabellen 'subscriptions'."""
    __tablename__ = "subscriptions"
    id = Column(String(36), primary_key=True)
    resource_type = Column(String(255), nullable=False)
    resource_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

class DeletedEntity(Base):
    """Mappar mot tabellen 'deletedEntities'."""
    __tablename__ = "deletedEntities"
    id = Column(String(36), primary_key=True)
    resource_type = Column(String(255), nullable=False)
    deleted_at = Column(DateTime, nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

class Log(Base):
    """Mappar mot tabellen 'log'."""
    __tablename__ = "log"
    id = Column(String(36), primary_key=True)
    log_message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)