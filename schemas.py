# schemas.py
from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict


# Helper class for Pydantic
class Config:
    from_attributes = True

# --- Lookup Request Schema ---
class LookupRequest(BaseModel):
    ids: List[str]

# --- Base Schemas ---
class OrganisationBase(BaseModel):
    id: str
    name: str

class PersonBase(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    securityMarking: str

class PlacementBase(BaseModel):
    id: str
    organisation_id: str
    person_id: str

class Duty(BaseModel):
    id: str
    name: str

class Group(BaseModel):
    id: str
    name: str

class Programme(BaseModel):
    id: str
    name: str

class StudyPlan(BaseModel):
    id: str
    name: str

class Syllabus(BaseModel):
    id: str
    name: str

class SchoolUnitOffering(BaseModel):
    id: str
    name: str

class CalendarEventBase(BaseModel):
    id: str
    name: str
    activity_id: str

class AttendanceEventBase(BaseModel):
    id: str
    name: str

class AttendanceBase(BaseModel):
    id: str
    person_id: str
    activity_id: str
    attendance_event_id: str
    timestamp: datetime

class AttendanceSchedule(BaseModel):
    id: str
    name: str

class GradeBase(BaseModel):
    id: str
    person_id: str
    grade_value: str

class AggregatedAttendanceBase(BaseModel):
    id: str
    person_id: str
    attendance_percentage: float

class Resource(BaseModel):
    id: str
    name: str

class Room(BaseModel):
    id: str
    name: str

class SubscriptionBase(BaseModel):
    id: str
    resource_type: str
    resource_id: str
    user_id: str

class DeletedEntity(BaseModel):
    id: str
    resource_type: str
    deleted_at: datetime

class Log(BaseModel):
    id: str
    log_message: str
    timestamp: datetime


# --- Schemas with Relations ---
class OrganisationWithPlacements(OrganisationBase):
    placements: List[PlacementBase] = []

class PersonWithRelations(PersonBase):
    placements: List[PlacementBase] = []
    attendance: List[AttendanceBase] = []
    grades: List[GradeBase] = []
    aggregated_attendance: List[AggregatedAttendanceBase] = []

class PlacementWithRelations(PlacementBase):
    organisation: OrganisationBase
    person: PersonBase

class ActivityWithRelations(BaseModel):
    id: str
    name: str
    calendar_events: List[CalendarEventBase] = []
    attendance_records: List[AttendanceBase] = []

class CalendarEventWithActivity(CalendarEventBase):
    activity: ActivityWithRelations

class AttendanceWithRelations(AttendanceBase):
    person: PersonBase
    activity: ActivityWithRelations
    attendance_event: AttendanceEventBase

class GradeWithPerson(GradeBase):
    person: PersonBase

class AggregatedAttendanceWithPerson(AggregatedAttendanceBase):
    person: PersonBase


# --- Schemas for Request/Response Bodies ---
class SubscriptionCreate(BaseModel):
    resource_type: str
    resource_id: str
    user_id: str

class SubscriptionUpdate(BaseModel):
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    user_id: Optional[str] = None
