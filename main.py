from fastapi import FastAPI, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime, timedelta
import uuid # For generating mock IDs

# Initialize the FastAPI application
app = FastAPI(
    title="SS12000 API Server",
    description="A basic test server for the SS12000 API, serving static and slightly dynamic JSON responses.",
    version="0.2.0" # Updated version
)

# --- Mock Data (Static JSON Responses) ---
# In a real scenario, you'd load these from files or generate them dynamically.

# Mock data for /organisations
MOCK_ORGANISATIONS = [
    {
        "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "displayName": "Mock School District North",
        "organisationNumber": "556000-1234",
        "type": "MainOrganization",
        "address": {
            "street": "Schoolvägen 10",
            "city": "Mockville",
            "postalCode": "12345",
            "country": "SE"
        },
        "contact": {
            "email": "info@mockschooldistrict.se",
            "phone": "+46123456789"
        },
        "meta": {
            "created": "2023-01-15T10:00:00Z",
            "modified": "2024-03-20T14:30:00Z"
        }
    },
    {
        "id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210",
        "displayName": "Mock High School East",
        "organisationNumber": "556000-5678",
        "type": "SchoolUnit",
        "parentOrganisation": {
            "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "displayName": "Mock School District North"
        },
        "address": {
            "street": "High School Allé 5",
            "city": "Mockville",
            "postalCode": "12345",
            "country": "SE"
        },
        "meta": {
            "created": "2023-02-01T08:00:00Z",
            "modified": "2024-04-10T11:00:00Z"
        }
    },
    {
        "id": "c1d2e3f4-a5b6-7890-1234-567890abcde1",
        "displayName": "Mock Elementary School West",
        "organisationNumber": "556000-9012",
        "type": "SchoolUnit",
        "parentOrganisation": {
            "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "displayName": "Mock School District North"
        },
        "address": {
            "street": "Oak Tree Lane 1",
            "city": "Mockville",
            "postalCode": "12345",
            "country": "SE"
        },
        "meta": {
            "created": "2023-03-01T09:00:00Z",
            "modified": "2024-05-01T10:00:00Z"
        }
    }
]

# Mock data for /persons
MOCK_PERSONS = [
    {
        "id": "11223344-5566-7788-99aa-bbccddeeff00",
        "firstName": "Anna",
        "lastName": "Andersson",
        "civicNumber": "19800101-1234",
        "email": "anna.andersson@mockschool.se",
        "roles": ["Teacher"],
        "meta": {
            "created": "2023-01-20T09:00:00Z",
            "modified": "2024-01-25T10:00:00Z"
        }
    },
    {
        "id": "22334455-6677-8899-aabb-ccddeeff0011",
        "firstName": "Erik",
        "lastName": "Eriksson",
        "civicNumber": "20050315-5678",
        "email": "erik.eriksson@mockschool.se",
        "roles": ["Student"],
        "meta": {
            "created": "2023-08-10T11:00:00Z",
            "modified": "2024-02-01T13:00:00Z"
        }
    },
    {
        "id": "33445566-7788-99aa-bbcc-ddeeff001122",
        "firstName": "Sara",
        "lastName": "Svensson",
        "civicNumber": "19950720-9876",
        "email": "sara.svensson@mockschool.se",
        "roles": ["Administrator"],
        "meta": {
            "created": "2023-05-01T14:00:00Z",
            "modified": "2024-03-05T09:00:00Z"
        }
    }
]

# Mock data for /placements
MOCK_PLACEMENTS = [
    {
        "id": "p1a2b3c4-d5e6-7890-1234-567890abcdef",
        "person": {"id": "11223344-5566-7788-99aa-bbccddeeff00", "displayName": "Anna Andersson"},
        "organisation": {"id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210", "displayName": "Mock High School East"},
        "startDate": "2023-08-15",
        "endDate": "2025-06-10",
        "type": "Employment",
        "meta": {
            "created": "2023-08-01T09:00:00Z",
            "modified": "2023-08-01T09:00:00Z"
        }
    },
    {
        "id": "p2b3c4d5-e6f7-8901-2345-67890abcdef0",
        "person": {"id": "22334455-6677-8899-aabb-ccddeeff0011", "displayName": "Erik Eriksson"},
        "organisation": {"id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210", "displayName": "Mock High School East"},
        "startDate": "2023-08-15",
        "endDate": "2026-06-10",
        "type": "StudentEnrollment",
        "meta": {
            "created": "2023-08-01T09:15:00Z",
            "modified": "2023-08-01T09:15:00Z"
        }
    }
]

