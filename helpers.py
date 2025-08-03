from fastapi import HTTPException
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, asc, func, or_

from datetime import date
from typing import List, Optional
from database import *
from schemas import *

def apply_sorting(query, model, sortkey: Optional[str]):
    """
    Applicerar sortering på en SQLAlchemy-fråga baserat på sortkey-parametern.
    """
    if not sortkey:
        return query

    sort_mapping = {
        "ModifiedDesc": (model.modified, desc),
        "ModifiedAsc": (model.modified, asc),
        "CreatedDesc": (model.created, desc),
        "CreatedAsc": (model.created, asc),
        "DisplayNameAsc": (model.display_name, asc),
        "DisplayNameDesc": (model.display_name, desc),
        "GivenNameAsc": (model.given_name, asc),
        "GivenNameDesc": (model.given_name, desc),
        "FamilyNameAsc": (model.family_name, asc),
        "FamilyNameDesc": (model.family_name, desc),
        "CivicNoAsc": (model.civic_no, asc),
        "CivicNoDesc": (model.civic_no, desc),
        "StartDateDesc": (model.start_date, desc),
        "StartDateAsc": (model.start_date, asc),
        "EndDateAsc": (model.end_date, asc),
        "EndDateDesc": (model.end_date, desc),
        "NameAsc": (model.name, asc),
        "NameDesc": (model.name, desc),
    }
    
    # Check if the sortkey exists in the mapping before attempting to use it.
    if sortkey not in sort_mapping:
        raise HTTPException(status_code=400, detail=f"Ogiltig sortkey: {sortkey}")

    column, direction = sort_mapping.get(sortkey, (None, None))
    
    # We now have to handle the case when the sortkey is valid for some models but not for others.
    # For example 'DisplayNameAsc' is only valid for Person and not for other Models.
    try:
        if column and direction:
            query = query.order_by(direction(column))
    except AttributeError:
        # Handle case where the column does not exist on the model
        raise HTTPException(status_code=400, detail=f"Ogiltig sortkey: {sortkey} för denna resurs.")


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

def expand_organisations(organisations: List[Organisation], db: Session) -> List[OrganisationExpanded]:
    """
    Hjälpfunktion för att expandera organisationsobjekt med parent_name.
    """
    expanded_list = []
    for org in organisations:
        expanded_org = org.__dict__.copy()
        if org.parent_id:
            parent_org = db.query(Organisation).filter(Organisation.id == org.parent_id).first()
            if parent_org:
                expanded_org['parent_name'] = parent_org.name
        
        # Säkerställer att school_types hanteras korrekt innan konvertering till Pydantic
        if expanded_org.get('school_types') and isinstance(expanded_org['school_types'], str):
            expanded_org['school_types'] = [SchoolTypesEnum(t) for t in expanded_org['school_types'].split(',')]
            
        expanded_list.append(OrganisationExpanded(**expanded_org))
    return expanded_list

def expand_persons_data(persons: List[Person], expand: List[PersonExpandEnum], expand_ref_names: bool, db: Session) -> List[PersonExpanded]:
    """
    Hjälpfunktion för att expandera personobjekt med relaterad data.
    """
    expanded_list = []
    for person in persons:
        person_data = person.__dict__.copy()
        expanded_person = PersonExpanded(**person_data)

        if expand and expand_ref_names:
            # Hämta referensnamn för alla relevanta tabeller
            organisations = {org.id: org.name for org in db.query(Organisation).all()}
            persons_map = {p.id: p.display_name for p in db.query(Person).all()}
            groups = {g.id: g.name for g in db.query(Group).all()}
        
        if expand and PersonExpandEnum.duties in expand:
            duties = db.query(Duty).filter(Duty.person_id == person.id).all()
            if expand_ref_names:
                expanded_duties = []
                for duty in duties:
                    duty_schema = DutySchema.from_orm(duty)
                    duty_schema.person_name = persons_map.get(duty.person_id)
                    duty_schema.duty_at_name = organisations.get(duty.duty_at_id)
                    expanded_duties.append(duty_schema)
                expanded_person.duties = expanded_duties
            else:
                expanded_person.duties = [DutySchema.from_orm(d) for d in duties]

        if expand and PersonExpandEnum.placements in expand:
            placements = db.query(Placement).filter(Placement.child_id == person.id).all()
            if expand_ref_names:
                expanded_placements = []
                for placement in placements:
                    placement_schema = PlacementSchema.from_orm(placement)
                    placement_schema.child_name = persons_map.get(placement.child_id)
                    placement_schema.owner_name = persons_map.get(placement.owner_id)
                    placement_schema.placed_at_name = organisations.get(placement.placed_at_id)
                    expanded_placements.append(placement_schema)
                expanded_person.placements = expanded_placements
            else:
                expanded_person.placements = [PlacementSchema.from_orm(p) for p in placements]

        if expand and PersonExpandEnum.ownedPlacements in expand:
            owned_placements = db.query(Placement).filter(Placement.owner_id == person.id).all()
            if expand_ref_names:
                expanded_owned_placements = []
                for placement in owned_placements:
                    placement_schema = PlacementSchema.from_orm(placement)
                    placement_schema.child_name = persons_map.get(placement.child_id)
                    placement_schema.owner_name = persons_map.get(placement.owner_id)
                    placement_schema.placed_at_name = organisations.get(placement.placed_at_id)
                    expanded_owned_placements.append(placement_schema)
                expanded_person.owned_placements = expanded_owned_placements
            else:
                expanded_person.owned_placements = [PlacementSchema.from_orm(p) for p in owned_placements]
                
        if expand and PersonExpandEnum.groupMemberships in expand:
            group_memberships = db.query(GroupMembership).filter(GroupMembership.person_id == person.id).all()
            if expand_ref_names:
                expanded_group_memberships = []
                for gm in group_memberships:
                    gm_schema = GroupMembershipSchema.from_orm(gm)
                    gm_schema.person_name = persons_map.get(gm.person_id)
                    gm_schema.group_name = groups.get(gm.group_id)
                    expanded_group_memberships.append(gm_schema)
                expanded_person.group_memberships = expanded_group_memberships
            else:
                expanded_person.group_memberships = [GroupMembershipSchema.from_orm(gm) for gm in group_memberships]

        if expand and PersonExpandEnum.responsibleFor in expand:
            responsible_for = db.query(ResponsibleFor).filter(ResponsibleFor.responsible_id == person.id).all()
            if expand_ref_names:
                expanded_responsible_for = []
                for rf in responsible_for:
                    rf_schema = ResponsibleForSchema.from_orm(rf)
                    rf_schema.responsible_name = persons_map.get(rf.responsible_id)
                    rf_schema.child_name = persons_map.get(rf.child_id)
                    expanded_responsible_for.append(rf_schema)
                expanded_person.responsible_for = expanded_responsible_for
            else:
                expanded_person.responsible_for = [ResponsibleForSchema.from_orm(rf) for rf in responsible_for]
                
        expanded_list.append(expanded_person)
    return expanded_list

