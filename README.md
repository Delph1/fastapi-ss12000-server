# **SS12000 Python Mock API Server**

This project provides a basic mock API server for the SS12000 standard, built using FastAPI. It's designed to simulate the SS12000 API endpoints, providing static and slightly dynamic JSON responses for testing and development purposes.

## **Table of Contents**

- [**SS12000 Python Mock API Server**](#ss12000-python-mock-api-server)
  - [**Table of Contents**](#table-of-contents)
  - [**Features**](#features)
  - [**Prerequisites**](#prerequisites)
  - [**Project Structure**](#project-structure)
  - [**Setup and Running**](#setup-and-running)
    - [**Local Setup (Python)**](#local-setup-python)
    - [**Docker Setup (Recommended)**](#docker-setup-recommended)
      - [**Using Docker Compose**](#using-docker-compose)
      - [**Manual Docker Commands**](#manual-docker-commands)
  - [**API Endpoints**](#api-endpoints)
  - [**Mock Data and Customization**](#mock-data-and-customization)
  - [**Contributing**](#contributing)
  - [**License**](#license)

## **Features**

* **FastAPI Framework:** Leverages FastAPI for high performance and automatic OpenAPI documentation.  
* **Mock Data:** Provides static mock data for core SS12000 resources (Organisations, Persons, Placements, etc.).  
* **Basic Filtering & Pagination:** Includes a helper to simulate limit, offset, and meta.modifiedAfter filters.  
* **CRUD Simulation:** Basic GET, POST, DELETE, and PATCH operations are mocked for relevant endpoints (e.g., Subscriptions, Attendances).  
* **Docker Support:** Easily containerize and run the mock server using Docker.  
* **Interactive Docs:** Automatic Swagger UI (/docs) and ReDoc (/redoc) for easy API exploration and testing.

## **Prerequisites**

To run this mock server, you will need:

* **Python 3.7+** (for local setup)  
* **pip** (Python package installer)  
* **Docker Desktop** (or Docker Engine) (for Docker setup)

## **Project Structure**

Your project directory should be structured as follows:  
ss12000-mock-server/  
├── main.py  
├── Dockerfile  
├── requirements.txt  
└── docker-compose.yml

* main.py: The main Python application code for the FastAPI server, containing all endpoint definitions and mock data.  
* Dockerfile: Defines the Docker image for the application.  
* requirements.txt: Lists the Python dependencies required by main.py.  
* docker-compose.yml: A Docker Compose file for easily building and running the server, especially useful for development with live reloading.

## **Setup and Running**

You can run the mock server either directly using Python or via Docker. Docker is recommended for ease of use and consistent environments.

### **Local Setup (Python)**

1. **Create a Project Directory:** Create a new directory (e.g., ss12000-mock-server) and navigate into it.  
2. **Save Files:** Place main.py and requirements.txt into this directory.  
3. **Create and Activate Virtual Environment (Recommended):**  
   python \-m venv venv  
   \# On Windows: .\\venv\\Scripts\\activate  
   \# On macOS/Linux: source venv/bin/activate

4. **Install Dependencies:**  
   pip install \-r requirements.txt

5. **Run the Server:**  
   uvicorn main:app \--reload \--port 8000

   The \--reload flag enables live reloading, so changes to main.py will automatically restart the server.

### **Docker Setup (Recommended)**

Ensure you have Docker Desktop installed and running.

#### **Using Docker Compose**

Docker Compose simplifies building and running multi-container Docker applications. It's ideal for development as it supports live reloading.

1. **Navigate to your project directory:**  
   cd ss12000-test-server

2. **Build and Run the services:**  
   docker-compose up \--build

   * The \--build flag tells Docker Compose to build the image. You only need this the first time or if Dockerfile or requirements.txt change.  
   * For subsequent runs after the first build, you can just use docker-compose up.  
3. Stop the services:  
   To stop and remove the containers, networks, and volumes created by docker-compose up, press Ctrl+C in your terminal, then run:  
   docker-compose down

#### **Manual Docker Commands**

You can also build and run the Docker image manually.

1. **Navigate to your project directory:**  
   cd ss12000-test-server

2. **Build the Docker image:**  
   docker build \-t ss12000-test-server .

   This command builds the Docker image and tags it as ss12000-test-server.  
3. **Run the Docker container:**  
   docker run \-p 8000:8000 ss12000-test-server

   This command runs a container from your image, mapping port 8000 on your host to port 8000 in the container.

## **API Endpoints**

Once the server is running (either locally or via Docker), you can access the API:

* **Interactive API Documentation (Swagger UI):** Open your web browser and go to http://localhost:8000/docs  
* **ReDoc Documentation:** http://localhost:8000/redoc

You can test the following endpoints:

* GET /organisations  
* GET /organisations/{organisation\_id}  
* POST /organisations/lookup  
* GET /persons  
* GET /persons/{person\_id}  
* POST /persons/lookup  
* GET /placements  
* GET /duties  
* GET /groups  
* GET /programmes  
* GET /studyplans  
* GET /syllabuses  
* GET /schoolUnitOfferings  
* GET /activities  
* GET /calendarEvents  
* GET /attendances  
* DELETE /attendances/{attendance\_id}  
* GET /attendanceEvents  
* GET /attendanceSchedules  
* GET /grades  
* GET /aggregatedAttendance  
* GET /resources  
* GET /rooms  
* GET /subscriptions  
* POST /subscriptions  
* DELETE /subscriptions/{subscription\_id}  
* GET /subscriptions/{subscription\_id}  
* PATCH /subscriptions/{subscription\_id}  
* GET /deletedEntities  
* GET /log  
* GET /statistics

Many GET endpoints support limit, offset, and meta.modifiedAfter query parameters for basic pagination and filtering.

## **Mock Data and Customization**

The mock data is currently hardcoded in main.py. For more advanced testing or to expand the mock data:

* **Edit main.py:** Directly modify the MOCK\_ variables (e.g., MOCK\_ORGANISATIONS, MOCK\_PERSONS) to add, remove, or change mock data.  
* **Implement More Dynamic Logic:** Enhance the apply\_pagination\_and\_filters or perform\_lookup functions, or add new logic to endpoints to simulate more complex API behaviors (e.g., specific filtering rules, error responses, relationships between entities).  
* **Externalize Mock Data:** For very large or complex mock datasets, consider loading the data from external JSON or YAML files instead of hardcoding it in main.py.

## **Contributing**

Feel free to fork this repository, add more mock data, implement more sophisticated dynamic behaviors, or improve the server in any way. Pull requests are welcome\!

## **License**

This project is open-source and available under the GNU GENERAL PUBLIC LICENSE Version 3.