# Mock data for /duties
MOCK_DUTIES = [
    {
        "id": "d1e2f3g4-h5i6-7890-1234-567890abcde0",
        "name": "Mathematics Teacher",
        "description": "Responsible for teaching mathematics to high school students.",
        "person": {"id": "11223344-5566-7788-99aa-bbccddeeff00", "displayName": "Anna Andersson"},
        "organisation": {"id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210", "displayName": "Mock High School East"},
        "meta": {
            "created": "2023-08-05T10:00:00Z",
            "modified": "2023-08-05T10:00:00Z"
        }
    },
    {
        "id": "d2e3f4g5-h6i7-8901-2345-67890abcdef1",
        "name": "Student Counselor",
        "description": "Provides guidance and support to students.",
        "person": {"id": "33445566-7788-99aa-bbcc-ddeeff001122", "displayName": "Sara Svensson"},
        "organisation": {"id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210", "displayName": "Mock High School East"},
        "meta": {
            "created": "2023-09-01T11:00:00Z",
            "modified": "2023-09-01T11:00:00Z"
        }
    }
]

# Mock data for /groups
MOCK_GROUPS = [
    {
        "id": "g1h2i3j4-k5l6-7890-1234-567890abcde0",
        "name": "Class 10A",
        "type": "Class",
        "organisation": {"id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210", "displayName": "Mock High School East"},
        "members": [
            {"id": "22334455-6677-8899-aabb-ccddeeff0011", "displayName": "Erik Eriksson"}
        ],
        "meta": {
            "created": "2023-08-10T08:00:00Z",
            "modified": "2023-08-10T08:00:00Z"
        }
    }
]

# Mock data for /programmes
MOCK_PROGRAMMES = [
    {
        "id": "pr1o2g3r-a4m5-6789-0123-456789abcdef",
        "name": "Natural Science Program",
        "code": "NV",
        "organisation": {"id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210", "displayName": "Mock High School East"},
        "meta": {
            "created": "2023-01-01T00:00:00Z",
            "modified": "2023-01-01T00:00:00Z"
        }
    }
]

# Mock data for /studyplans
MOCK_STUDYPLANS = [
    {
        "id": "st1u2d3y-p4l5-6789-0123-456789abcdef",
        "name": "Erik Eriksson's Study Plan",
        "person": {"id": "22334455-6677-8899-aabb-ccddeeff0011", "displayName": "Erik Eriksson"},
        "programme": {"id": "pr1o2g3r-a4m5-6789-0123-456789abcdef", "displayName": "Natural Science Program"},
        "meta": {
            "created": "2023-08-15T09:00:00Z",
            "modified": "2023-08-15T09:00:00Z"
        }
    }
]

# Mock data for /syllabuses
MOCK_SYLLABUSES = [
    {
        "id": "sy1l2l3a-b4u5-6789-0123-456789abcdef",
        "name": "Mathematics 3c Syllabus",
        "code": "MA3C",
        "description": "Syllabus for Mathematics course 3c.",
        "meta": {
            "created": "2022-06-01T00:00:00Z",
            "modified": "2022-06-01T00:00:00Z"
        }
    }
]

# Mock data for /schoolUnitOfferings
MOCK_SCHOOL_UNIT_OFFERINGS = [
    {
        "id": "off1e2r3i-n4g5-6789-0123-456789abcdef",
        "name": "Mathematics 3c - Fall 2024",
        "schoolUnit": {"id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210", "displayName": "Mock High School East"},
        "syllabus": {"id": "sy1l2l3a-b4u5-6789-0123-456789abcdef", "displayName": "Mathematics 3c Syllabus"},
        "startDate": "2024-08-20",
        "endDate": "2025-01-15",
        "meta": {
            "created": "2024-05-01T10:00:00Z",
            "modified": "2024-05-01T10:00:00Z"
        }
    }
]

# Mock data for /activities
MOCK_ACTIVITIES = [
    {
        "id": "act1i2v3i-t4y5-6789-0123-456789abcdef",
        "name": "Math 3c Lecture 1",
        "type": "Lecture",
        "schoolUnitOffering": {"id": "off1e2r3i-n4g5-6789-0123-456789abcdef", "displayName": "Mathematics 3c - Fall 2024"},
        "teachers": [{"id": "11223344-5566-7788-99aa-bbccddeeff00", "displayName": "Anna Andersson"}],
        "students": [{"id": "22334455-6677-8899-aabb-ccddeeff0011", "displayName": "Erik Eriksson"}],
        "meta": {
            "created": "2024-08-10T09:00:00Z",
            "modified": "2024-08-10T09:00:00Z"
        }
    }
]

# Mock data for /calendarEvents
MOCK_CALENDAR_EVENTS = [
    {
        "id": "cal1e2n3d-a4r5-6789-0123-456789abcdef",
        "activity": {"id": "act1i2v3i-t4y5-6789-0123-456789abcdef", "displayName": "Math 3c Lecture 1"},
        "startDateTime": "2024-08-20T09:00:00Z",
        "endDateTime": "2024-08-20T10:00:00Z",
        "room": {"id": "room123", "displayName": "Room A101"},
        "meta": {
            "created": "2024-08-10T09:00:00Z",
            "modified": "2024-08-10T09:00:00Z"
        }
    }
]

