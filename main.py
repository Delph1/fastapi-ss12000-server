# main.py
import uuid
from datetime import datetime
from typing import List, Optional, Union

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc

from database import (
    get_db, Organisation, Person, Placement, Duty, Group, Programme, StudyPlan, Syllabus,
    SchoolUnitOffering, Activity, CalendarEvent, Attendance, AttendanceEvent,
    AttendanceSchedule, Grade, AggregatedAttendance, Resource, Room, Subscription,
    DeletedEntity, Log
)

from schemas import (
    OrganisationWithPlacements, OrganisationBase, PersonWithRelations, PersonBase,
    PlacementWithRelations, PlacementBase, Duty, Group, Programme, StudyPlan, Syllabus,
    SchoolUnitOffering, ActivityWithRelations, CalendarEventWithActivity,
    AttendanceWithRelations, AttendanceEventBase, AttendanceSchedule, GradeWithPerson,
    AggregatedAttendanceWithPerson, Resource, Room, SubscriptionBase,
    SubscriptionCreate, SubscriptionUpdate, DeletedEntity, Log, LookupRequest
)


# --- FastAPI-applikation ---
app = FastAPI(title="SS12000 Mock API med MySQL")

# Hjälpfunktion för dynamisk sortering
def apply_sorting(query, model, sortkey: Optional[str]):
    """Applicerar sortering på en SQLAlchemy-fråga baserat på sortkey-parametern."""
    if not sortkey:
        return query

    sort_mapping = {
        "ModifiedDesc": (model.modified, desc),
        "ModifiedAsc": (model.modified, asc),
        "CreatedDesc": (model.created, desc),
        "CreatedAsc": (model.created, asc),
    }

    column, sort_order = sort_mapping.get(sortkey, (None, None))
    if column and sort_order:
        return query.order_by(sort_order(column))
    else:
        return query

# Hjälpfunktion för att applicera meta-filter
def apply_meta_filters(query, model, metaCreatedBefore: Optional[datetime], metaCreatedAfter: Optional[datetime], metaModifiedBefore: Optional[datetime], metaModifiedAfter: Optional[datetime]):
    """Applicerar meta-filter på en SQLAlchemy-fråga."""
    if metaCreatedBefore:
        query = query.filter(model.created < metaCreatedBefore)
    if metaCreatedAfter:
        query = query.filter(model.created > metaCreatedAfter)
    if metaModifiedBefore:
        query = query.filter(model.modified < metaModifiedBefore)
    if metaModifiedAfter:
        query = query.filter(model.modified > metaModifiedAfter)
    return query


# --- API-slutpunkter ---
@app.get("/organisations", response_model=List[OrganisationWithPlacements])
def get_organisations(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0,
):
    query = db.query(Organisation).options(joinedload(Organisation.placements))
    query = apply_meta_filters(query, Organisation, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Organisation, sortkey)
    return query.offset(offset).limit(limit).all()

@app.get("/organisations/{organisation_id}", response_model=OrganisationWithPlacements)
def get_organisation(organisation_id: str, db: Session = Depends(get_db)):
    """Hämta en specifik organisation, inklusive dess placeringar."""
    organisation = db.query(Organisation).options(joinedload(Organisation.placements)).filter(Organisation.id == organisation_id).first()
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return organisation

