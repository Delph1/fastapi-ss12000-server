# main.py
import uuid
from datetime import datetime
from typing import List, Optional, Union

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, func, or_

from database import *
from schemas import *

# Expand helper functions
from helpers import *

# --- FastAPI-applikation ---
app = FastAPI(title="SS12000 Mock API med MySQL")


# --- API Endpoints ---
# --- Organisations endpoints below ---
@app.get("/organisations", response_model=List[OrganisationBase], summary="Hämta en lista med organisationer.")
def get_organisations(
    db: Session = Depends(get_db),
    parent: Optional[List[str]] = Query(None, description="Begränsa urvalet till utpekade organisations-ID:n."),
    schoolUnitCode: Optional[List[str]] = Query(None, alias="schoolUnitCode", description="Begränsa urvalet till de skolenheter som har den angivna Skolenhetskoden."),
    organisationCode: Optional[List[str]] = Query(None, alias="organisationCode", description="Begränsa urvalet till de organisationselement som har den angivna koden."),
    municipalityCode: Optional[str] = Query(None, alias="municipalityCode", description="Begränsa urvalet till de organisationselement som har angiven kommunkod."),
    type: Optional[List[OrganisationTypeEnum]] = Query(None, description="Begränsa urvalet till utpekade typ."),
    schoolTypes: Optional[List[SchoolTypesEnum]] = Query(None, alias="schoolTypes", description="Begränsa urvalet till de organisationselement som har den angivna skolformen."),
    startDate_onOrBefore: Optional[date] = Query(None, alias="startDate.onOrBefore", description="Begränsa urvalet till organisationselement som har ett startDate värde innan eller på det angivna datumet."),
    startDate_onOrAfter: Optional[date] = Query(None, alias="startDate.onOrAfter", description="Begränsa urvalet till organisationselement som har ett startDate värde på eller efter det angivna datumet."),
    endDate_onOrBefore: Optional[date] = Query(None, alias="endDate.onOrBefore", description="Begränsa urvalet till organisationselement som har ett endDate värde innan eller på det angivna datumet."),
    endDate_onOrAfter: Optional[date] = Query(None, alias="endDate.onOrAfter", description="Begränsa urvalet till organisationselement som har ett endDate värde på eller efter det angivna datumet."),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="meta.created.before"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="meta.created.after"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="meta.modified.before"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="meta.modified.after"),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returnera `displayName` för alla refererade objekt."),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "DisplayNameAsc".'),
    limit: int = 100,
    offset: int = 0,
    pageToken: Optional[str] = Query(None, description="Ett opakt värde som servern givit som svar på en tidigare ställd fråga.")
):
    """
    Hämta en lista med organisationer med stöd för filtrering, sortering och paginering.
    """
    # Hantera pageToken som inte kan kombineras med andra filter
    if pageToken and (parent or schoolUnitCode or organisationCode or municipalityCode or type or schoolTypes or startDate_onOrBefore or startDate_onOrAfter or endDate_onOrBefore or endDate_onOrAfter or metaCreatedBefore or metaCreatedAfter or metaModifiedBefore or metaModifiedAfter or sortkey):
        raise HTTPException(
            status_code=400,
            detail="Filter can not be combined with pageToken."
        )

    # Bygg upp SQLAlchemy-frågan
    query = db.query(Organisation)

    # Applicera filter
    if parent:
        query = query.filter(Organisation.parent_id.in_(parent))
    if schoolUnitCode:
        query = query.filter(Organisation.school_unit_code.in_(schoolUnitCode))
    if organisationCode:
        query = query.filter(Organisation.organisation_code.in_(organisationCode))
    if municipalityCode:
        query = query.filter(Organisation.municipality_code == municipalityCode)
    if type:
        query = query.filter(Organisation.type.in_([t.value for t in type]))
    if schoolTypes:
        # Denna filtrering antar att school_types lagras som en komma-separerad sträng
        for st in schoolTypes:
            query = query.filter(Organisation.school_types.like(f"%{st.value}%"))
            
    if startDate_onOrBefore:
        query = query.filter(Organisation.start_date <= startDate_onOrBefore)
    if startDate_onOrAfter:
        query = query.filter(Organisation.start_date >= startDate_onOrAfter)
        
    if endDate_onOrBefore:
        query = query.filter(Organisation.end_date <= endDate_onOrBefore)
    if endDate_onOrAfter:
        # Inkludera poster med null endDate
        query = query.filter(
            (Organisation.end_date >= endDate_onOrAfter) | (Organisation.end_date.is_(None))
        )

    # Applicera meta-parametrar
    query = apply_meta_filters(query, Organisation, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    
    # Applicera sortering
    query = apply_sorting(query, Organisation, sortkey)
    
    # Applicera paginering
    organisations = query.offset(offset).limit(limit).all()

    if expandReferenceNames:
        return expand_organisations(organisations, db)
    else:
        # Konvertera Pydantic modellen med rätt hantering av `school_types`
        return [OrganisationExpanded.from_orm(org) for org in organisations]

@app.get("/organisations/{id}", response_model=OrganisationBase, summary="Hämta en organisation baserat på ID.")
def get_organisation_by_id(
    id: str,
    db: Session = Depends(get_db),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returnera `displayName` för alla refererade objekt.")
):
    """
    Hämtar en enskild organisation baserat på dess ID.
    Returnerar en 404-fel om organisationen inte hittas.
    """
    organisation = db.query(Organisation).filter(Organisation.id == id).first()
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    if expandReferenceNames:
        # Om expandReferenceNames är true, expandera organisationen
        return expand_organisations([organisation], db)[0]
    else:
        return OrganisationExpanded.from_orm(organisation)

@app.post("/organisations/lookup", response_model=List[OrganisationBase], summary="Hämta många organisationer baserat på en lista av ID:n.")
def lookup_organisations(
    request_body: LookupRequest,
    db: Session = Depends(get_db),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returnera `displayName` för alla refererade objekt.")
):
    """
    Hämtar en lista med organisationer baserat på en lista av ID:n som skickas i request body.
    """
    # Hämta en lista med organisationer vars ID finns i request_body.organisations
    organisations = db.query(Organisation).filter(Organisation.id.in_(request_body.organisations)).all()
    
    if expandReferenceNames:
        return expand_organisations(organisations, db)
    else:
        # Konvertera Pydantic modellen med rätt hantering av `school_types`
        return [OrganisationExpanded.from_orm(org) for org in organisations]

# --- Persons endpoints below ---
@app.get("/persons", response_model=List[PersonExpanded], summary="Hämta en lista med personer.", tags=["Person"])
def get_persons(
    db: Session = Depends(get_db),
    nameContains: Optional[List[str]] = Query(None, description="Begränsa urvalet till de personer vars namn innehåller något av parameterns värden."),
    civicNo: Optional[str] = Query(None, description="Begränsa urvalet till den person vars civicNo matchar parameterns värde."),
    eduPersonPrincipalName: Optional[str] = Query(None, alias="eduPersonPrincipalName", description="Begränsa urvalet till den person vars eduPersonPrincipalNames matchar parameterns värde."),
    identifier_value: Optional[str] = Query(None, alias="identifier.value", description="Begränsa urvalet till den person vilka har ett värde i `externalIdentifiers.value` som matchar parameterns värde."),
    identifier_context: Optional[str] = Query(None, alias="identifier.context", description="Begränsa urvalet till den person vilka har ett värde i `externalIdentifiers.context` som matchar parameterns värde."),
    relationship_entity_type: Optional[PersonRelationshipTypeEnum] = Query(None, alias="relationship.entity.type", description="Begränsa urvalet till de personer som har en denna typ av relation till andra entititeter."),
    relationship_organisation: Optional[str] = Query(None, alias="relationship.organisation", description="Begränsa urvalet till de personer som har en relation till angivet organisationselement."),
    relationship_start_date_onOrBefore: Optional[date] = Query(None, alias="relationship.startDate.onOrBefore", description="Begränsa urvalet av personer till de som har relationer med startDate innan eller på det angivna datumet."),
    relationship_start_date_onOrAfter: Optional[date] = Query(None, alias="relationship.startDate.onOrAfter", description="Begränsa urvalet av personer till de som har relationer med startDate efter eller på det angivna datumet."),
    relationship_end_date_onOrBefore: Optional[date] = Query(None, alias="relationship.endDate.onOrBefore", description="Begränsa urvalet av personer till de som har relationer med endDate innan eller på det angivna datumet."),
    relationship_end_date_onOrAfter: Optional[date] = Query(None, alias="relationship.endDate.onOrAfter", description="Begränsa urvalet av personer till de som har relationer med endDate efter eller på det angivna datumet."),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="meta.created.before"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="meta.created.after"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="meta.modified.before"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="meta.modified.after"),
    expand: Optional[List[PersonExpandEnum]] = Query(None, description="Beskriver om expanderade data ska hämtas."),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returnera `displayName` för alla refererade objekt."),
    sortkey: Optional[str] = Query(None, description='Anger hur resultatet ska sorteras.'),
    limit: int = 100,
    offset: int = 0,
    pageToken: Optional[str] = Query(None, description="Ett opakt värde som servern givit som svar på en tidigare ställd fråga.")
):
    """
    Hämtar en lista med personer med stöd för avancerad filtrering, sortering och paginering.
    """
    if pageToken and (nameContains or civicNo or eduPersonPrincipalName or identifier_value or identifier_context or relationship_entity_type or relationship_organisation or relationship_start_date_onOrBefore or relationship_start_date_onOrAfter or relationship_end_date_onOrBefore or relationship_end_date_onOrAfter or metaCreatedBefore or metaCreatedAfter or metaModifiedBefore or metaModifiedAfter or expand or sortkey):
        raise HTTPException(
            status_code=400,
            detail="Filter can not be combined with pageToken."
        )

    query = db.query(Person)

    # Filtrering på namn
    if nameContains:
        # Skapar en and-klausul för alla namnfragment
        name_filters = [
            or_(
                func.lower(Person.display_name).contains(func.lower(name_part)),
                func.lower(Person.given_name).contains(func.lower(name_part)),
                func.lower(Person.family_name).contains(func.lower(name_part))
            ) for name_part in nameContains
        ]
        query = query.filter(*name_filters)

    # Exakt matchning
    if civicNo:
        query = query.filter(Person.civic_no == civicNo)
    if eduPersonPrincipalName:
        query = query.filter(Person.edu_person_principal_name == eduPersonPrincipalName)
    
    # Externa identifierare
    if identifier_value:
        query = query.filter(Person.external_identifier_value == identifier_value)
    if identifier_context:
        query = query.filter(Person.external_identifier_context == identifier_context)

    # Filtrering baserat på relationer
    if relationship_entity_type:
        if relationship_entity_type == PersonRelationshipTypeEnum.enrolment:
            query = query.join(Enrolment, Enrolment.person_id == Person.id)
            if relationship_organisation:
                query = query.filter(Enrolment.enroled_at_id == relationship_organisation)
            if relationship_start_date_onOrBefore:
                query = query.filter(Enrolment.start_date <= relationship_start_date_onOrBefore)
            if relationship_start_date_onOrAfter:
                query = query.filter(Enrolment.start_date >= relationship_start_date_onOrAfter)
            if relationship_end_date_onOrBefore:
                query = query.filter(Enrolment.end_date <= relationship_end_date_onOrBefore)
            if relationship_end_date_onOrAfter:
                query = query.filter(Enrolment.end_date >= relationship_end_date_onOrAfter)
                
        elif relationship_entity_type == PersonRelationshipTypeEnum.duty:
            query = query.join(Duty, Duty.person_id == Person.id)
            if relationship_organisation:
                query = query.filter(Duty.duty_at_id == relationship_organisation)
            if relationship_start_date_onOrBefore:
                query = query.filter(Duty.start_date <= relationship_start_date_onOrBefore)
            if relationship_start_date_onOrAfter:
                query = query.filter(Duty.start_date >= relationship_start_date_onOrAfter)
            if relationship_end_date_onOrBefore:
                query = query.filter(Duty.end_date <= relationship_end_date_onOrBefore)
            if relationship_end_date_onOrAfter:
                query = query.filter(Duty.end_date >= relationship_end_date_onOrAfter)

        elif relationship_entity_type == PersonRelationshipTypeEnum.placement_child:
            query = query.join(Placement, Placement.child_id == Person.id)
            if relationship_organisation:
                query = query.filter(Placement.placed_at_id == relationship_organisation)
            if relationship_start_date_onOrBefore:
                query = query.filter(Placement.start_date <= relationship_start_date_onOrBefore)
            if relationship_start_date_onOrAfter:
                query = query.filter(Placement.start_date >= relationship_start_date_onOrAfter)
            if relationship_end_date_onOrBefore:
                query = query.filter(Placement.end_date <= relationship_end_date_onOrBefore)
            if relationship_end_date_onOrAfter:
                query = query.filter(Placement.end_date >= relationship_end_date_onOrAfter)
                
        elif relationship_entity_type == PersonRelationshipTypeEnum.placement_owner:
            query = query.join(Placement, Placement.owner_id == Person.id)
            if relationship_organisation:
                query = query.filter(Placement.placed_at_id == relationship_organisation)
            if relationship_start_date_onOrBefore:
                query = query.filter(Placement.start_date <= relationship_start_date_onOrBefore)
            if relationship_start_date_onOrAfter:
                query = query.filter(Placement.start_date >= relationship_start_date_onOrAfter)
            if relationship_end_date_onOrBefore:
                query = query.filter(Placement.end_date <= relationship_end_date_onOrBefore)
            if relationship_end_date_onOrAfter:
                query = query.filter(Placement.end_date >= relationship_end_date_onOrAfter)
                
        elif relationship_entity_type == PersonRelationshipTypeEnum.groupMembership:
            query = query.join(GroupMembership, GroupMembership.person_id == Person.id)
            if relationship_start_date_onOrBefore:
                query = query.filter(GroupMembership.start_date <= relationship_start_date_onOrBefore)
            if relationship_start_date_onOrAfter:
                query = query.filter(GroupMembership.start_date >= relationship_start_date_onOrAfter)
            if relationship_end_date_onOrBefore:
                query = query.filter(GroupMembership.end_date <= relationship_end_date_onOrBefore)
            if relationship_end_date_onOrAfter:
                query = query.filter(GroupMembership.end_date >= relationship_end_date_onOrAfter)
                
        elif relationship_entity_type in [PersonRelationshipTypeEnum.responsibleFor_enrolment, PersonRelationshipTypeEnum.responsibleFor_placement]:
            # För enkelhetens skull i mocken, behandlas de här relationerna på samma sätt
            query = query.join(ResponsibleFor, ResponsibleFor.responsible_id == Person.id)
            if relationship_start_date_onOrBefore:
                query = query.filter(ResponsibleFor.start_date <= relationship_start_date_onOrBefore)
            if relationship_start_date_onOrAfter:
                query = query.filter(ResponsibleFor.start_date >= relationship_start_date_onOrAfter)
            if relationship_end_date_onOrBefore:
                query = query.filter(ResponsibleFor.end_date <= relationship_end_date_onOrBefore)
            if relationship_end_date_onOrAfter:
                query = query.filter(ResponsibleFor.end_date >= relationship_end_date_onOrAfter)

    # Applicera meta-parametrar
    query = apply_meta_filters(query, Person, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)

    # Applicera sortering
    if sortkey:
        query = apply_sorting(query, Person, sortkey)
    else:
        query = query.order_by(Person.display_name.asc()) # Standard sortering

    # Applicera paginering
    persons = query.offset(offset).limit(limit).all()
    
    # Expanderade data
    if expand or expandReferenceNames:
        return expand_persons_data(persons, expand, expandReferenceNames, db)
    else:
        return [PersonBase.from_orm(p) for p in persons]

