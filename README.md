# Astermind AI Clone (Proof of Concept)

This project is a full-stack proof-of-concept application inspired by Astermind.ai. It focuses on identifying, reasoning about, and auditing security anomalies using simulated network traffic data.

## Features

*   **FastAPI Backend:** A robust backend built with Python and FastAPI.
*   **Anomaly Detection:** Built-in logic to identify anomalies in traffic and access patterns.
*   **Security Reasoning & Hypothesis:** Evaluates anomalies to generate hypotheses and security insights.
*   **Geolocation (GeoIP) Mocking:** Simulates IP geolocation lookups for analysis.
*   **Cryptographic Audit Chaining:** Secures logs with SHA-256 cryptographic chaining.
*   **Synthetic Traffic Simulator:** Generates mock network traffic and logs to test the systems.
*   **MCP Token Reduction:** Includes logic for context reduction.
*   **Dark-Mode Dashboard:** A responsive, console-style UI built with vanilla HTML, JS, Tailwind CSS, and Chart.js for visualizing metrics via Levey-Jennings control charts.

## Prerequisites

*   Python 3.10+
*   pip

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/wtfmanseriously/astermind-project.git
    cd astermind-project/backend
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  **Start the backend server:**
    Navigate to the `backend` directory and run:
    ```bash
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload
    ```

2.  **Access the Dashboard:**
    Open your web browser and navigate to:
    `http://localhost:8000/static/index.html`

## Running Tests

The application includes a comprehensive suite of `pytest` unit tests covering the core modules.

To run the tests, execute:
```bash
pytest
```
This will run all 14 tests across the detection, audit, detective, and MCP subsystems.

## Project Structure

*   `backend/app.py`: Main FastAPI application entry point.
*   `backend/detection.py`: Anomaly detection engine.
*   `backend/detective.py`: Security reasoning logic.
*   `backend/audit.py`: Cryptographic logging chain.
*   `backend/geoip.py`: IP lookup simulation.
*   `backend/simulator.py`: Traffic log generator.
*   `backend/static/`: Contains the frontend HTML (`index.html`) and JavaScript (`app.js`).
*   `backend/test_*.py`: Pytest files for various modules.