@app.post("/organisations/lookup", response_model=List[OrganisationWithPlacements])
def lookup_organisations(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med organisationer baserat på en lista med ID:n."""
    organisations = db.query(Organisation).options(joinedload(Organisation.placements)).filter(Organisation.id.in_(lookup_data.ids)).all()
    return organisations


@app.get("/persons", response_model=List[PersonWithRelations])
def get_persons(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0,
):
    query = db.query(Person).options(
        joinedload(Person.placements),
        joinedload(Person.attendance),
        joinedload(Person.grades),
        joinedload(Person.aggregated_attendance)
    )
    query = apply_meta_filters(query, Person, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Person, sortkey)
    return query.offset(offset).limit(limit).all()


@app.get("/persons/{person_id}", response_model=PersonWithRelations)
def get_person(person_id: str, db: Session = Depends(get_db)):
    """
    Hämta en specifik person, inklusive alla dess relaterade objekt
    (placeringar, närvaror, betyg och aggregerad närvaro).
    """
    person = db.query(Person).options(
        joinedload(Person.placements),
        joinedload(Person.attendance).joinedload(Attendance.activity),
        joinedload(Person.attendance).joinedload(Attendance.attendance_event),
        joinedload(Person.grades),
        joinedload(Person.aggregated_attendance)
    ).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

@app.post("/persons/lookup", response_model=List[PersonWithRelations])
def lookup_persons(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med personer baserat på en lista med ID:n."""
    persons = db.query(Person).options(
        joinedload(Person.placements),
        joinedload(Person.attendance).joinedload(Attendance.activity),
        joinedload(Person.attendance).joinedload(Attendance.attendance_event),
        joinedload(Person.grades),
        joinedload(Person.aggregated_attendance)
    ).filter(Person.id.in_(lookup_data.ids)).all()
    return persons


@app.get("/placements", response_model=List[PlacementWithRelations])
def list_placements(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    """Listar placeringar med detaljer om organisation och person."""
    query = db.query(Placement).options(joinedload(Placement.organisation), joinedload(Placement.person))
    query = apply_meta_filters(query, Placement, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Placement, sortkey)
    return query.offset(offset).limit(limit).all()

@app.get("/placements/{placement_id}", response_model=PlacementWithRelations)
def get_placement(placement_id: str, db: Session = Depends(get_db)):
    placement = db.query(Placement).options(joinedload(Placement.organisation), joinedload(Placement.person)).filter(Placement.id == placement_id).first()
    if not placement:
        raise HTTPException(status_code=404, detail="Placement not found")
    return placement

@app.post("/placements/lookup", response_model=List[PlacementWithRelations])
def lookup_placements(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med placeringar baserat på en lista med ID:n."""
    placements = db.query(Placement).options(joinedload(Placement.organisation), joinedload(Placement.person)).filter(Placement.id.in_(lookup_data.ids)).all()
    return placements


@app.get("/duties", response_model=List[Duty])
def get_duties(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    query = db.query(Duty)
    query = apply_meta_filters(query, Duty, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Duty, sortkey)
    return query.offset(offset).limit(limit).all()

@app.post("/duties/lookup", response_model=List[Duty])
def lookup_duties(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med uppdrag baserat på en lista med ID:n."""
    duties = db.query(Duty).filter(Duty.id.in_(lookup_data.ids)).all()
    return duties

@app.get("/groups", response_model=List[Group])
def get_groups(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    query = db.query(Group)
    query = apply_meta_filters(query, Group, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Group, sortkey)
    return query.offset(offset).limit(limit).all()

@app.post("/groups/lookup", response_model=List[Group])
def lookup_groups(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med grupper baserat på en lista med ID:n."""
    groups = db.query(Group).filter(Group.id.in_(lookup_data.ids)).all()
    return groups

@app.get("/programmes", response_model=List[Programme])
def get_programmes(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    query = db.query(Programme)
    query = apply_meta_filters(query, Programme, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Programme, sortkey)
    return query.offset(offset).limit(limit).all()

@app.post("/programmes/lookup", response_model=List[Programme])
def lookup_programmes(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med program baserat på en lista med ID:n."""
    programmes = db.query(Programme).filter(Programme.id.in_(lookup_data.ids)).all()
    return programmes

@app.get("/studyPlans", response_model=List[StudyPlan])
def get_study_plans(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    query = db.query(StudyPlan)
    query = apply_meta_filters(query, StudyPlan, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, StudyPlan, sortkey)
    return query.offset(offset).limit(limit).all()

@app.post("/studyPlans/lookup", response_model=List[StudyPlan])
def lookup_study_plans(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med studieplaner baserat på en lista med ID:n."""
    study_plans = db.query(StudyPlan).filter(StudyPlan.id.in_(lookup_data.ids)).all()
    return study_plans

@app.get("/syllabuses", response_model=List[Syllabus])
def get_syllabuses(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    query = db.query(Syllabus)
    query = apply_meta_filters(query, Syllabus, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Syllabus, sortkey)
    return query.offset(offset).limit(limit).all()

@app.post("/syllabuses/lookup", response_model=List[Syllabus])
def lookup_syllabuses(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med kursplaner baserat på en lista med ID:n."""
    syllabuses = db.query(Syllabus).filter(Syllabus.id.in_(lookup_data.ids)).all()
    return syllabuses

@app.get("/schoolUnitOfferings", response_model=List[SchoolUnitOffering])
def get_school_unit_offerings(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    query = db.query(SchoolUnitOffering)
    query = apply_meta_filters(query, SchoolUnitOffering, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, SchoolUnitOffering, sortkey)
    return query.offset(offset).limit(limit).all()

@app.post("/schoolUnitOfferings/lookup", response_model=List[SchoolUnitOffering])
def lookup_school_unit_offerings(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med skolenhetsutbud baserat på en lista med ID:n."""
    school_unit_offerings = db.query(SchoolUnitOffering).filter(SchoolUnitOffering.id.in_(lookup_data.ids)).all()
    return school_unit_offerings

@app.get("/activities", response_model=List[ActivityWithRelations])
def get_activities(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    """Hämtar en lista över aktiviteter med tillhörande kalenderhändelser och närvaroposter."""
    query = db.query(Activity).options(
        joinedload(Activity.calendar_events),
        joinedload(Activity.attendance_records)
    )
    query = apply_meta_filters(query, Activity, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Activity, sortkey)
    return query.offset(offset).limit(limit).all()

@app.get("/activities/{activity_id}", response_model=ActivityWithRelations)
def get_activity(activity_id: str, db: Session = Depends(get_db)):
    """Hämtar en specifik aktivitet med tillhörande kalenderhändelser och närvaroposter."""
    activity = db.query(Activity).options(
        joinedload(Activity.calendar_events),
        joinedload(Activity.attendance_records)
    ).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

@app.post("/activities/lookup", response_model=List[ActivityWithRelations])
def lookup_activities(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med aktiviteter baserat på en lista med ID:n."""
    activities = db.query(Activity).options(
        joinedload(Activity.calendar_events),
        joinedload(Activity.attendance_records)
    ).filter(Activity.id.in_(lookup_data.ids)).all()
    return activities

@app.get("/calendarEvents", response_model=List[CalendarEventWithActivity])
def get_calendar_events(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    """Hämtar en lista över kalenderhändelser med tillhörande aktivitet."""
    query = db.query(CalendarEvent).options(joinedload(CalendarEvent.activity))
    query = apply_meta_filters(query, CalendarEvent, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, CalendarEvent, sortkey)
    return query.offset(offset).limit(limit).all()

@app.get("/calendarEvents/{calendar_event_id}", response_model=CalendarEventWithActivity)
def get_calendar_event(calendar_event_id: str, db: Session = Depends(get_db)):
    """Hämtar en specifik kalenderhändelse med tillhörande aktivitet."""
    calendar_event = db.query(CalendarEvent).options(joinedload(CalendarEvent.activity)).filter(CalendarEvent.id == calendar_event_id).first()
    if not calendar_event:
        raise HTTPException(status_code=404, detail="Calendar Event not found")
    return calendar_event

@app.post("/calendarEvents/lookup", response_model=List[CalendarEventWithActivity])
def lookup_calendar_events(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med kalenderhändelser baserat på en lista med ID:n."""
    calendar_events = db.query(CalendarEvent).options(joinedload(CalendarEvent.activity)).filter(CalendarEvent.id.in_(lookup_data.ids)).all()
    return calendar_events

@app.get("/attendance", response_model=List[AttendanceWithRelations])
def get_attendance_records(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    """Hämtar en lista över närvaroposter med relaterade person, aktivitet och närvarohändelse."""
    query = db.query(Attendance).options(
        joinedload(Attendance.person),
        joinedload(Attendance.activity),
        joinedload(Attendance.attendance_event)
    )
    query = apply_meta_filters(query, Attendance, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Attendance, sortkey)
    return query.offset(offset).limit(limit).all()

@app.get("/attendance/{attendance_id}", response_model=AttendanceWithRelations)
def get_attendance_record(attendance_id: str, db: Session = Depends(get_db)):
    """Hämtar en specifik närvaropost med relaterade person, aktivitet och närvarohändelse."""
    attendance_record = db.query(Attendance).options(
        joinedload(Attendance.person),
        joinedload(Attendance.activity),
        joinedload(Attendance.attendance_event)
    ).filter(Attendance.id == attendance_id).first()
    if not attendance_record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return attendance_record

@app.post("/attendance/lookup", response_model=List[AttendanceWithRelations])
def lookup_attendance(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med närvaroposter baserat på en lista med ID:n."""
    attendance_records = db.query(Attendance).options(
        joinedload(Attendance.person),
        joinedload(Attendance.activity),
        joinedload(Attendance.attendance_event)
    ).filter(Attendance.id.in_(lookup_data.ids)).all()
    return attendance_records

@app.get("/attendanceEvents", response_model=List[AttendanceEventBase])
def get_attendance_events(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    query = db.query(AttendanceEvent)
    query = apply_meta_filters(query, AttendanceEvent, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, AttendanceEvent, sortkey)
    return query.offset(offset).limit(limit).all()

@app.post("/attendanceEvents/lookup", response_model=List[AttendanceEventBase])
def lookup_attendance_events(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med närvarohändelser baserat på en lista med ID:n."""
    attendance_events = db.query(AttendanceEvent).filter(AttendanceEvent.id.in_(lookup_data.ids)).all()
    return attendance_events

@app.get("/attendanceSchedules", response_model=List[AttendanceSchedule])
def get_attendance_schedules(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    query = db.query(AttendanceSchedule)
    query = apply_meta_filters(query, AttendanceSchedule, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, AttendanceSchedule, sortkey)
    return query.offset(offset).limit(limit).all()

@app.post("/attendanceSchedules/lookup", response_model=List[AttendanceSchedule])
def lookup_attendance_schedules(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med närvaroscheman baserat på en lista med ID:n."""
    attendance_schedules = db.query(AttendanceSchedule).filter(AttendanceSchedule.id.in_(lookup_data.ids)).all()
    return attendance_schedules

@app.get("/grades", response_model=List[GradeWithPerson])
def get_grades(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    """Hämtar en lista över betyg med relaterad person."""
    query = db.query(Grade).options(joinedload(Grade.person))
    query = apply_meta_filters(query, Grade, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Grade, sortkey)
    return query.offset(offset).limit(limit).all()

@app.get("/grades/{grade_id}", response_model=List[GradeWithPerson])
def get_grade(grade_id: str, db: Session = Depends(get_db)):
    """Hämtar ett specifikt betyg med relaterad person."""
    grade = db.query(Grade).options(joinedload(Grade.person)).filter(Grade.id == grade_id).all()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    return grade

@app.post("/grades/lookup", response_model=List[GradeWithPerson])
def lookup_grades(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med betyg baserat på en lista med ID:n."""
    grades = db.query(Grade).options(joinedload(Grade.person)).filter(Grade.id.in_(lookup_data.ids)).all()
    return grades


@app.get("/aggregatedAttendance", response_model=List[AggregatedAttendanceWithPerson])
def get_aggregated_attendance(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    """Hämtar en lista över aggregerade närvaroposter med relaterad person."""
    query = db.query(AggregatedAttendance).options(joinedload(AggregatedAttendance.person))
    query = apply_meta_filters(query, AggregatedAttendance, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, AggregatedAttendance, sortkey)
    return query.offset(offset).limit(limit).all()

@app.get("/aggregatedAttendance/{aggregated_attendance_id}", response_model=AggregatedAttendanceWithPerson)
def get_aggregated_attendance_record(aggregated_attendance_id: str, db: Session = Depends(get_db)):
    """Hämta en specifik aggregerad närvaropost med relaterad person."""
    aggregated_attendance_record = db.query(AggregatedAttendance).options(joinedload(AggregatedAttendance.person)).filter(AggregatedAttendance.id == aggregated_attendance_id).first()
    if not aggregated_attendance_record:
        raise HTTPException(status_code=404, detail="Aggregated attendance record not found")
    return aggregated_attendance_record

@app.post("/aggregatedAttendance/lookup", response_model=List[AggregatedAttendanceWithPerson])
def lookup_aggregated_attendance(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med aggregerade närvaroposter baserat på en lista med ID:n."""
    aggregated_attendance_records = db.query(AggregatedAttendance).options(joinedload(AggregatedAttendance.person)).filter(AggregatedAttendance.id.in_(lookup_data.ids)).all()
    return aggregated_attendance_records

@app.get("/resources", response_model=List[Resource])
def get_resources(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    query = db.query(Resource)
    query = apply_meta_filters(query, Resource, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Resource, sortkey)
    return query.offset(offset).limit(limit).all()

@app.post("/resources/lookup", response_model=List[Resource])
def lookup_resources(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med resurser baserat på en lista med ID:n."""
    resources = db.query(Resource).filter(Resource.id.in_(lookup_data.ids)).all()
    return resources

@app.get("/rooms", response_model=List[Room])
def get_rooms(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    query = db.query(Room)
    query = apply_meta_filters(query, Room, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Room, sortkey)
    return query.offset(offset).limit(limit).all()

@app.post("/rooms/lookup", response_model=List[Room])
def lookup_rooms(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med rum baserat på en lista med ID:n."""
    rooms = db.query(Room).filter(Room.id.in_(lookup_data.ids)).all()
    return rooms

@app.get("/subscriptions", response_model=List[SubscriptionBase])
def get_subscriptions(db: Session = Depends(get_db)):
    return db.query(Subscription).all()

@app.post("/subscriptions", response_model=SubscriptionCreate)
def create_subscription(subscription: SubscriptionCreate, db: Session = Depends(get_db)):
    db_subscription = Subscription(**subscription.model_dump(), id=str(uuid.uuid4()))
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

@app.patch("/subscriptions/{subscription_id}", response_model=SubscriptionBase)
def update_subscription(subscription_id: str, subscription_update: SubscriptionUpdate, db: Session = Depends(get_db)):
    db_subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not db_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    update_data = subscription_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_subscription, key, value)

    db.commit()
    db.refresh(db_subscription)
    return db_subscription

@app.delete("/subscriptions/{subscription_id}")
def delete_subscription(subscription_id: str, db: Session = Depends(get_db)):
    db_subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not db_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(db_subscription)
    db.commit()
    return {"message": "Subscription deleted successfully"}

@app.get("/deletedEntities", response_model=List[DeletedEntity])
def get_deleted_entities(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0
):
    query = db.query(DeletedEntity)
    query = apply_meta_filters(query, DeletedEntity, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, DeletedEntity, sortkey)
    return query.offset(offset).limit(limit).all()

@app.post("/deletedEntities/lookup", response_model=List[DeletedEntity])
def lookup_deleted_entities(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med borttagna entiteter baserat på en lista med ID:n."""
    deleted_entities = db.query(DeletedEntity).filter(DeletedEntity.id.in_(lookup_data.ids)).all()
    return deleted_entities

@app.get("/log", response_model=List[Log])
def get_logs(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0,
):
    query = db.query(Log)
    query = apply_meta_filters(query, Log, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Log, sortkey)
    return query.offset(offset).limit(limit).all()

@app.post("/log/lookup", response_model=List[Log])
def lookup_logs(lookup_data: LookupRequest, db: Session = Depends(get_db)):
    """Hämta en lista med loggar baserat på en lista med ID:n."""
    logs = db.query(Log).filter(Log.id.in_(lookup_data.ids)).all()
    return logs

@app.get("/statistics")
def get_statistics(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returns expanded reference names in the response."),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0,
    pageToken: Optional[str] = Query(None, description="An opaque value that the server has returned to a previous query.")
):
    return {"message": "This is a placeholder for statistics with meta-params."}