@app.post("/persons/lookup", response_model=List[PersonExpanded])
def persons_lookup(
    request_body: LookupRequest,
    db: Session = Depends(get_db),
    expand: Optional[List[str]] = Query(None, description="Expands related data for the person, e.g., 'duties', 'placements'."),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returns expanded reference names in the response.")
):
    """
    Fetches multiple persons based on a list of IDs or social security numbers.
    """
    if not request_body.identifiers:
        return []

    # Get persons from the database
    persons = db.query(Person).filter(
        Person.id.in_(request_body.identifiers) | Person.civic_no.in_(request_body.identifiers) 
    ).all()

    if expand or expandReferenceNames:
        return expand_persons_data(persons, expand, expandReferenceNames, db)
    else:
        return [PersonBase.from_orm(p) for p in persons]

@app.get("/persons/{id}", response_model=PersonExpanded)
def get_person_by_id(
    id: str,
    db: Session = Depends(get_db),
    expand: Optional[List[str]] = Query(None, description="Expands related data for the person, e.g., 'duties', 'placements'."),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returns expanded reference names in the response.")
):
    """
    Get person by person id.
    """
    try:
        # Check if the ID is a valid UUID, otherwise it's a Bad Request (400)
        uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format. Must be a valid UUID.")
    
    person = db.query(Person).filter(Person.id == id).first()
    
    if not person:
        raise HTTPException(status_code=404, detail="Person not found.")
    
    expanded_data = {}
    if expand:
        expanded_data = expand_persons_data(List(person), expand, expandReferenceNames, db)
    
    person_dict = person.__dict__
    person_dict.update(expanded_data)
    
    return PersonExpanded(**person_dict)

