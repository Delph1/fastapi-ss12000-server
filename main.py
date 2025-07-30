from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional, Dict, Any
import uvicorn

# Initialize the FastAPI application
app = FastAPI(
    title="SS12000 API Server",
    description="A basic mock server for the SS12000 API, serving static JSON responses.",
    version="0.1.0"
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
    }
]

# --- Helper function for pagination and filtering (basic) ---
def apply_pagination_and_filters(data: List[Dict], limit: int, offset: int, query_params: Dict[str, Any]) -> List[Dict]:
    """
    Applies basic pagination and a very simple 'meta.modifiedAfter' filter.
    For a full dynamic mock, this would be much more sophisticated.
    """
    filtered_data = []
    
    # Simple filtering for 'meta.modifiedAfter'
    modified_after_str = query_params.get('meta.modifiedAfter')
    if modified_after_str:
        try:
            modified_after_dt = datetime.fromisoformat(modified_after_str.replace('Z', '+00:00'))
            for item in data:
                item_modified_str = item.get('meta', {}).get('modified')
                if item_modified_str:
                    item_modified_dt = datetime.fromisoformat(item_modified_str.replace('Z', '+00:00'))
                    if item_modified_dt >= modified_after_dt:
                        filtered_data.append(item)
        except ValueError:
            # Handle invalid date format by ignoring the filter
            filtered_data = data # Fallback to unfiltered if date is invalid
            print(f"Warning: Invalid date format for meta.modifiedAfter: {modified_after_str}")
    else:
        filtered_data = data # No date filter applied

    # Apply pagination
    return filtered_data[offset : offset + limit]

# --- Endpoints ---

@app.get("/organisations", summary="Get a list of organisations")
async def get_organisations(
    limit: int = Query(100, ge=1, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    # Example of a potential filter param, not implemented for dynamic filtering yet
    # type: Optional[str] = Query(None, description="Filter by organisation type"),
    # For a basic mock, we'll just return all data for now, then apply pagination
    **kwargs: Any # Catch-all for other query parameters
):
    """
    Returns a list of mock organisations.
    Supports basic pagination.
    """
    paginated_data = apply_pagination_and_filters(MOCK_ORGANISATIONS, limit, offset, kwargs)
    return {
        "data": paginated_data,
        "meta": {
            "totalCount": len(MOCK_ORGANISATIONS),
            "limit": limit,
            "offset": offset
        }
    }

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
            # For a basic mock, expandReferenceNames doesn't change the static data
            return org
    raise HTTPException(status_code=404, detail="Organisation not found")

@app.get("/persons", summary="Get a list of persons")
async def get_persons(
    limit: int = Query(100, ge=1, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    # Example of a potential filter param
    # roles: Optional[List[str]] = Query(None, description="Filter by roles (e.g., Teacher, Student)"),
    # meta_modified_after: Optional[str] = Query(None, alias="meta.modifiedAfter", description="Filter by modified date (ISO 8601)"),
    **kwargs: Any # Catch-all for other query parameters
):
    """
    Returns a list of mock persons.
    Supports basic pagination and a simple 'meta.modifiedAfter' filter.
    """
    paginated_data = apply_pagination_and_filters(MOCK_PERSONS, limit, offset, kwargs)
    return {
        "data": paginated_data,
        "meta": {
            "totalCount": len(MOCK_PERSONS),
            "limit": limit,
            "offset": offset
        }
    }

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
            # For a basic mock, 'expand' and 'expandReferenceNames' don't change the static data
            # In a dynamic mock, you'd conditionally add related data here.
            return person
    raise HTTPException(status_code=404, detail="Person not found")

# --- Example of a POST endpoint (for subscriptions) ---
@app.post("/subscriptions", summary="Create a new subscription (webhook)")
async def create_subscription(subscription_data: Dict[str, Any]):
    """
    Mocks the creation of a new subscription.
    Returns the received data with a mock ID.
    """
    # In a real mock, you'd store this in-memory and assign a unique ID.
    # For simplicity, we'll just return the input data with a hardcoded ID.
    mock_id = "sub-12345-abcde"
    response_data = {
        "id": mock_id,
        "name": subscription_data.get("name", "New Mock Subscription"),
        "target": subscription_data.get("target"),
        "resourceTypes": subscription_data.get("resourceTypes", []),
        "meta": {
            "created": "2024-07-30T10:00:00Z",
            "modified": "2024-07-30T10:00:00Z"
        }
    }
    return response_data

# --- Running the server ---
if __name__ == "__main__":
    # To run this server, save the code as main.py and execute:
    # uvicorn main:app --reload --port 8000
    # Then open your browser to http://127.0.0.1:8000/docs
    from datetime import datetime # Import datetime here for local execution

    print("Starting SS12000 Mock API Server...")
    print("Access the interactive documentation at: http://127.0.0.1:8000/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)