# Mock data for /attendances
MOCK_ATTENDANCES = [
    {
        "id": "att1e2n3d-a4n5-6789-0123-456789abcdef",
        "person": {"id": "22334455-6677-8899-aabb-ccddeeff0011", "displayName": "Erik Eriksson"},
        "activity": {"id": "act1i2v3i-t4y5-6789-0123-456789abcdef", "displayName": "Math 3c Lecture 1"},
        "status": "Present",
        "dateTime": "2024-08-20T09:05:00Z",
        "meta": {
            "created": "2024-08-20T09:05:00Z",
            "modified": "2024-08-20T09:05:00Z"
        }
    }
]

# Mock data for /attendanceEvents
MOCK_ATTENDANCE_EVENTS = [
    {
        "id": "atte1v2e3n-t4f5-6789-0123-456789abcdef",
        "attendance": {"id": "att1e2n3d-a4n5-6789-0123-456789abcdef", "displayName": "Erik Eriksson - Math 3c Lecture 1"},
        "type": "Created",
        "dateTime": "2024-08-20T09:05:00Z",
        "meta": {
            "created": "2024-08-20T09:05:00Z",
            "modified": "2024-08-20T09:05:00Z"
        }
    }
]

# Mock data for /attendanceSchedules
MOCK_ATTENDANCE_SCHEDULES = [
    {
        "id": "atts1c2h3e-d4u5-6789-0123-456789abcdef",
        "activity": {"id": "act1i2v3i-t4y5-6789-0123-456789abcdef", "displayName": "Math 3c Lecture 1"},
        "startDate": "2024-08-20",
        "endDate": "2025-01-15",
        "weekdays": ["Tuesday", "Thursday"],
        "timeOfDay": "09:00",
        "meta": {
            "created": "2024-08-01T10:00:00Z",
            "modified": "2024-08-01T10:00:00Z"
        }
    }
]

# Mock data for /grades
MOCK_GRADES = [
    {
        "id": "gr1a2d3e-f4g5-6789-0123-456789abcdef",
        "person": {"id": "22334455-6677-8899-aabb-ccddeeff0011", "displayName": "Erik Eriksson"},
        "schoolUnitOffering": {"id": "off1e2r3i-n4g5-6789-0123-456789abcdef", "displayName": "Mathematics 3c - Fall 2024"},
        "grade": "C",
        "gradeDate": "2025-01-10",
        "meta": {
            "created": "2025-01-10T11:00:00Z",
            "modified": "2025-01-10T11:00:00Z"
        }
    }
]

# Mock data for /aggregatedAttendance
MOCK_AGGREGATED_ATTENDANCE = [
    {
        "id": "agg1r2e3g-a4t5-6789-0123-456789abcdef",
        "person": {"id": "22334455-6677-8899-aabb-ccddeeff0011", "displayName": "Erik Eriksson"},
        "schoolUnitOffering": {"id": "off1e2r3i-n4g5-6789-0123-456789abcdef", "displayName": "Mathematics 3c - Fall 2024"},
        "totalPresentMinutes": 1200,
        "totalAbsentMinutes": 60,
        "periodStartDate": "2024-08-20",
        "periodEndDate": "2024-09-20",
        "meta": {
            "created": "2024-09-21T08:00:00Z",
            "modified": "2024-09-21T08:00:00Z"
        }
    }
]

# Mock data for /resources
MOCK_RESOURCES = [
    {
        "id": "res1o2u3r-c4e5-6789-0123-456789abcdef",
        "name": "Projector",
        "type": "Equipment",
        "organisation": {"id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210", "displayName": "Mock High School East"},
        "meta": {
            "created": "2023-01-01T00:00:00Z",
            "modified": "2023-01-01T00:00:00Z"
        }
    }
]

# Mock data for /rooms
MOCK_ROOMS = [
    {
        "id": "room123",
        "name": "Room A101",
        "capacity": 30,
        "organisation": {"id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210", "displayName": "Mock High School East"},
        "meta": {
            "created": "2023-01-01T00:00:00Z",
            "modified": "2023-01-01T00:00:00Z"
        }
    }
]

# In-memory store for subscriptions (to simulate creation/deletion)
IN_MEMORY_SUBSCRIPTIONS = {}

# In-memory store for deleted entities (to simulate deletion tracking)
IN_MEMORY_DELETED_ENTITIES = []

# In-memory store for log entries
IN_MEMORY_LOG_ENTRIES = []

# In-memory store for statistics
IN_MEMORY_STATISTICS = {
    "totalOrganisations": len(MOCK_ORGANISATIONS),
    "totalPersons": len(MOCK_PERSONS),
    "lastUpdated": datetime.now().isoformat(timespec='seconds') + 'Z'
}