# --- Placements endpoints below ---
@app.get("/placements", response_model=List[PlacementExpanded], summary="Hämta en lista med placeringar.")
def get_placements(
    db: Session = Depends(get_db),
    child_id: Optional[List[str]] = Query(None, alias="child"),
    owner_id: Optional[List[str]] = Query(None, alias="owner"),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="meta.created.before"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="meta.created.after"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="meta.modified.before"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="meta.modified.after"),
    expand: Optional[List[PlacementExpandEnum]] = Query(None, alias="expand", description="Lista med expanderbara fält, t.ex. 'child', 'owners'"),
    sortkey: Optional[str] = Query(None, description='Sorteringsordning, t.ex. "ModifiedDesc" eller "CreatedAsc".'),
    limit: int = 100,
    offset: int = 0,
):
    """
    Hämta en lista med placeringar baserat på filter och sorteringsparametrar.
    """
    query = db.query(Placement)
    
    # Apply filters
    if child_id:
        query = query.filter(Placement.child_id.in_(child_id))
    if owner_id:
        query = query.join(Placement.owners).filter(Person.id.in_(owner_id))

    query = apply_meta_filters(query, Placement, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Placement, sortkey)
    query = apply_expand_for_placements(query, expand)
    
    placements = query.offset(offset).limit(limit).all()

    return placements

