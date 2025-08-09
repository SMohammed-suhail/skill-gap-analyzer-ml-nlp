# skill-gap-analyzer-ml-nlp
An AI-powered web app for skill gap analysis and personalized training recommendations using Machine Learning and NLP technique. Users upload resumes, and the system extracts skills, compares them with desired job roles, identifies missing skills, and suggests tutorials and job listings. Built with Flask and Firebase.
click here to see live demo:https://skill-gap-analyzer-ml-nlp.onrender.com
# Skill Gap Analysis Web Application

A Flask-based web application that analyzes resume skills, identifies missing skills for a target job role, and recommends job listings and tutorials.  
The app integrates **Mistral AI**, **YouTube API**, and **Adzuna API** for AI-powered skill extraction, analysis, and content recommendations.

## Features
- **User Authentication** with Firebase (Sign Up / Sign In / Logout)
- **Resume Upload** (PDF to images via PyMuPDF)
- **Skill Extraction** from resume using Mistral AI
- **Skill Gap Analysis** between resume and target job
- **Job Recommendations** from Adzuna API
- **Video Tutorials** from YouTube API
- **Clickable Tutorial Links** from pre-saved CSV

## Tech Stack
- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, Bootstrap
- **Database**: Firebase Authentication (NoSQL for user auth)
- **APIs**:
  - Mistral AI (Skill extraction & gap analysis)
  - Adzuna (Job search)
  - YouTube Data API (Tutorial recommendations)
- Libraries:
  - `flask`
  - `pymupdf`
  - `google-api-python-client`
  - `requests`
  - `mistralai`

## Project Structure
├── app.py # Main Flask application
├── templates/ # HTML templates
├── static/ # CSS, JS, and assets
├── requirements.txt # Python dependencies
├── README.md # Project documentation
└── final_clickable.csv # Pre-saved tutorial links
run:
python app.py

