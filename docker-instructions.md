# **Docker Instructions for SS12000 test Server**

This section outlines how to build and run your SS12000 Python Mock Server using Docker and Docker Compose.

## **Prerequisites**

* **Docker Desktop** (or Docker Engine) installed on your machine, or your own flavour of container tools. 

## **Setup**

1. **Create a Project Directory:** Create a new directory for your mock server (e.g., ss12000-mock-server).  
2. **Place Files:**  
   * Save the main.py code (from the ss12000-python-mock-server Canvas) as main.py in this directory.  
   * Save the Dockerfile code (from the Dockerfile for SS12000 Mock Server Canvas) as Dockerfile in the *same* directory.  
   * Save the requirements.txt content (from the requirements.txt for SS12000 Mock Server Canvas) as requirements.txt in the *same* directory.  
   * Save the docker-compose.yml code (from the Docker Compose for SS12000 Mock Server Canvas) as docker-compose.yml in the *same* directory.

Your directory structure should look like this:ss12000-test-server/  
├── main.py  
├── Dockerfile  
├── requirements.txt  
└── docker-compose.yml

## **Building and Running with Docker Compose (Recommended for Development)**

Docker Compose is ideal for development because it allows live reloading of your code changes without rebuilding the image.

1. Navigate to your project directory:  
   Open your terminal or command prompt and change the directory to ss12000-mock-server.  
   cd ss12000-mock-server

2. **Build and Run the services:**  
   docker-compose up \--build

   * \--build: This tells Docker Compose to build the image before starting the container. You only need to use this the first time or if you change the Dockerfile or requirements.txt.  
   * If you just want to start the containers after the first build, you can simply run docker-compose up.  
3. Access the API:  
   Once the container is running, open your web browser and go to:  
   * **Interactive API Documentation (Swagger UI):** http://localhost:8000/docs  
   * **Direct API Endpoints:** http://localhost:8000/organisations, http://localhost:8000/persons, etc.  
4. Stop the services:  
   To stop and remove the containers, networks, and volumes created by docker-compose up, press Ctrl+C in your terminal, then run:  
   docker-compose down

## **Building and Running with Docker (Manual)**

You can also build and run the Docker image manually without docker-compose. This is useful for understanding the underlying Docker commands or for single-container deployments.

1. **Navigate to your project directory** (as above).  
2. **Build the Docker image:**  
   docker build \-t ss12000-test-server .

   * \-t ss12000-mock-server: Tags the image with the name ss12000-mock-server.  
   * .: Specifies that the Dockerfile is in the current directory.  
3. **Run the Docker container:**  
   docker run \-p 8000:8000 ss12000-test-server

   * \-p 8000:8000: Maps port 8000 on your host machine to port 8000 inside the container.  
   * ss12000-mock-server: The name of the image to run.  
4. **Access the API:** (Same as above) http://localhost:8000/docs  
5. Stop the container:  
   To stop the running container, you'll need its container ID or name. You can find it with docker ps. Then run:  
   docker stop \<container\_id\_or\_name\>

   To remove it:  
   docker rm \<container\_id\_or\_name\>

Using Docker Compose is generally recommended for development as it simplifies the process of managing your services.