@app.get("/placements/{id}", response_model=PlacementExpanded, summary="Placering baserat på id")
def get_placement_by_id(
    id: str,
    db: Session = Depends(get_db),
    expand: Optional[List[PlacementExpandEnum]] = Query(None, alias="expand"),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returnera 'displayName' för alla refererade objekt.")
):
    """
    Hämta en specifik placering baserat på dess ID.
    """
    query = db.query(Placement)
    query = apply_expand_for_placements(query, expand)
    
    placement = query.filter(Placement.id == id).first()
    
    if not placement:
        raise HTTPException(status_code=404, detail="Placering hittades inte")
        
    return placement

@app.post("/placements/lookup", response_model=PlacementExpandedArray, summary="Hämta många placeringar baserat på en lista av ID:n eller av Id från personer.")
def lookup_placements(
    lookup_data: LookupRequest,
    db: Session = Depends(get_db),
    expand: Optional[List[PlacementExpandEnum]] = Query(None, alias="expand"),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returnera 'displayName' för alla refererade objekt.")
):
    """
    Istället för att hämta placeringar en i taget med en loop av GET-anrop så finns det även möjlighet att hämta många placeringar på en gång genom att skicka ett anrop med en lista med önskade placeringar.
    """
    query = db.query(Placement)
    
    # Handle the lookup logic based on placement IDs and person IDs
    if not lookup_data.ids:
        return []
    
    # Check if any ID matches a placement, a child, or an owner.
    # We'll use or_ for this. We also need to do a join for the owners.
    query = query.join(Placement.owners, isouter=True).filter(
        or_(
            Placement.id.in_(lookup_data.ids),
            Placement.child_id.in_(lookup_data.ids),
            Person.id.in_(lookup_data.ids)
        )
    ).distinct()

    query = apply_expand_for_placements(query, expand)
    
    placements = query.all()
    
    return placements


