from flask import Flask, jsonify
import os
import re
import pdfplumber
from docx import Document
import spacy
from dateutil import parser
from datetime import datetime

from flask import Blueprint, jsonify
import os

scoring_bp = Blueprint('scoring_bp', __name__)

app = Flask(__name__)

# --- Configuration ---
BASE_DIR = 'app'
JD_FOLDER = os.path.join(BASE_DIR, 'jdfolder')
RESUME_FOLDER = os.path.join(BASE_DIR, 'resumes')

#sap_skills = ["General Ledger", "Accounts Payable", "S/4HANA", "SAP Security", "Authorization", "PFCG", "GRC", "Fiori", "BAPI", "MM", "SD", "FI", "CO"]

# --- Utility Functions ---
def clean_text(text):
    return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())

#extraction of matched skills

# Load medium-sized spaCy model for semantic similarity
nlp = spacy.load("en_core_web_lg")

# Step 1: Extract "Skills" section
def extract_skills_section(text):
    lines = text.splitlines()
    skills_lines = []
    capture = False

    for line in lines:
        stripped = line.strip()
        # Start capturing after "Skills" heading
        if re.match(r'(?i)^skills\s*[:\-]?\s*$', stripped):
            capture = True
            continue
        # Stop capturing when another heading or empty line appears
        if capture:
            if re.match(r'^[A-Z][a-zA-Z\s]*$', stripped) or stripped == "":
                break
            skills_lines.append(stripped)

    return "\n".join(skills_lines)
# Step 2: Parse bullet points into a list of skills
def parse_bullet_skills(section_text):
    lines = section_text.splitlines()
    return [
        re.sub(r"^[•\-–\*\d\.\)\s]*", "", line.strip()).lower()
        for line in lines
        if line.strip()
    ]

# Step 3: Match skills using spaCy similarity
def match_skills(jd_skills, resume_skills, threshold=0.7):
    matched=[]
    for jd_skill in jd_skills:
        jd_vec = nlp(jd_skill)
        for res_skill in resume_skills:
            res_vec = nlp(res_skill)
            if jd_vec.similarity(res_vec) >= threshold:
                if res_skill not in matched:
                    matched.append(res_skill)
    return matched




def extract_keywords(text, keyword_list):
    text = clean_text(text)
    return [kw for kw in keyword_list if kw.lower() in text]

def count_certifications(text):
    lines = text.splitlines()
    cert_count = 0
    capture = False
    # Define the stop keyword/section heading
    stop_keywords = ["Projects or Responsibilities", "projects", "responsibilities"]

    for line in lines:
        line_strip = line.strip()
        lower = line_strip.lower()

        # Start capturing when "certifications" appears
        if not capture and re.match(r'^certifications?:?$', lower):
            capture = True
            continue

        if capture:
            # Stop capturing if a stop keyword appears
            if any(kw in lower for kw in stop_keywords):
                break
            if "no certifications found" in lower:
                continue
            # Count if it's a bullet point or a valid certification-looking line
            if re.match(r'^[-•*]\s+', line_strip) or len(line_strip) > 5:
                cert_count += 1

    return cert_count

DESCRIPTION_KEYWORDS = [
    "developed", "implemented", "designed", "customized", "enhanced", "configured",
    "created", "built", "optimized", "tested", "supported", "migrated", "maintained",
    "debugged", "integrated", "performed", "remediated", "upgraded", "analyzed",
    "documented", "refactored", "deployed", "delivered"
]

PROJECT_SECTION_KEYWORDS = [
    r'project\s*\d+', r'project[#:\-]?\s*\d+', r'project\s*name', r'assignment', r'client\s*work'
]

def count_projects(text):
    lines = text.splitlines()
    return sum(
        1 for i in range(len(lines) - 1)
        if re.match(r"^project\s*#?\d*[:\-]?", lines[i].strip(), re.IGNORECASE)
        and re.search(r"^role\s*[:\-]", lines[i+1], re.IGNORECASE)
    )
def extract_experience_years(text):
    match = re.search(r'(\d{1,2})\+?\s*(years|yrs)\b.*?\b(experience|expertise)?', text.lower())
    return int(match.group(1)) if match else 0
def calculate_score(matched_skills, jd_skills, certs, projects, exp):
    # Weight distribution
    max_skill_weight = 40
    max_cert_weight = 10
    max_proj_weight = 30
    max_exp_weight = 20

    # Skills (proportional to JD)
    skill_score = (len(matched_skills) / len(jd_skills)) * max_skill_weight if jd_skills else 0

    # Certifications (max 3 = 10 points)
    cert_score = min(certs, 3) / 3 * max_cert_weight

    # Projects (max 8 = 30 points)
    proj_score = min(projects, 8) / 8 * max_proj_weight

    # Experience (bucketed)
    if exp <= 5:
        exp_score = 5
    elif 6 <= exp <= 10:
        exp_score = 10
    elif 11 <= exp <= 15:
        exp_score = 15
    else:
        exp_score = 20

    total_score = skill_score + cert_score + proj_score + exp_score
    return round(total_score, 2)


def read_file(path):
    if path.endswith('.txt'):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    elif path.endswith('.pdf'):
        with pdfplumber.open(path) as pdf:
            return '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())
    elif path.endswith('.docx'):
        doc = Document(path)
        return '\n'.join([para.text for para in doc.paragraphs])
    else:
        return ''

# --- Flask Route ---
@scoring_bp.route('/score', methods=['GET'])
def process_folder():
    jd_files = [f for f in os.listdir(JD_FOLDER) if f.endswith(('.pdf', '.docx', '.txt'))]
    if not jd_files:
        return jsonify({"error": "No JD file found in jdfolder"}), 404

    jd_path = os.path.join(JD_FOLDER, jd_files[0])
    jd_text = read_file(jd_path)
    jd_section = extract_skills_section(jd_text)
    jd_skills = parse_bullet_skills(jd_section)

    results = []
    for filename in os.listdir(RESUME_FOLDER):
        filepath = os.path.join(RESUME_FOLDER, filename)
        if not os.path.isfile(filepath) or not filepath.endswith(('.pdf', '.docx', '.txt')):
            continue

        resume_text = read_file(filepath)
        resume_section = extract_skills_section(resume_text)
        resume_skills = parse_bullet_skills(resume_section)
        resume_skills = match_skills(jd_skills, resume_skills)
        certs = count_certifications(resume_text)
        projects = count_projects(resume_text)
        exp_years = extract_experience_years(resume_text)
        score = calculate_score(resume_skills, jd_skills, certs, projects, exp_years)

        results.append({
            'Resume': filename,
            'Matched Skills': resume_skills,
            'Certifications': certs,
            'Projects': projects,
            'Experience (Years)': exp_years,
            'Score': score
        })
    jd_name = jd_files[0]

    # Delete files after processing
    try:
        os.remove(jd_path)
        for filename in os.listdir(RESUME_FOLDER):
            filepath = os.path.join(RESUME_FOLDER, filename)
            if os.path.isfile(filepath):
                os.remove(filepath)
    except Exception as e:
        print(f"Error deleting files: {e}")

    return jsonify({
        "JD File": jd_name,
        "JD Skills": jd_skills,
        "Results": results
    })
# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)
