# database.py
import os
from datetime import date, datetime

from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

# --- Databas configuration ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL-miljövariabeln är inte inställd")

engine = create_engine(DATABASE_URL)

Base = declarative_base()

# --- SQLAlchemy models ---

class Organisation(Base):
    __tablename__ = "organisations"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(String(36), ForeignKey('organisations.id'))
    school_unit_code = Column(String(255))
    organisation_code = Column(String(255))
    municipality_code = Column(String(255))
    type = Column(String(50))
    school_types = Column(String(255)) # Lagras som en komma-separerad sträng
    start_date = Column(date)
    end_date = Column(date)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)
    
    # Define the relationship to itself for parent-child relationships
    parent = relationship("Organisation", remote_side=[id], back_populates="children")
    children = relationship("Organisation", back_populates="parent")

class Person(Base):
    __tablename__ = "persons"
    id = Column(String(36), primary_key=True)
    display_name = Column(String(255), nullable=False)
    given_name = Column(String(255))
    family_name = Column(String(255))
    email = Column(String(255))
    civic_no = Column(String(255), unique=True)
    edu_person_principal_name = Column(String(255))
    external_identifier_value = Column(String(255))
    external_identifier_context = Column(String(255))
    securityMarking = Column(String(50), nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    placements_child = relationship("Placement", foreign_keys="Placement.child_id", back_populates="child")
    placements_owner = relationship("Placement", foreign_keys="Placement.owner_id", back_populates="owner")
    duties = relationship("Duty", back_populates="person")
    group_memberships = relationship("GroupMembership", back_populates="person")
    responsible_for_children = relationship("ResponsibleFor", foreign_keys="ResponsibleFor.responsible_id", back_populates="responsible")
    responsible_for_enrolments = relationship("ResponsibleFor", foreign_keys="ResponsibleFor.responsible_id", back_populates="responsible") # Placeholder for now
    responsible_for_placements = relationship("ResponsibleFor", foreign_keys="ResponsibleFor.responsible_id", back_populates="responsible") # Placeholder for now
    
class Placement(Base):
    """Mappar mot tabellen 'placements'. Representerar en placering för en person."""
    __tablename__ = "placements"
    id = Column(String(36), primary_key=True)
    organisation_id = Column(String(36), ForeignKey('organisations.id'))
    group_id = Column(String(36), ForeignKey('groups.id'))
    person_id = Column(String(36), ForeignKey('persons.id'))  # Representerar 'child' i specen
    owner_id = Column(String(36), ForeignKey('persons.id'))
    start_date = Column(date)
    end_date = Column(date)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)
    
    placed_at = relationship("Organisation")
    group = relationship("Group")
    child = relationship("Person", foreign_keys=[person_id], primaryjoin="Placement.person_id == Person.id")
    owner = relationship("Person", foreign_keys=[owner_id], primaryjoin="Placement.owner_id == Person.id")

class PlacementOwner(Base):
    __tablename__ = "placement_owners"
    placement_id = Column(String(36), ForeignKey('placements.id'), primary_key=True)
    owner_id = Column(String(36), ForeignKey('persons.id'), primary_key=True)

class Duty(Base):
    __tablename__ = "duties"
    id = Column(String(36), primary_key=True)
    person_id = Column(String(36), ForeignKey('persons.id'))
    organisation_id = Column(String(36), ForeignKey('organisations.id'))
    duty_role = Column(String(255), nullable=False)
    start_date = Column(date)
    end_date = Column(date)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    person = relationship("Person", foreign_keys=[person_id])
    organisation = relationship("Organisation", foreign_keys=[organisation_id])

class Group(Base):
    __tablename__ = "groups"
    id = Column(String(36), primary_key=True)
    display_name = Column(String(255), nullable=False)
    group_type = Column(String(50), nullable=False)
    school_types = Column(String(255)) # Lagras som en komma-separerad sträng
    start_date = Column(date)
    end_date = Column(date)
    organisation_id = Column(String(36), ForeignKey('organisations.id'))
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organisation = relationship("Organisation", foreign_keys=[organisation_id])
    assignment_roles = relationship("AssignmentRole", back_populates="group")
    group_memberships = relationship("GroupMembership", back_populates="group")

class AssignmentRole(Base):
    __tablename__ = "assignment_roles"
    id = Column(String(36), primary_key=True)
    group_id = Column(String(36), ForeignKey('groups.id'))
    person_id = Column(String(36), ForeignKey('persons.id'))
    assignment_role = Column(String(255), nullable=False)
    start_date = Column(date)
    end_date = Column(date)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group = relationship("Group", back_populates="assignment_roles")
    person = relationship("Person", foreign_keys=[person_id])

class GroupMembership(Base):
    __tablename__ = "group_memberships"
    id = Column(String(36), primary_key=True)
    person_id = Column(String(36), ForeignKey('persons.id'))
    group_id = Column(String(36), ForeignKey('groups.id'))
    start_date = Column(date)
    end_date = Column(date)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    person = relationship("Person", back_populates="group_memberships")
    group = relationship("Group", back_populates="group_memberships")

class ResponsibleFor(Base):
    __tablename__ = "responsible_for"
    id = Column(String(36), primary_key=True)
    responsible_id = Column(String(36), ForeignKey('persons.id'))
    child_id = Column(String(36), ForeignKey('persons.id'))
    start_date = Column(date)
    end_date = Column(date)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)
    
    responsible = relationship("Person", foreign_keys=[responsible_id])
    child = relationship("Person", foreign_keys=[child_id])

class Programme(Base):
    __tablename__ = "programmes"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(255), nullable=False)
    parent_programme_id = Column(String(36), ForeignKey('programmes.id'))
    school_types = Column(String(255)) # Lagras som en komma-separerad sträng
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)

    # Relationships
    parent_programme = relationship("Programme", remote_side=[id])

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

class Enrolment(Base):
    __tablename__ = "enrolments"
    id = Column(String(36), primary_key=True)
    person_id = Column(String(36), ForeignKey('persons.id'))
    enroled_at_id = Column(String(36), ForeignKey('organisations.id'))
    start_date = Column(date)
    end_date = Column(date)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(DateTime, default=datetime.utcnow)
    
    person = relationship("Person")
    enroled_at = relationship("Organisation")

Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()