@app.get("/duties", response_model=DutiesArray, summary="Hämta en lista med tjänstgöringar.")
def get_duties(
    db: Session = Depends(get_db),
    organisation: Optional[str] = Query(None, alias="organisation", description="Begränsa urvalet till de tjänstgöringar som är kopplade till ett organisationselement."),
    dutyRole: Optional[DutyRoleEnum] = Query(None, alias="dutyRole", description="Begränsta urvalet till de tjänstgöringar som matchar roll"),
    person: Optional[str] = Query(None, alias="person", description="Begränsa urvalet till de tjänstgöringar som är kopplade till person ID"),
    startDate_onOrBefore: Optional[date] = Query(None, alias="startDate.onOrBefore"),
    startDate_onOrAfter: Optional[date] = Query(None, alias="startDate.onOrAfter"),
    endDate_onOrBefore: Optional[date] = Query(None, alias="endDate.onOrBefore"),
    endDate_onOrAfter: Optional[date] = Query(None, alias="endDate.onOrAfter"),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="meta.created.before"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="meta.created.after"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="meta.modified.before"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="meta.modified.after"),
    expand: Optional[List[DutyExpandEnum]] = Query(None, alias="expand", description="Beskriver om expanderade data ska hämtas"),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames"),
    sortkey: Optional[str] = Query(None, description="Anger hur resultatet ska sorteras."),
    limit: int = 100,
    offset: int = 0,
):
    """
    Hämta en lista med tjänstgöringar baserat på filter och sorteringsparametrar.
    """
    if organisation:
        # NOTE: A full implementation for a real-world scenario would need to recursively
        # find all descendants of the given organisation, but for this mock API,
        # we will simply filter on the organisation ID directly.
        pass

    query = db.query(Duty)

    if organisation:
        query = query.filter(Duty.organisation_id == organisation)
    if dutyRole:
        query = query.filter(Duty.duty_role == dutyRole)
    if person:
        query = query.filter(Duty.person_id == person)
    if startDate_onOrBefore:
        query = query.filter(Duty.start_date <= startDate_onOrBefore)
    if startDate_onOrAfter:
        query = query.filter(Duty.start_date >= startDate_onOrAfter)
    if endDate_onOrBefore:
        query = query.filter(or_(Duty.end_date.is_(None), Duty.end_date <= endDate_onOrBefore))
    if endDate_onOrAfter:
        query = query.filter(or_(Duty.end_date.is_(None), Duty.end_date >= endDate_onOrAfter))

    query = apply_meta_filters(query, Duty, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_expand_for_duties(query, expand)
    query = apply_sorting(query, Duty, sortkey)

    duties = query.offset(offset).limit(limit).all()
    return duties

@app.get("/duties/{id}", response_model=DutyExpanded, summary="Hämta tjänstgöring baserat på tjänstgörings ID")
def get_duty_by_id(
    id: str,
    db: Session = Depends(get_db),
    expand: Optional[List[DutyExpandEnum]] = Query(None, alias="expand"),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames")
):
    """
    Hämta en specifik tjänstgöring baserat på dess ID.
    """
    query = db.query(Duty)
    query = apply_expand_for_duties(query, expand)
    
    duty = query.filter(Duty.id == id).first()
    
    if not duty:
        raise HTTPException(status_code=404, detail="Tjänstgöring hittades inte")
    
    return duty

@app.post("/duties/lookup", response_model=DutiesArray, summary="Hämta många tjänstgöringar baserat på en lista av ID:n.")
def lookup_duties(
    lookup_data: LookupRequest,
    db: Session = Depends(get_db),
    expand: Optional[List[DutyExpandEnum]] = Query(None, alias="expand"),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames")
):
    """
    Istället för att hämta tjänstgöringar en i taget med en loop av GET-anrop så finns det även möjlighet att hämta många tjänstgöringar på en gång genom att skicka ett anrop med en lista med önskade tjänstgöringar.
    """
    if not lookup_data.ids:
        return []

    query = db.query(Duty).filter(Duty.id.in_(lookup_data.ids))
    query = apply_expand_for_duties(query, expand)
    duties = query.all()
    return duties

@app.get("/groups", response_model=GroupsExpanded, summary="Hämta en lista med grupper.")
def get_groups(
    db: Session = Depends(get_db),
    groupType: Optional[List[GroupTypesEnum]] = Query(None, alias="groupType", description="Begränsa urvalet till grupper av en eller flera type."),
    schoolTypes: Optional[List[SchoolTypesEnum]] = Query(None, alias="schoolTypes", description="Begränsa urvalet av grupper till de som har en av de angivna skolformerna."),
    organisation: Optional[List[str]] = Query(None, alias="organisation", description="Begränsa urvalet till de grupper som direkt kopplade till angivna organisationselement."),
    startDate_onOrBefore: Optional[date] = Query(None, alias="startDate.onOrBefore"),
    startDate_onOrAfter: Optional[date] = Query(None, alias="startDate.onOrAfter"),
    endDate_onOrBefore: Optional[date] = Query(None, alias="endDate.onOrBefore"),
    endDate_onOrAfter: Optional[date] = Query(None, alias="endDate.onOrAfter"),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="meta.created.before"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="meta.created.after"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="meta.modified.before"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="meta.modified.after"),
    expand: Optional[List[GroupExpandEnum]] = Query(None, alias="expand", description="Beskriver om expanderade data ska hämtas"),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returnera 'displayName' för alla refererade objekt."),
    sortkey: Optional[str] = Query(None, description="Anger hur resultatet ska sorteras."),
    limit: int = 100,
    offset: int = 0,
    pageToken: Optional[str] = Query(None, alias="pageToken", description="Ett opakt värde som servern givit som svar på en tidigare ställd fråga. Kan inte kombineras med andra filter men väl med 'limit'."),
):
    """
    Hämta en lista med grupper baserat på filter och sorteringsparametrar.
    """
    if pageToken and any([groupType, schoolTypes, organisation, startDate_onOrBefore, startDate_onOrAfter, endDate_onOrBefore, endDate_onOrAfter, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter]):
        raise HTTPException(status_code=400, detail="Filter kan inte kombineras med pageToken.")
    
    # We ignore pageToken for this mock API as it requires more complex pagination logic.
    # We will raise a 400 error for any use of pageToken with other filters.
    if pageToken:
        # TODO: Implement pageToken logic if needed in the future
        raise HTTPException(status_code=501, detail="PageToken-funktionalitet är inte implementerad.")
        
    query = db.query(Group)

    if groupType:
        query = query.filter(Group.group_type.in_(groupType))
    if schoolTypes:
        # We need to filter by comma-separated string, so we'll do an OR
        or_clauses = [Group.school_types.like(f"%{st}%") for st in schoolTypes]
        query = query.filter(or_(*or_clauses))
    if organisation:
        query = query.filter(Group.organisation_id.in_(organisation))
    if startDate_onOrBefore:
        query = query.filter(Group.start_date <= startDate_onOrBefore)
    if startDate_onOrAfter:
        query = query.filter(Group.start_date >= startDate_onOrAfter)
    if endDate_onOrBefore:
        query = query.filter(or_(Group.end_date.is_(None), Group.end_date <= endDate_onOrBefore))
    if endDate_onOrAfter:
        query = query.filter(or_(Group.end_date.is_(None), Group.end_date >= endDate_onOrAfter))

    query = apply_meta_filters(query, Group, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_expand_for_groups(query, expand)
    query = apply_sorting(query, Group, sortkey)

    groups = query.offset(offset).limit(limit).all()
    
    # TODO: Handle expandReferenceNames for groups
    # This requires adding the logic to `expand_groups_data` function which is not yet created.

    return {"__root__": groups}

@app.post("/groups/lookup", response_model=GroupsExpanded, summary="Hämta många grupper baserat på en lista av ID:n.")
def lookup_groups(
    lookup_data: LookupRequest,
    db: Session = Depends(get_db),
    expand: Optional[List[GroupExpandEnum]] = Query(None, alias="expand"),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames")
):
    """
    Istället för att hämta grupper en i taget med en loop av GET-anrop så finns det även möjlighet att hämta många grupper på en gång genom att skicka ett anrop med en lista med önskade grupper.
    """
    if not lookup_data.ids:
        return []

    query = db.query(Group).filter(Group.id.in_(lookup_data.ids))
    query = apply_expand_for_groups(query, expand)
    groups = query.all()
    return {"__root__": groups}

@app.get("/groups/{id}", response_model=GroupExpanded, summary="Hämta grupp baserat på grupp ID")
def get_group_by_id(
    id: str,
    db: Session = Depends(get_db),
    expand: Optional[List[GroupExpandEnum]] = Query(None, alias="expand"),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames")
):
    """
    Hämta en specifik grupp baserat på dess ID.
    """
    query = db.query(Group)
    query = apply_expand_for_groups(query, expand)
    
    group = query.filter(Group.id == id).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Grupp hittades inte")
    
    return group

@app.get("/programmes", response_model=ProgrammesArray, summary="Hämta en lista av program.")
def get_programmes(
    db: Session = Depends(get_db),
    schoolTypes: Optional[List[SchoolTypesEnum]] = Query(None, alias="schoolType", description="Begränsa urvalet till de program som matchar skolformen."),
    code: Optional[str] = Query(None, description="Begränsta urvalet till de program som matchar programkod"),
    parentProgramme: Optional[str] = Query(None, description="Begränsta urvalet till de program som matchar angivet parentProgramme."),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="meta.created.before"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="meta.created.after"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="meta.modified.before"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="meta.modified.after"),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames"),
    sortkey: Optional[ProgrammeSortkeyEnum] = Query(None, description="Anger hur resultatet ska sorteras."),
    limit: int = 100,
    offset: int = 0,
    pageToken: Optional[str] = Query(None, alias="pageToken", description="Ett opakt värde som servern givit som svar på en tidigare ställd fråga. Kan inte kombineras med andra filter men väl med 'limit'."),
):
    """
    Hämta en lista med program baserat på filter och sorteringsparametrar.
    """
    if pageToken and any([schoolTypes, code, parentProgramme, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter]):
        raise HTTPException(status_code=400, detail="Filter kan inte kombineras med pageToken.")
        
    if pageToken:
        # TODO: Implement pageToken logic if needed in the future
        raise HTTPException(status_code=501, detail="PageToken-funktionalitet är inte implementerad.")
        
    query = db.query(Programme)
    
    if schoolTypes:
        or_clauses = [Programme.school_types.like(f"%{st}%") for st in schoolTypes]
        query = query.filter(or_(*or_clauses))
    if code:
        query = query.filter(Programme.code == code)
    if parentProgramme:
        query = query.filter(Programme.parent_programme_id == parentProgramme)
        
    query = apply_meta_filters(query, Programme, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Programme, sortkey)
    
    programmes = query.offset(offset).limit(limit).all()
    
    return programmes

