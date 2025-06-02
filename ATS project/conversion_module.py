from flask import Blueprint, request, jsonify
import os
import re
from docx import Document
import fitz  # PyMuPDF

conversion_bp = Blueprint('conversion_bp', __name__)
UPLOAD_FOLDER = 'temp_uploads'
JD_FOLDER = 'app/jdfolder'
RESUME_FOLDER = 'app/resumes'
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(JD_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_lines(file_storage):
    ext = os.path.splitext(file_storage.filename)[1].lower()

    if ext == ".pdf":
        doc = fitz.open("pdf", file_storage.read())
        text = "\n".join(page.get_text() for page in doc)
    elif ext == ".docx":
        doc = Document(file_storage)
        text = "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
    elif ext == ".txt":
        text = file_storage.read().decode('utf-8')
    else:
        text = ""

    return text.splitlines()

def extract_section_items(text, section_keywords):
    lines = text.split('\n')
    items = []
    collecting = False

    for i, line in enumerate(lines):
        line_strip = line.strip()

        # Normalize bullets and lowercase
        line_no_bullet = re.sub(r'^[•*o\-]+\s*', '', line_strip).strip().lower()

        # Check if line is exactly a keyword or starts with it
        if not collecting and any(
            line_no_bullet == kw.lower() or line_no_bullet.startswith(kw.lower())
            for kw in section_keywords
        ):
            collecting = True
            continue

        if collecting:
            # If the current line looks like a new section header, but ISN'T a bullet, stop
            no_bullet = re.sub(r'^[•*o\-]+\s*', '', line_strip).strip()
            is_heading_like = (
                no_bullet.isupper() or
                (re.match(r'^[A-Z][a-z]+(\s[A-Z][a-z]+)*[:]?$', no_bullet) and len(no_bullet.split()) <= 5)
            )
            if is_heading_like and not re.match(r'^[•*o\-]', line_strip):
                break

            # Append the line as a bullet point
            if line_strip:
                normalized_bullet = re.sub(r'^[•*o\-]+\s*', '- ', line_strip)
                if not normalized_bullet.startswith('- '):
                    normalized_bullet = '- ' + normalized_bullet
                items.append(normalized_bullet)

    return items



def format_resume(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    cert_keywords = [
        "certifications", "certification", "professional certifications", "technical certifications"
    ]
    project_keywords = [
        "projects", "project experience", "responsibilities", "work experience", "professional experience",
        "experience highlights", "career experience", "employment history", "project highlights"
    ]
    experience_keywords = [
        "experience", "work experience", "professional experience", "employment history", "career summary",
        "job experience", "work history", "relevant experience", "project experience"
    ]
    skill_keywords = [
        "skills", "skill set", "core skills", "key skills", "areas of expertise", "expertise", "relevant skills",
        "technical skills", "technical expertise", "technical proficiencies", "technology stack", "tech stack",
        "technical summary", "technologies", "technical competencies", "tools and technologies",
        "development tools", "programming languages", "frameworks & technologies", "platforms",
        "software proficiency", "it skills", "programming skills", "software skills", "technology experience",
        "engineering skills", "professional skills", "summary of skills", "specialized skills", "it proficiency",
        "capabilities", "technical skills required"
    ]

    certs = extract_section_items(text, cert_keywords)
    projects = extract_section_items(text, project_keywords)
    experience = extract_section_items(text, experience_keywords)
    skills = extract_section_items(text, skill_keywords)

    formatted_resume = "Certifications\n"
    formatted_resume += "\n".join(certs) if certs else "No certifications found."
    formatted_resume += "\n\nProjects or Responsibilities\n"
    formatted_resume += "\n".join(projects) if projects else "No projects found."
    formatted_resume += "\n\nExperience\n"
    formatted_resume += "\n".join(experience) if experience else "No experience info found."
    formatted_resume += "\n\nSkills\n"
    formatted_resume += "\n".join(skills) if skills else "No skills found."

    return formatted_resume

@conversion_bp.route('/upload', methods=['POST'])
def upload():
    jd_file = request.files.get("jd")
    resumes = request.files.getlist("resumes")

    if not jd_file or not resumes:
        return jsonify({"error": "Both JD and resumes are required"}), 400

    # Extract JD text
    jd_lines = extract_text_lines(jd_file)
    jd_text = "\n".join(jd_lines)
    jd_formatted = format_resume(jd_text)

    jd_filename = os.path.splitext(jd_file.filename)[0] + "_formatted.txt"
    jd_path = os.path.join(JD_FOLDER, jd_filename)
    with open(jd_path, "w", encoding="utf-8") as f:
        f.write(jd_formatted)

    saved_files = []
    for resume in resumes:
        resume_lines = extract_text_lines(resume)
        resume_text = "\n".join(resume_lines)
        resume_formatted = format_resume(resume_text)

        formatted_name = os.path.splitext(resume.filename)[0] + "_formatted.txt"
        formatted_path = os.path.join(RESUME_FOLDER, formatted_name)
        with open(formatted_path, "w", encoding="utf-8") as f:
            f.write(resume_formatted)

        saved_files.append(formatted_name)

    return jsonify({
        "message": "Files formatted and saved",
        "jd_file": jd_filename,
        "resumes": saved_files
    })
