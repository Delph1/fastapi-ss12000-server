# schemas.py
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict


# Helper class for Pydantic
class Config:
    from_attributes = True

# --- Enums ---
class OrganisationTypeEnum(str, Enum):
    skola = "Skola"
    avdelning = "Avdelning"
    kommun = "Kommun"
    
class SchoolTypesEnum(str, Enum):
    grundskola = "Grundskola"
    gymnasium = "Gymnasium"

class PersonExpandEnum(str, Enum):
    duties = "duties"
    responsibleFor = "responsibleFor"
    placements = "placements"
    ownedPlacements = "ownedPlacements"
    groupMemberships = "groupMemberships"

class PersonRelationshipTypeEnum(str, Enum):
    enrolment = "enrolment"
    duty = "duty"
    placement_child = "placement.child"
    placement_owner = "placement.owner"
    responsibleFor_enrolment = "responsibleFor.enrolment"
    responsibleFor_placement = "responsibleFor.placement"
    groupMembership = "groupMembership"

class PlacementExpandEnum(str, Enum):
    child = "child"
    owners = "owners"

class DutyRoleEnum(str, Enum):
    teacher = "Teacher"
    principal = "Principal"
    student = "Student"
    staff = "Staff"

class DutyExpandEnum(str, Enum):
    person = "person"

class GroupTypesEnum(str, Enum):
    classGroup = "ClassGroup"
    teachingGroup = "TeachingGroup"

class GroupExpandEnum(str, Enum):
    assignmentRoles = "assignmentRoles"

class ProgrammeSortkeyEnum(str, Enum):
    NameAsc = "NameAsc"
    CodeAsc = "CodeAsc"
    ModifiedDesc = "ModifiedDesc"

# --- Lookup Request Schema ---
class LookupRequest(BaseModel):
    ids: List[str]

# --- Base Schemas ---