@app.post("/programmes/lookup", response_model=ProgrammesArray, summary="Hämta många program baserat på en lista av ID:n.")
def lookup_programmes(
    lookup_data: LookupRequest,
    db: Session = Depends(get_db),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames")
):
    """
    Istället för att hämta program en i taget med en loop av GET-anrop så finns det även möjlighet att hämta många program på en gång genom att skicka ett anrop med en lista med önskade program.
    """
    if not lookup_data.ids:
        return []
    
    programmes = db.query(Programme).filter(Programme.id.in_(lookup_data.ids)).all()
    return programmes

@app.get("/programmes/{id}", response_model=Programme, summary="Hämta program baserat på ID")
def get_programme_by_id(
    id: str,
    db: Session = Depends(get_db),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames")
):
    """
    Hämta ett specifikt program baserat på dess ID.
    """
    programme = db.query(Programme).filter(Programme.id == id).first()
    
    if not programme:
        raise HTTPException(status_code=404, detail="Programmet hittades inte.")
    
    return programme

@app.get("/studyplans", response_model=Union[StudyPlans, StudyPlansExpandedArray])
def get_studyplans(
    db: Session = Depends(get_db),
    student: Optional[List[str]] = Query(None, description="Begränsa urvalet till utpekade elever."),
    startDate_onOrBefore: Optional[date] = Query(None, alias="startDate.onOrBefore"),
    startDate_onOrAfter: Optional[date] = Query(None, alias="startDate.onOrAfter"),
    endDate_onOrBefore: Optional[date] = Query(None, alias="endDate.onOrBefore"),
    endDate_onOrAfter: Optional[date] = Query(None, alias="endDate.onOrAfter"),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="meta.created.before"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="meta.created.after"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="meta.modified.before"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="meta.modified.after"),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returnera 'displayName' för alla refererade objekt."),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = Query(100, ge=1, le=100),
    offset: int = 0,
    pageToken: Optional[str] = Query(None, description="Ett opakt värde för sidnumrering. Kan inte kombineras med andra filter.")
):
    """Hämta en lista med studieplaner."""
    if pageToken and any([student, startDate_onOrBefore, startDate_onOrAfter, endDate_onOrBefore, endDate_onOrAfter, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter, sortkey, offset]):
        raise HTTPException(status_code=400, detail="Filter och sortkey kan inte kombineras med pageToken.")
    
    query = db.query(StudyPlan)
    
    # Använd ny hjälpkfunktion för att applicera filter
    query = apply_studyplan_filters(query, student, startDate_onOrBefore, startDate_onOrAfter, endDate_onOrBefore, endDate_onOrAfter)
    
    # Använd befintliga hjälpkfunktioner för metadata och sortering
    query = apply_meta_filters(query, StudyPlan, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, StudyPlan, sortkey)
    
    studyplans = query.offset(offset).limit(limit).all()
    
    # Hantera 'expandReferenceNames'
    if expandReferenceNames:
        expanded_studyplans = []
        for sp in studyplans:
            student_obj = db.query(Person).filter(Person.id == sp.student_id).first()
            expanded_sp = StudyPlanExpanded.from_orm(sp)
            expanded_sp.student = PersonSchema.from_orm(student_obj) if student_obj else None
            expanded_studyplans.append(expanded_sp)
        return expanded_studyplans
    
    return studyplans

