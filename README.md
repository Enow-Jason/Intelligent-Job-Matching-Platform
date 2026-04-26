# Your project name here

# GradMatch AI

GradMatch AI is an AI-assisted job recommendation platform for job seekers, especially graduates and early-career users.

Users can create an account, save their profile, upload a CV/resume, and receive personalised job recommendations with match scores, explanation bullets, skill-gap insights, and detailed job information.

---

## Tech Stack

- Frontend: React + Vite + Tailwind CSS
- Backend: Spring Boot
- AI Microservice: FastAPI
- Database: MySQL
- NLP Model: Sentence Transformers (`all-MiniLM-L6-v2`)

---

## Folder Structure

```text
JobPlatform/
│
├── ai_service/                 # FastAPI AI recommendation service
├── data/
│   ├── raw/                    # Raw datasets
│   └── processed/              # Processed datasets and embeddings
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── layout/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── services/
├── notebooks/                  # Data prep, evaluation, and case-study notebooks
├── src/main/java/              # Spring Boot backend source
├── src/main/resources/         # Spring Boot config files
├── requirements.txt            # Python dependencies
├── build.gradle                # Gradle build file
└── README.md

# Requirements

Make sure the following are installed:

- Java 17
- Python 3.10+
- Node.js 18+
- npm
- MySQL 8+

# Python Environment for AI Service

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

# Running the Application

All three parts must be running.

## 1. Start the FastAPI AI Service

From the project root:

```bash
uvicorn ai_service.main:app --reload --host 0.0.0.0 --port 8000
```

## 2. Start the Spring Boot Backend

From the project root:

```powershell
.\gradlew.bat bootRun
```

This should run on:

- http://localhost:8080

## 3. Start the React Frontend

```bash
cd frontend
npm install
npm run dev
```

This should run on:

- http://localhost:5173

# Database Setup

Create a MySQL database, for example:

```sql
CREATE DATABASE jobplatform;
```

Then update your Spring Boot database configuration in `application.properties` or `application.yml` with your local MySQL username, password, and database name.

# Main Features

- User sign up and sign in
- Profile persistence with MySQL
- Password update
- Resume/CV upload
- AI-powered job recommendations
- Experience-aware reranking
- Personalised recommendation explanations
- Saved jobs / bookmarks
- Sorting, filtering, and pagination
- Theme support
