import base64
import csv
import json
import os
import random
import string

import fitz  # PyMuPDF
import googleapiclient.discovery
import googleapiclient.errors
import requests
from flask import Flask, render_template, redirect, request, session, url_for, flash
from mistralai import Mistral

# Firebase REST API for Authentication
FIREBASE_WEB_API_KEY = "AIzaSyD7ks5VJzVrgZDoIMbx-4Ja3MwPVPeQA3Q"

def firebase_signup(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)
    return response.json()

def firebase_login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)
    return response.json()

app = Flask(__name__)
app.secret_key = "Qazwsx@123"

# Mistral setup
mistral_api_key = "WTuMOibXWmpTqjvscYHSaaCOjjXCakkJ"
mistral_model = "pixtral-large-2411"
try:
    client = Mistral(api_key=mistral_api_key)
    print("Mistral initialized")
except Exception as e:
    print("Mistral init failed:", e)
    client = None

# Adzuna keys
ADZUNA_APP_ID = "b03f76e8"
ADZUNA_APP_KEY = "3aba17aaa08c6bd408d4f71350fa835a"

# YouTube API
YOUTUBE_API_KEY = "AIzaSyCWQ5BsUYN7IG2wreRvDt5L8KEwmPbY9vQ"
try:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
except:
    youtube = None

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

def encode_image(img):
    with open(img, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def pdf_to_images(pdf_path, out_folder):
    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(2, 2)
    images = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat)
        img_path = os.path.join(out_folder, f"page_{i+1}.png")
        pix.save(img_path)
        images.append(img_path)
    doc.close()
    return images

def extract_keywords_from_image(img):
    if not client:
        return []
    img64 = encode_image(img)
    prompt = "Extract JSON of resume keywords: technologies, frameworks, languages, job roles."
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": f"data:image/png;base64,{img64}"}]}]
    try:
        res = client.chat.complete(model=mistral_model, messages=messages, response_format={"type": "json_object"})
        content = json.loads(res.choices[0].message.content)
        return content.get("keywords", [])
    except:
        return []

def analyze_skill_gap(resume_skills, job_title):
    """Uses Mistral to analyze the skill gap between resume and job title."""
    if not client:
        print("Mistral client not initialized. Cannot analyze skill gap.")
        return {"missing_skills": [], "analysis": ""}

    prompt = (
        f"Analyze the skill gap between these resume skills: {resume_skills} "
        f"and this target job title: {job_title}. "
        "Return a JSON object with two keys: "
        "'missing_skills' (list of skills needed for the job but not in resume), "
        "'analysis' (a brief text analysis of the gap). "
        "Example: {\"missing_skills\": [\"AWS\", \"Docker\"], \"analysis\": \"The resume lacks cloud and containerization skills...\"}"
    )

    try:
        response = client.chat.complete(
            model=mistral_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"Error analyzing skill gap: {e}")
        return {"missing_skills": [], "analysis": ""}

def get_youtube_tutorials(keywords, max_results=1):
    tutorials = {}
    if not youtube:
        return tutorials
    for kw in keywords:
        try:
            search = youtube.search().list(q=f"{kw} tutorial", part="id,snippet", maxResults=max_results, type="video").execute()
            for item in search.get("items", []):
                vid = item["id"].get("videoId")
                title = item["snippet"].get("title")
                if vid:
                    tutorials[kw] = [{"title": title, "link": f"https://www.youtube.com/watch?v={vid}"}]
        except:
            continue
    return tutorials

def get_clickable_tutorials_from_file(missing_skills, filepath="final_clickable.csv"):
    links = {}
    try:
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                skill = row['GUI Development'].strip().lower()
                link = row['YouTube Link'].strip()
                for ms in missing_skills:
                    if ms.lower() == skill:
                        links[ms] = [{"title": f"{ms} Tutorial", "link": link}]
    except:
        pass
    return links

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ulogin", methods=["GET", "POST"])
def ulogin():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        resp = firebase_login(email, password)
        if 'idToken' in resp:
            session['user'] = resp['email']
            session['username'] = resp['email'].split('@')[0]
            return redirect(url_for('userhome'))
        else:
            flash("Login failed: " + resp.get('error', {}).get('message', 'Unknown error'), 'danger')
    return render_template("ulogin.html")

@app.route("/uregister", methods=["GET", "POST"])
def uregister():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        resp = firebase_signup(email, password)
        if 'idToken' in resp:
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("ulogin"))
        else:
            flash("Registration failed: " + resp.get('error', {}).get('message', 'Unknown error'), 'danger')
    return render_template("uregister.html")

@app.route("/userhome")
def userhome():
    if 'user' not in session:
        return redirect(url_for("ulogin"))
    return render_template("userhome.html", username=session.get("username"))

@app.route("/ulogout")
def ulogout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("ulogin"))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if 'user' not in session:
        return redirect(url_for("ulogin"))

    if request.method == "GET":
        return render_template("upload.html")

    job = request.form.get("job_designation")
    file = request.files.get("file")
    if not job or not file:
        flash("All fields required", "warning")
        return redirect(url_for("upload"))

    temp_dir = os.path.join("workspace", "u_" + ''.join(random.choices(string.ascii_lowercase, k=8)))
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)
    file.save(file_path)
    imgs = pdf_to_images(file_path, temp_dir)

    all_keywords = set()
    for img in imgs:
        kws = extract_keywords_from_image(img)
        all_keywords.update([k.strip().lower() for k in kws])
    all_keywords = sorted(list(all_keywords))

    skill_gap_result = analyze_skill_gap(all_keywords, job)
    missing = skill_gap_result.get("missing_skills", [])
    all_keywords.extend(missing)

    job_results = []
    for kw in random.sample(all_keywords, min(len(all_keywords), 3)):
        url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}&results_per_page=1&what={kw}&where=bengaluru"
        try:
            r = requests.get(url)
            job_data = r.json().get('results', [])
            job_results.extend(job_data)
        except:
            continue
    job_results = job_results[:4]

    video_tutorials = get_youtube_tutorials(all_keywords)
    clickable_links = get_clickable_tutorials_from_file(missing)
    video_tutorials.update(clickable_links)

    return render_template("upload.html",
        job_results=job_results,
        video_tutorials=video_tutorials,
        keywords_found=all_keywords,
        skill_gap_analysis=skill_gap_result)

if __name__ == "__main__":
    if not os.path.exists("workspace"):
        os.makedirs("workspace")
    app.run(debug=True)