@app.get("/studyplans/{id}", response_model=Union[StudyPlanSchema, StudyPlanExpanded])
def get_studyplan_by_id(
    id: str,
    db: Session = Depends(get_db),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returnera 'displayName' för alla refererade objekt.")
):
    """Hämta studieplan baserat på ID."""
    studyplan = db.query(StudyPlan).filter(StudyPlan.id == id).first()
    if not studyplan:
        raise HTTPException(status_code=404, detail="Posten hittades inte.")

    if expandReferenceNames:
        student_obj = db.query(Person).filter(Person.id == studyplan.student_id).first()
        expanded_sp = StudyPlanExpanded.from_orm(studyplan)
        expanded_sp.student = PersonSchema.from_orm(student_obj) if student_obj else None
        return expanded_sp
    
    return studyplan
    return study_plans

@app.get("/syllabuses", response_model=List[SyllabusBase])
def get_syllabuses(
    db: Session = Depends(get_db),
    subject_code: Optional[List[str]] = Query(None, description="Filtrera efter ämneskod."),
    course_code: Optional[List[str]] = Query(None, description="Filtrera efter kurskod."),
    school_unit_offerings: Optional[List[str]] = Query(None, alias="schoolUnitOfferings.id", description="Filtrera efter en lista med skolenhetserbjudande-ID:n."),
    programmes: Optional[List[str]] = Query(None, alias="programmes.id", description="Filtrera efter en lista med program-ID:n."),
    startDate_onOrBefore: Optional[date] = Query(None, alias="startDate.onOrBefore"),
    startDate_onOrAfter: Optional[date] = Query(None, alias="startDate.onOrAfter"),
    endDate_onOrBefore: Optional[date] = Query(None, alias="endDate.onOrBefore"),
    endDate_onOrAfter: Optional[date] = Query(None, alias="endDate.onOrAfter"),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="meta.created.before"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="meta.created.after"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="meta.modified.before"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="meta.modified.after"),
    sortkey: Optional[str] = Query(None, description='Sort order, e.g. "ModifiedDesc", "CreatedAsc".'),
    limit: int = Query(100, ge=1, le=100),
    offset: int = 0,
):
    """Hämta en lista med läroplaner."""
    query = db.query(Syllabus)
    query = apply_syllabus_filters(query, subject_code, course_code, school_unit_offerings, programmes, startDate_onOrBefore, startDate_onOrAfter, endDate_onOrBefore, endDate_onOrAfter)
    query = apply_meta_filters(query, Syllabus, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, Syllabus, sortkey)
    
    return query.offset(offset).limit(limit).all()

