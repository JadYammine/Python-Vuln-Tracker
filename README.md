# Python Vulnerability Tracker

A FastAPI-based service to track vulnerabilities in Python project dependencies using the osv.dev API.

## Features
- Create and manage Python projects with name, description, and requirements.txt upload
- List all projects and identify vulnerable ones
- Retrieve dependencies for a project and highlight vulnerabilities
- List all dependencies across projects and show their vulnerability status
- Get details about a specific dependency, including usage and associated vulnerabilities
- Optimized API response time with caching for osv.dev queries

## Tech Stack
- Python 3.11
- FastAPI
- Uvicorn
- Poetry for dependency management
- Docker & Docker Compose for containerization
- Pydantic for data validation
- httpx for HTTP requests

## Getting Started

### Testing
To run the test suite from your host (no need to bash into the container):

```
./run.test.sh
```

This will execute all tests and print a summary.

### Development
1. Build and run the development container:
   ```
   ./run.dev.sh
   ```
   - Hot-reload enabled
   - Debugpy available on port 5678

### Production
1. Build and run the production container:
   ```
   ./run.sh
   ```

### API Endpoints
- `POST /projects` - Create a new project
- `GET /projects` - List all projects and highlight vulnerable ones
- `GET /projects/{project_id}/dependencies` - List dependencies for a project and show vulnerabilities
- `GET /dependencies` - List all dependencies and their vulnerability status
- `GET /dependencies/{dependency_name}` - Get details about a specific dependency

## Design Decisions
- In-memory storage for simplicity
- osv.dev API used for real-time vulnerability data
- Caching implemented to optimize response times and reduce redundant API calls

## Contributing
Feel free to fork and submit pull requests. All contributions are welcome!