def apply_expand_for_placements(query, expands: Optional[List[PlacementExpandEnum]]):
    """
    Hjälpfunktion för att dynamiskt lägga till 'joinedload' för placeringar.
    """
    if not expands:
        return query

    if PlacementExpandEnum.child in expands:
        query = query.options(joinedload(Placement.child))
    if PlacementExpandEnum.owners in expands:
        query = query.options(joinedload(Placement.owners))
    
    return query

def apply_expand_for_duties(query, expands: Optional[List[DutyExpandEnum]]):
    """
    Hjälpfunktion för att dynamiskt lägga till 'joinedload' för tjänstgöringar.
    """
    if not expands:
        return query

    if DutyExpandEnum.person in expands:
        query = query.options(joinedload(Duty.person))
    
    return query

def apply_expand_for_groups(query, expands: Optional[List[GroupExpandEnum]]):
    """
    Hjälpfunktion för att dynamiskt lägga till 'joinedload' för grupper.
    """
    if not expands:
        return query
    
    if GroupExpandEnum.assignmentRoles in expands:
        query = query.options(joinedload(Group.assignment_roles))
        
    return query

def apply_studyplan_filters(query, student_ids: Optional[List[str]],
                            startDate_onOrBefore: Optional[date], startDate_onOrAfter: Optional[date],
                            endDate_onOrBefore: Optional[date], endDate_onOrAfter: Optional[date]):
    if student_ids:
        query = query.filter(StudyPlan.student_id.in_(student_ids))
    
    if startDate_onOrBefore:
        # Poster med null i end_date tas alltid med
        query = query.filter(or_(StudyPlan.start_date <= startDate_onOrBefore, StudyPlan.end_date.is_(None)))
    if startDate_onOrAfter:
        query = query.filter(or_(StudyPlan.start_date >= startDate_onOrAfter, StudyPlan.end_date.is_(None)))

    if endDate_onOrBefore:
        query = query.filter(or_(StudyPlan.end_date <= endDate_onOrBefore, StudyPlan.end_date.is_(None)))
    if endDate_onOrAfter:
        query = query.filter(or_(StudyPlan.end_date >= endDate_onOrAfter, StudyPlan.end_date.is_(None)))
        
    return query

def apply_syllabus_filters(query, subject_code: Optional[List[str]], course_code: Optional[List[str]],
                           school_unit_offerings: Optional[List[str]], programmes: Optional[List[str]],
                           start_date_onOrBefore: Optional[date], start_date_onOrAfter: Optional[date],
                           end_date_onOrBefore: Optional[date], end_date_onOrAfter: Optional[date]):
    if subject_code:
        query = query.filter(Syllabus.subject_code.in_(subject_code))
    if course_code:
        query = query.filter(Syllabus.course_code.in_(course_code))
    if school_unit_offerings:
        # Denna filtrering kräver en "LIKE"-sökning eftersom det är en komma-separerad sträng
        for suo_id in school_unit_offerings:
            query = query.filter(Syllabus.school_unit_offerings.like(f"%{suo_id}%"))
    if programmes:
        for p_id in programmes:
            query = query.filter(Syllabus.programmes.like(f"%{p_id}%"))
    if start_date_onOrBefore:
        query = query.filter(Syllabus.start_date <= start_date_onOrBefore)
    if start_date_onOrAfter:
        query = query.filter(Syllabus.start_date >= start_date_onOrAfter)
    if end_date_onOrBefore:
        query = query.filter(Syllabus.end_date <= end_date_onOrBefore)
    if end_date_onOrAfter:
        query = query.filter(Syllabus.end_date >= end_date_onOrAfter)
    return query

def expand_school_unit_offering(offering: SchoolUnitOffering, expandReferenceNames: bool, db: Session):
    if expandReferenceNames:
        offering_dict = offering.__dict__.copy()
        if offering.offered_at_id:
            organisation = db.query(Organisation).get(offering.offered_at_id)
            if organisation:
                offering_dict['offered_at'] = OrganisationBase.from_orm(organisation)
        return SchoolUnitOfferingExpanded(**offering_dict)
    return SchoolUnitOfferingSchema.from_orm(offering)