@app.get("/syllabuses/{id}", response_model=SyllabusBase)
def get_syllabus_by_id(id: str, db: Session = Depends(get_db)):
    """Hämta en läroplan baserat på ID."""
    syllabus = db.query(Syllabus).filter(Syllabus.id == id).first()
    if not syllabus:
        raise HTTPException(status_code=404, detail="Läroplan hittades inte.")
    return syllabus

@app.get("/schoolunitofferings", response_model=List[SchoolUnitOfferingSchema])
def get_school_unit_offerings(
    db: Session = Depends(get_db),
    metaCreatedBefore: Optional[datetime] = Query(None, alias="metaCreatedBefore"),
    metaCreatedAfter: Optional[datetime] = Query(None, alias="metaCreatedAfter"),
    metaModifiedBefore: Optional[datetime] = Query(None, alias="metaModifiedBefore"),
    metaModifiedAfter: Optional[datetime] = Query(None, alias="metaModifiedAfter"),
    sortkey: Optional[str] = Query(None),
    limit: int = 100,
    offset: int = 0,
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returns expanded reference names in the response."),
):
    """Hämtar en lista över skolenhetserbjudanden."""
    query = db.query(SchoolUnitOffering)
    query = apply_meta_filters(query, SchoolUnitOffering, metaCreatedBefore, metaCreatedAfter, metaModifiedBefore, metaModifiedAfter)
    query = apply_sorting(query, SchoolUnitOffering, sortkey)
    offerings = query.offset(offset).limit(limit).all()

    if expandReferenceNames:
        return [expand_school_unit_offering(o, True, db) for o in offerings]

    return offerings

@app.post("/schoolunitofferings/lookup", response_model=List[Union[SchoolUnitOfferingExpanded, SchoolUnitOfferingSchema]])
def lookup_school_unit_offerings(
    lookup_data: LookupRequest,
    db: Session = Depends(get_db),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returnerar expanderade referensnamn i responsen.")
):
    """Hämtar en lista med skolenhetserbjudanden baserat på en lista med ID:n."""
    offerings = db.query(SchoolUnitOffering).filter(SchoolUnitOffering.id.in_(lookup_data.ids)).all()
    
    if expandReferenceNames:
        return [expand_school_unit_offering(o, True, db) for o in offerings]
    
    return [SchoolUnitOfferingSchema.from_orm(o) for o in offerings]

@app.get("/schoolUnitOfferings/{id}", response_model=Union[SchoolUnitOfferingExpanded, SchoolUnitOfferingSchema])
def get_school_unit_offering_by_id(
    id: str,
    db: Session = Depends(get_db),
    expandReferenceNames: Optional[bool] = Query(None, alias="expandReferenceNames", description="Returnerar expanderade referensnamn i responsen.")
):
    """Hämtar ett skolenhetserbjudande baserat på dess ID."""
    offering = db.query(SchoolUnitOffering).filter(SchoolUnitOffering.id == id).first()
    if not offering:
        raise HTTPException(status_code=404, detail="SchoolUnitOffering not found")

    if expandReferenceNames:
        return expand_school_unit_offering(offering, True, db)
    
    return SchoolUnitOfferingSchema.from_orm(offering)

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