class OrganisationBase(BaseModel):
    id: str
    name: str
    parent_id: Optional[str] = None
    school_unit_code: Optional[str] = None
    organisation_code: Optional[str] = None
    municipality_code: Optional[str] = None
    type: Optional[OrganisationTypeEnum] = None
    school_types: Optional[List[SchoolTypesEnum]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created: datetime
    modified: datetime

    # Konfigurera hur Pydantic hanterar ORM-objekt
    class Config:
        orm_mode = True
        
    @classmethod
    def from_orm(cls, obj):
        # Override från_orm för att hantera 'school_types' som en lista
        data = obj.__dict__.copy()
        if data.get('school_types'):
            data['school_types'] = [SchoolTypesEnum(t) for t in data['school_types'].split(',')]
        return cls(**data)

class OrganisationExpanded(OrganisationBase):
    parent_name: Optional[str] = None

class PersonBase(BaseModel):
    id: str
    display_name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None
    civic_no: Optional[str] = None
    edu_person_principal_name: Optional[str] = None
    external_identifier_value: Optional[str] = None
    external_identifier_context: Optional[str] = None
    securityMarking: str
    created: datetime
    modified: datetime

    class Config:
        orm_mode = True

class Person(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    securityMarking: str
    created: datetime
    modified: datetime

    class Config:
        orm_mode = True

class DutySchema(BaseModel):
    id: str
    person_id: str
    duty_at_id: str
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created: datetime
    modified: datetime
    
    # För att hantera expandReferenceNames
    person_name: Optional[str] = None
    duty_at_name: Optional[str] = None

    class Config:
        orm_mode = True

class Duty(BaseModel):
    id: str
    name: str

class DutyBase(BaseModel):
    id: str
    person_id: str
    organisation_id: str
    duty_role: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PlacementBase(BaseModel):
    id: str
    organisation_id: str
    group_id: Optional[str] = None
    person_id: str
    owner_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)

class PlacementSchema(BaseModel):
    id: str
    placed_at_id: str
    child_id: str
    owner_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created: datetime
    modified: datetime
    
    # För att hantera expandReferenceNames
    placed_at_name: Optional[str] = None
    child_name: Optional[str] = None
    owner_name: Optional[str] = None
    
    class Config:
        orm_mode = True

class Placements(BaseModel):
    __root__: List[PlacementSchema]

class GroupMembershipSchema(BaseModel):
    id: str
    person_id: str
    group_id: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created: datetime
    modified: datetime
    
    # För att hantera expandReferenceNames
    person_name: Optional[str] = None
    group_name: Optional[str] = None

    class Config:
        orm_mode = True

class EnrolmentSchema(BaseModel):
    id: str
    person_id: str
    enroled_at_id: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created: datetime
    modified: datetime
    
    # För att hantera expandReferenceNames
    person_name: Optional[str] = None
    enroled_at_name: Optional[str] = None
    
    class Config:
        orm_mode = True
        
class ResponsibleForSchema(BaseModel):
    id: str
    responsible_id: str
    child_id: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created: datetime
    modified: datetime
    
    # För att hantera expandReferenceNames
    responsible_name: Optional[str] = None
    child_name: Optional[str] = None
    
    class Config:
        orm_mode = True

class Group(BaseModel):
    id: str
    name: str

class Programme(BaseModel):
    id: str
    name: str
    code: str
    parent_programme_id: Optional[str] = None
    school_types: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class ProgrammesArray(BaseModel):
    __root__: List[Programme]

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

class LogSchema(BaseModel):
    id: str
    log_message: str
    timestamp: datetime
    created: datetime
    modified: datetime
    
    model_config = ConfigDict(from_attributes=True)

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

# --- Reference Schemas ---

class OrganisationReference(BaseModel):
    id: str
    displayName: Optional[str] = None

class PersonReference(BaseModel):
    id: str
    displayName: Optional[str] = None
    securityMarking: Optional[str] = None

class PlacementReference(BaseModel):
    id: str
    displayName: Optional[str] = None
    organisationId: Optional[str] = None
    personId: Optional[str] = None

class GroupMembershipReference(BaseModel):
    id: str
    displayName: Optional[str] = None
    groupId: Optional[str] = None
    personId: Optional[str] = None

class DutyReference(BaseModel):
    id: str
    displayName: Optional[str] = None
    
class GroupReference(BaseModel):
    id: str
    displayName: Optional[str] = None

# --- Schemas for Request/Response Bodies ---
class SubscriptionCreate(BaseModel):
    resource_type: str
    resource_id: str
    user_id: str

class SubscriptionUpdate(BaseModel):
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    user_id: Optional[str] = None

# --- Expanded Schemas ---

class PersonExpanded(PersonBase):
    duties: Optional[List[DutySchema]] = None
    placements: Optional[List[PlacementSchema]] = None
    owned_placements: Optional[List[PlacementSchema]] = None
    group_memberships: Optional[List[GroupMembershipSchema]] = None
    responsible_for: Optional[List[ResponsibleForSchema]] = None

class PersonsExpandedArray(BaseModel):
    __root__: List["PersonExpanded"]

class PersonExpanded(Person):
    duties: Optional[List[DutyReference]] = None
    placements: Optional[List[PlacementReference]] = None
    groupMemberships: Optional[List[GroupMembershipReference]] = None

    class Config:
        orm_mode = True



class PlacementExpandedArray(BaseModel):
    __root__: List["PlacementExpanded"]

class DutyExpanded(DutyBase):
    person: Optional[PersonBase] = None
    
    model_config = ConfigDict(from_attributes=True)

class DutiesArray(BaseModel):
    __root__: List["DutyExpanded"]

class AssignmentRoleBase(BaseModel):
    id: str
    group_id: Optional[str] = None
    person_id: Optional[str] = None
    assignment_role: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None

class AssignmentRoleSchema(AssignmentRoleBase):
    model_config = ConfigDict(from_attributes=True)

class AssignmentRoleExpanded(AssignmentRoleBase):
    person: Optional[Person] = None
    
    model_config = ConfigDict(from_attributes=True)

class GroupBase(BaseModel):
    id: str
    display_name: str
    group_type: GroupTypesEnum
    school_types: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    organisation_id: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None

class GroupSchema(GroupBase):
    model_config = ConfigDict(from_attributes=True)

class GroupsExpanded(BaseModel):
    __root__: List[GroupSchema]

class GroupExpanded(GroupBase):
    assignment_roles: Optional[List[AssignmentRoleExpanded]] = None
    
    model_config = ConfigDict(from_attributes=True)

    
class PlacementExpanded(PlacementBase):
    child: Optional[PersonBase] = None
    owner: Optional[PersonBase] = None
    placed_at: Optional[OrganisationBase] = None
    group: Optional[GroupBase] = None

    model_config = ConfigDict(from_attributes=True)