# --- Helper function for pagination and filtering (basic) ---
def apply_pagination_and_filters(data: List[Dict], limit: int, offset: int, query_params: Dict[str, Any]) -> List[Dict]:
    """
    Applies basic pagination and a simple 'meta.modifiedAfter' filter.
    For a full dynamic mock, this would be much more sophisticated.
    """
    current_data = list(data) # Create a mutable copy

    # Simple filtering for 'meta.modifiedAfter'
    modified_after_str = query_params.get('meta.modifiedAfter')
    if modified_after_str:
        try:
            modified_after_dt = datetime.fromisoformat(modified_after_str.replace('Z', '+00:00'))
            current_data = [
                item for item in current_data
                if item.get('meta', {}).get('modified') and
                   datetime.fromisoformat(item['meta']['modified'].replace('Z', '+00:00')) >= modified_after_dt
            ]
        except ValueError:
            print(f"Warning: Invalid date format for meta.modifiedAfter: {modified_after_str}. Filter ignored.")
    
    # Simple filtering for 'type' (e.g., for organisations)
    type_filter = query_params.get('type')
    if type_filter:
        current_data = [item for item in current_data if item.get('type') == type_filter]

    # Simple filtering for 'roles' (e.g., for persons)
    roles_filter = query_params.get('roles')
    if roles_filter and isinstance(roles_filter, list):
        current_data = [item for item in current_data if any(role in item.get('roles', []) for role in roles_filter)]

    # Apply pagination
    return current_data[offset : offset + limit]


# --- Generic Lookup Helper ---
def perform_lookup(
    data_source: List[Dict],
    ids: Optional[List[str]] = None,
    civic_numbers: Optional[List[str]] = None,
    expand: Optional[List[str]] = None,
    expand_reference_names: bool = False
) -> List[Dict]:
    """
    Generic helper to perform lookup operations on a data source.
    Simulates fetching by ID or civic number and basic expansion.
    """
    results = []
    
    if ids:
        for item_id in ids:
            for item in data_source:
                if item.get('id') == item_id:
                    result_item = item.copy()
                    # Apply basic expansion if requested (for mock purposes, just a placeholder)
                    if expand:
                        for exp_field in expand:
                            if exp_field == "duties" and "roles" in item and "Teacher" in item["roles"]:
                                result_item["duties"] = [
                                    {"id": "mock-duty-id-1", "name": "Mock Teaching Duty"}
                                ]
                            # Add more expansion logic here as needed
                    results.append(result_item)
                    break
    
    if civic_numbers:
        for civic_num in civic_numbers:
            for item in data_source:
                if item.get('civicNumber') == civic_num:
                    results.append(item.copy()) # Add copy to results
                    break
    
    # For expandReferenceNames, in a real mock, you'd iterate through references
    # and add displayNames. For static data, this is mostly illustrative.
    
    return results

# --- Endpoints ---

