## Project Setup and Execution Guide

### 1. Prerequisites

- Install **Docker Desktop** (used to run the MySQL database).
- Install **Python 3.11** (required to run the Flask application).
- Install **Visual Studio Code** or any terminal-based editor.

### Step 1: Start the Database using Docker

- Open Docker Desktop.
- Navigate to the **Containers** section.
- Locate the container named **meal_mysql**.
- Click the **Start (▶)** button to run the container.
- Ensure the container is running with port mapping **3308 → 3306**.
- This container runs a **MySQL 8** database used by the application.
- The Flask application will not work unless this container is running.

### Step 2: Open the Project in Visual Studio Code

- Open Visual Studio Code.
- Open the project folder (**meal_app**) in VS Code.
- Open a new terminal inside VS Code.

### Step 3: Set Up the Python Virtual Environment

- Navigate to the project root directory in the terminal.
- Create a virtual environment using Python 3.11:

  py -3.11 -m venv .venv

- Activate the virtual environment (Windows):

  .venv\Scripts\activate

- Once activated, the terminal prompt will show **(.venv)**.

### Step 4: Configure Flask Environment Variables

- Set the Flask application entry point:

  set FLASK_APP=wsgi

- Enable development mode:

  set FLASK_ENV=development

### Step 5: Run the Application

- Start the Flask development server:

  flask run

- The application will start running locally.
- Open a browser and go to:

  http://127.0.0.1:5000