# Organisations
@app.get("/organisations", summary="Get a list of organisations")
async def get_organisations(
    limit: int = Query(100, ge=1, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    type: Optional[str] = Query(None, description="Filter by organisation type (e.g., 'MainOrganization', 'SchoolUnit')"),
    **kwargs: Any # Catch-all for other query parameters
):
    """
    Returns a list of mock organisations.
    Supports basic pagination and filtering by 'type'.
    """
    query_params = {"type": type, **kwargs}
    paginated_data = apply_pagination_and_filters(MOCK_ORGANISATIONS, limit, offset, query_params)
    return {
        "data": paginated_data,
        "meta": {
            "totalCount": len(MOCK_ORGANISATIONS),
            "limit": limit,
            "offset": offset
        }
    }

@app.post("/organisations/lookup", summary="Lookup multiple organisations by ID")
async def lookup_organisations(
    body: Dict[str, Any] = Body(..., example={"organisationIds": ["a1b2c3d4-e5f6-7890-1234-567890abcdef"]}),
    expandReferenceNames: bool = Query(False, description="Return displayName for all referenced objects")
):
    """
    Returns multiple mock organisations based on a list of IDs.
    """
    organisation_ids = body.get("organisationIds", [])
    results = perform_lookup(MOCK_ORGANISATIONS, ids=organisation_ids, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/organisations/{organisation_id}", summary="Get a specific organisation by ID")
async def get_organisation_by_id(
    organisation_id: str,
    expandReferenceNames: bool = Query(False, description="Return displayName for all referenced objects")
):
    """
    Returns a specific mock organisation by its ID.
    """
    for org in MOCK_ORGANISATIONS:
        if org["id"] == organisation_id:
            return org
    raise HTTPException(status_code=404, detail="Organisation not found")

# Persons
@app.get("/persons", summary="Get a list of persons")
async def get_persons(
    limit: int = Query(100, ge=1, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    roles: Optional[List[str]] = Query(None, description="Filter by roles (e.g., Teacher, Student)"),
    meta_modified_after: Optional[str] = Query(None, alias="meta.modifiedAfter", description="Filter by modified date (ISO 8601)"),
    **kwargs: Any # Catch-all for other query parameters
):
    """
    Returns a list of mock persons.
    Supports basic pagination and filtering by 'roles' and 'meta.modifiedAfter'.
    """
    query_params = {"roles": roles, "meta.modifiedAfter": meta_modified_after, **kwargs}
    paginated_data = apply_pagination_and_filters(MOCK_PERSONS, limit, offset, query_params)
    return {
        "data": paginated_data,
        "meta": {
            "totalCount": len(MOCK_PERSONS),
            "limit": limit,
            "offset": offset
        }
    }

@app.post("/persons/lookup", summary="Lookup multiple persons by ID or civic number")
async def lookup_persons(
    body: Dict[str, Any] = Body(..., example={"personIds": ["11223344-5566-7788-99aa-bbccddeeff00"], "civicNumbers": ["19800101-1234"]}),
    expand: Optional[List[str]] = Query(None, description="Describes if expanded data should be fetched (e.g., duties)"),
    expandReferenceNames: bool = Query(False, description="Return displayName for all referenced objects")
):
    """
    Returns multiple mock persons based on a list of IDs or civic numbers.
    """
    person_ids = body.get("personIds")
    civic_numbers = body.get("civicNumbers")
    results = perform_lookup(MOCK_PERSONS, ids=person_ids, civic_numbers=civic_numbers, expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/persons/{person_id}", summary="Get a specific person by ID")
async def get_person_by_id(
    person_id: str,
    expand: Optional[List[str]] = Query(None, description="Describes if expanded data should be fetched (e.g., duties)"),
    expandReferenceNames: bool = Query(False, description="Return displayName for all referenced objects")
):
    """
    Returns a specific mock person by their ID.
    """
    for person in MOCK_PERSONS:
        if person["id"] == person_id:
            # In a dynamic mock, you'd conditionally add related data here based on 'expand'.
            return person
    raise HTTPException(status_code=404, detail="Person not found")

# Placements
@app.get("/placements", summary="Get a list of placements")
async def get_placements(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_PLACEMENTS, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_PLACEMENTS), "limit": limit, "offset": offset}}

@app.post("/placements/lookup", summary="Lookup multiple placements by ID")
async def lookup_placements(
    body: Dict[str, Any] = Body(..., example={"placementIds": ["p1a2b3c4-d5e6-7890-1234-567890abcdef"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_PLACEMENTS, ids=body.get("placementIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/placements/{placement_id}", summary="Get a specific placement by ID")
async def get_placement_by_id(
    placement_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_PLACEMENTS:
        if item["id"] == placement_id: return item
    raise HTTPException(status_code=404, detail="Placement not found")

# Duties
@app.get("/duties", summary="Get a list of duties")
async def get_duties(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_DUTIES, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_DUTIES), "limit": limit, "offset": offset}}

@app.post("/duties/lookup", summary="Lookup multiple duties by ID")
async def lookup_duties(
    body: Dict[str, Any] = Body(..., example={"dutyIds": ["d1e2f3g4-h5i6-7890-1234-567890abcde0"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_DUTIES, ids=body.get("dutyIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/duties/{duty_id}", summary="Get a specific duty by ID")
async def get_duty_by_id(
    duty_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_DUTIES:
        if item["id"] == duty_id: return item
    raise HTTPException(status_code=404, detail="Duty not found")

# Groups
@app.get("/groups", summary="Get a list of groups")
async def get_groups(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_GROUPS, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_GROUPS), "limit": limit, "offset": offset}}

@app.post("/groups/lookup", summary="Lookup multiple groups by ID")
async def lookup_groups(
    body: Dict[str, Any] = Body(..., example={"groupIds": ["g1h2i3j4-k5l6-7890-1234-567890abcde0"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_GROUPS, ids=body.get("groupIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/groups/{group_id}", summary="Get a specific group by ID")
async def get_group_by_id(
    group_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_GROUPS:
        if item["id"] == group_id: return item
    raise HTTPException(status_code=404, detail="Group not found")

# Programmes
@app.get("/programmes", summary="Get a list of programmes")
async def get_programmes(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_PROGRAMMES, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_PROGRAMMES), "limit": limit, "offset": offset}}

@app.post("/programmes/lookup", summary="Lookup multiple programmes by ID")
async def lookup_programmes(
    body: Dict[str, Any] = Body(..., example={"programmeIds": ["pr1o2g3r-a4m5-6789-0123-456789abcdef"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_PROGRAMMES, ids=body.get("programmeIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/programmes/{programme_id}", summary="Get a specific programme by ID")
async def get_programme_by_id(
    programme_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_PROGRAMMES:
        if item["id"] == programme_id: return item
    raise HTTPException(status_code=404, detail="Programme not found")

# StudyPlans
@app.get("/studyplans", summary="Get a list of study plans")
async def get_studyplans(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_STUDYPLANS, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_STUDYPLANS), "limit": limit, "offset": offset}}

@app.post("/studyplans/lookup", summary="Lookup multiple study plans by ID")
async def lookup_studyplans(
    body: Dict[str, Any] = Body(..., example={"studyPlanIds": ["st1u2d3y-p4l5-6789-0123-456789abcdef"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_STUDYPLANS, ids=body.get("studyPlanIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/studyplans/{study_plan_id}", summary="Get a specific study plan by ID")
async def get_studyplan_by_id(
    study_plan_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_STUDYPLANS:
        if item["id"] == study_plan_id: return item
    raise HTTPException(status_code=404, detail="Study Plan not found")

# Syllabuses
@app.get("/syllabuses", summary="Get a list of syllabuses")
async def get_syllabuses(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_SYLLABUSES, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_SYLLABUSES), "limit": limit, "offset": offset}}

@app.post("/syllabuses/lookup", summary="Lookup multiple syllabuses by ID")
async def lookup_syllabuses(
    body: Dict[str, Any] = Body(..., example={"syllabusIds": ["sy1l2l3a-b4u5-6789-0123-456789abcdef"]}),
    expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_SYLLABUSES, ids=body.get("syllabusIds"), expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/syllabuses/{syllabus_id}", summary="Get a specific syllabus by ID")
async def get_syllabus_by_id(
    syllabus_id: str, expandReferenceNames: bool = Query(False)
):
    for item in MOCK_SYLLABUSES:
        if item["id"] == syllabus_id: return item
    raise HTTPException(status_code=404, detail="Syllabus not found")

# SchoolUnitOfferings
@app.get("/schoolUnitOfferings", summary="Get a list of school unit offerings")
async def get_school_unit_offerings(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_SCHOOL_UNIT_OFFERINGS, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_SCHOOL_UNIT_OFFERINGS), "limit": limit, "offset": offset}}

@app.post("/schoolUnitOfferings/lookup", summary="Lookup multiple school unit offerings by ID")
async def lookup_school_unit_offerings(
    body: Dict[str, Any] = Body(..., example={"schoolUnitOfferingIds": ["off1e2r3i-n4g5-6789-0123-456789abcdef"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_SCHOOL_UNIT_OFFERINGS, ids=body.get("schoolUnitOfferingIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/schoolUnitOfferings/{offering_id}", summary="Get a specific school unit offering by ID")
async def get_school_unit_offering_by_id(
    offering_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_SCHOOL_UNIT_OFFERINGS:
        if item["id"] == offering_id: return item
    raise HTTPException(status_code=404, detail="School Unit Offering not found")

# Activities
@app.get("/activities", summary="Get a list of activities")
async def get_activities(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_ACTIVITIES, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_ACTIVITIES), "limit": limit, "offset": offset}}

@app.post("/activities/lookup", summary="Lookup multiple activities by ID")
async def lookup_activities(
    body: Dict[str, Any] = Body(..., example={"activityIds": ["act1i2v3i-t4y5-6789-0123-456789abcdef"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_ACTIVITIES, ids=body.get("activityIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/activities/{activity_id}", summary="Get a specific activity by ID")
async def get_activity_by_id(
    activity_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_ACTIVITIES:
        if item["id"] == activity_id: return item
    raise HTTPException(status_code=404, detail="Activity not found")

# CalendarEvents
@app.get("/calendarEvents", summary="Get a list of calendar events")
async def get_calendar_events(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_CALENDAR_EVENTS, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_CALENDAR_EVENTS), "limit": limit, "offset": offset}}

@app.post("/calendarEvents/lookup", summary="Lookup multiple calendar events by ID")
async def lookup_calendar_events(
    body: Dict[str, Any] = Body(..., example={"calendarEventIds": ["cal1e2n3d-a4r5-6789-0123-456789abcdef"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_CALENDAR_EVENTS, ids=body.get("calendarEventIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/calendarEvents/{event_id}", summary="Get a specific calendar event by ID")
async def get_calendar_event_by_id(
    event_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_CALENDAR_EVENTS:
        if item["id"] == event_id: return item
    raise HTTPException(status_code=404, detail="Calendar Event not found")

# Attendances
@app.get("/attendances", summary="Get a list of attendances")
async def get_attendances(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_ATTENDANCES, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_ATTENDANCES), "limit": limit, "offset": offset}}

@app.post("/attendances/lookup", summary="Lookup multiple attendances by ID")
async def lookup_attendances(
    body: Dict[str, Any] = Body(..., example={"attendanceIds": ["att1e2n3d-a4n5-6789-0123-456789abcdef"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_ATTENDANCES, ids=body.get("attendanceIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/attendances/{attendance_id}", summary="Get a specific attendance by ID")
async def get_attendance_by_id(
    attendance_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_ATTENDANCES:
        if item["id"] == attendance_id: return item
    raise HTTPException(status_code=404, detail="Attendance not found")

@app.delete("/attendances/{attendance_id}", summary="Delete an attendance by ID")
async def delete_attendance(attendance_id: str):
    global MOCK_ATTENDANCES # Indicate modification of global list
    original_len = len(MOCK_ATTENDANCES)
    MOCK_ATTENDANCES = [item for item in MOCK_ATTENDANCES if item["id"] != attendance_id]
    if len(MOCK_ATTENDANCES) < original_len:
        # Simulate adding to deleted entities log
        IN_MEMORY_DELETED_ENTITIES.append({
            "id": attendance_id,
            "entityType": "Attendance",
            "deletedAt": datetime.now().isoformat(timespec='seconds') + 'Z'
        })
        return {"message": "Attendance deleted successfully"}
    raise HTTPException(status_code=404, detail="Attendance not found")

# AttendanceEvents
@app.get("/attendanceEvents", summary="Get a list of attendance events")
async def get_attendance_events(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_ATTENDANCE_EVENTS, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_ATTENDANCE_EVENTS), "limit": limit, "offset": offset}}

@app.post("/attendanceEvents/lookup", summary="Lookup multiple attendance events by ID")
async def lookup_attendance_events(
    body: Dict[str, Any] = Body(..., example={"attendanceEventIds": ["atte1v2e3n-t4f5-6789-0123-456789abcdef"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_ATTENDANCE_EVENTS, ids=body.get("attendanceEventIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/attendanceEvents/{event_id}", summary="Get a specific attendance event by ID")
async def get_attendance_event_by_id(
    event_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_ATTENDANCE_EVENTS:
        if item["id"] == event_id: return item
    raise HTTPException(status_code=404, detail="Attendance Event not found")

# AttendanceSchedules
@app.get("/attendanceSchedules", summary="Get a list of attendance schedules")
async def get_attendance_schedules(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_ATTENDANCE_SCHEDULES, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_ATTENDANCE_SCHEDULES), "limit": limit, "offset": offset}}

@app.post("/attendanceSchedules/lookup", summary="Lookup multiple attendance schedules by ID")
async def lookup_attendance_schedules(
    body: Dict[str, Any] = Body(..., example={"attendanceScheduleIds": ["atts1c2h3e-d4u5-6789-0123-456789abcdef"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_ATTENDANCE_SCHEDULES, ids=body.get("attendanceScheduleIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/attendanceSchedules/{schedule_id}", summary="Get a specific attendance schedule by ID")
async def get_attendance_schedule_by_id(
    schedule_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_ATTENDANCE_SCHEDULES:
        if item["id"] == schedule_id: return item
    raise HTTPException(status_code=404, detail="Attendance Schedule not found")

# Grades
@app.get("/grades", summary="Get a list of grades")
async def get_grades(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_GRADES, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_GRADES), "limit": limit, "offset": offset}}

@app.post("/grades/lookup", summary="Lookup multiple grades by ID")
async def lookup_grades(
    body: Dict[str, Any] = Body(..., example={"gradeIds": ["gr1a2d3e-f4g5-6789-0123-456789abcdef"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_GRADES, ids=body.get("gradeIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/grades/{grade_id}", summary="Get a specific grade by ID")
async def get_grade_by_id(
    grade_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_GRADES:
        if item["id"] == grade_id: return item
    raise HTTPException(status_code=404, detail="Grade not found")

# AggregatedAttendance
@app.get("/aggregatedAttendance", summary="Get a list of aggregated attendance records")
async def get_aggregated_attendances(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_AGGREGATED_ATTENDANCE, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_AGGREGATED_ATTENDANCE), "limit": limit, "offset": offset}}

@app.post("/aggregatedAttendance/lookup", summary="Lookup multiple aggregated attendance records by ID")
async def lookup_aggregated_attendances(
    body: Dict[str, Any] = Body(..., example={"aggregatedAttendanceIds": ["agg1r2e3g-a4t5-6789-0123-456789abcdef"]}),
    expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_AGGREGATED_ATTENDANCE, ids=body.get("aggregatedAttendanceIds"), expand=expand, expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/aggregatedAttendance/{attendance_id}", summary="Get a specific aggregated attendance record by ID")
async def get_aggregated_attendance_by_id(
    attendance_id: str, expand: Optional[List[str]] = Query(None), expandReferenceNames: bool = Query(False)
):
    for item in MOCK_AGGREGATED_ATTENDANCE:
        if item["id"] == attendance_id: return item
    raise HTTPException(status_code=404, detail="Aggregated Attendance not found")

# Resources
@app.get("/resources", summary="Get a list of resources")
async def get_resources(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_RESOURCES, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_RESOURCES), "limit": limit, "offset": offset}}

@app.post("/resources/lookup", summary="Lookup multiple resources by ID")
async def lookup_resources(
    body: Dict[str, Any] = Body(..., example={"resourceIds": ["res1o2u3r-c4e5-6789-0123-456789abcdef"]}),
    expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_RESOURCES, ids=body.get("resourceIds"), expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/resources/{resource_id}", summary="Get a specific resource by ID")
async def get_resource_by_id(
    resource_id: str, expandReferenceNames: bool = Query(False)
):
    for item in MOCK_RESOURCES:
        if item["id"] == resource_id: return item
    raise HTTPException(status_code=404, detail="Resource not found")

# Rooms
@app.get("/rooms", summary="Get a list of rooms")
async def get_rooms(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(MOCK_ROOMS, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(MOCK_ROOMS), "limit": limit, "offset": offset}}

@app.post("/rooms/lookup", summary="Lookup multiple rooms by ID")
async def lookup_rooms(
    body: Dict[str, Any] = Body(..., example={"roomIds": ["room123"]}),
    expandReferenceNames: bool = Query(False)
):
    results = perform_lookup(MOCK_ROOMS, ids=body.get("roomIds"), expand_reference_names=expandReferenceNames)
    return {"data": results}

@app.get("/rooms/{room_id}", summary="Get a specific room by ID")
async def get_room_by_id(
    room_id: str, expandReferenceNames: bool = Query(False)
):
    for item in MOCK_ROOMS:
        if item["id"] == room_id: return item
    raise HTTPException(status_code=404, detail="Room not found")

# Subscriptions (Webhooks)
@app.get("/subscriptions", summary="Get a list of subscriptions")
async def get_subscriptions(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(list(IN_MEMORY_SUBSCRIPTIONS.values()), limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(IN_MEMORY_SUBSCRIPTIONS), "limit": limit, "offset": offset}}

@app.post("/subscriptions", summary="Create a new subscription (webhook)")
async def create_subscription(subscription_data: Dict[str, Any]):
    """
    Mocks the creation of a new subscription.
    Returns the received data with a mock ID.
    """
    new_id = str(uuid.uuid4())
    current_time = datetime.now().isoformat(timespec='seconds') + 'Z'
    response_data = {
        "id": new_id,
        "name": subscription_data.get("name", "New Mock Subscription"),
        "target": subscription_data.get("target"),
        "resourceTypes": subscription_data.get("resourceTypes", []),
        "meta": {
            "created": current_time,
            "modified": current_time
        }
    }
    IN_MEMORY_SUBSCRIPTIONS[new_id] = response_data
    return response_data

@app.delete("/subscriptions/{subscription_id}", summary="Delete a subscription by ID")
async def delete_subscription(subscription_id: str):
    if subscription_id in IN_MEMORY_SUBSCRIPTIONS:
        del IN_MEMORY_SUBSCRIPTIONS[subscription_id]
        return {"message": "Subscription deleted successfully"}
    raise HTTPException(status_code=404, detail="Subscription not found")

@app.get("/subscriptions/{subscription_id}", summary="Get a specific subscription by ID")
async def get_subscription_by_id(subscription_id: str):
    if subscription_id in IN_MEMORY_SUBSCRIPTIONS:
        return IN_MEMORY_SUBSCRIPTIONS[subscription_id]
    raise HTTPException(status_code=404, detail="Subscription not found")

@app.patch("/subscriptions/{subscription_id}", summary="Update a subscription by ID")
async def update_subscription(subscription_id: str, subscription_data: Dict[str, Any]):
    if subscription_id not in IN_MEMORY_SUBSCRIPTIONS:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    current_sub = IN_MEMORY_SUBSCRIPTIONS[subscription_id]
    current_sub.update(subscription_data)
    current_sub["meta"]["modified"] = datetime.now().isoformat(timespec='seconds') + 'Z'
    return current_sub

# DeletedEntities
@app.get("/deletedEntities", summary="Get a list of deleted entities")
async def get_deleted_entities(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    paginated_data = apply_pagination_and_filters(IN_MEMORY_DELETED_ENTITIES, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(IN_MEMORY_DELETED_ENTITIES), "limit": limit, "offset": offset}}

# Log
@app.get("/log", summary="Get a list of log entries")
async def get_log(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    # Simulate some log entries if empty
    if not IN_MEMORY_LOG_ENTRIES:
        IN_MEMORY_LOG_ENTRIES.extend([
            {"id": str(uuid.uuid4()), "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(timespec='seconds') + 'Z', "level": "INFO", "message": "Server started."},
            {"id": str(uuid.uuid4()), "timestamp": (datetime.now() - timedelta(minutes=2)).isoformat(timespec='seconds') + 'Z', "level": "WARNING", "message": "Mock data loaded."},
        ])
    paginated_data = apply_pagination_and_filters(IN_MEMORY_LOG_ENTRIES, limit, offset, kwargs)
    return {"data": paginated_data, "meta": {"totalCount": len(IN_MEMORY_LOG_ENTRIES), "limit": limit, "offset": offset}}

# Statistics
@app.get("/statistics", summary="Get API statistics")
async def get_statistics(
    limit: int = Query(100, ge=1), offset: int = Query(0, ge=0), **kwargs: Any
):
    # For statistics, we'll just return the single mock object for now
    # In a more advanced mock, this could be dynamically calculated.
    return {"data": [IN_MEMORY_STATISTICS], "meta": {"totalCount": 1, "limit": limit, "offset": offset}}


# --- Running the server ---
if __name__ == "__main__":
    # To run this server, save the code as main.py and execute:
    # uvicorn main:app --reload --port 8000
    # Then open your browser to http://127.0.0.1:8000/docs

    print("Starting SS12000 Mock API Server...")
    print("Access the interactive documentation at: http://127.0.0.1:8000/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
