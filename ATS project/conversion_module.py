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

def extract_text_and_headings_from_pdf(file_bytes):
    doc = fitz.open("pdf", file_bytes)
    lines = []
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b['type'] == 0:  # text block
                for line in b["lines"]:
                    line_str = ""
                    max_fontsize = 0
                    for span in line["spans"]:
                        line_str += span["text"]
                        if span["size"] > max_fontsize:
                            max_fontsize = span["size"]
                    if line_str.strip():
                        lines.append((line_str.strip(), max_fontsize))
    return lines

def extract_text_and_headings_from_docx(docx_file):
    doc = Document(docx_file)
    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        max_fontsize = 0
        for run in para.runs:
            if run.font.size:
                # font.size is in Emu units; convert to points
                size_pt = run.font.size.pt if hasattr(run.font.size, 'pt') else run.font.size / 12700
                if size_pt > max_fontsize:
                    max_fontsize = size_pt
        lines.append((text, max_fontsize))
    return lines

def extract_text_and_headings(file_storage):
    ext = os.path.splitext(file_storage.filename)[1].lower()

    if ext == ".pdf":
        file_bytes = file_storage.read()
        return extract_text_and_headings_from_pdf(file_bytes)
    elif ext == ".docx":
        return extract_text_and_headings_from_docx(file_storage)
    elif ext == ".txt":
        text = file_storage.read().decode('utf-8')
        return [(line, 0) for line in text.splitlines()]
    return []
import re
def extract_section_items_with_fontsize(lines, section_keywords, fontsize_threshold=1.2):
    """
    Extracts lines from a resume section using font size and heading detection logic.
    """
    items = []
    collecting = False
    base_fontsize = None

    # Combined keyword list to detect transitions
    all_section_keywords = [
        "certifications", "certification", "professional certifications", "technical certifications",
        "projects", "project experience", "responsibilities", "work experience", "professional experience",
        "experience highlights", "career experience", "employment history", "project highlights",
        "education", "academic background", "educational qualifications", "academic qualifications",
        "academic details", "academic information", "educational background",
        "skills", "skill set", "core skills", "key skills", "areas of expertise", "expertise", "relevant skills",
        "technical skills", "technical expertise", "technical proficiencies", "technology stack", "tech stack",
        "technical summary", "technologies", "technical competencies", "tools and technologies",
        "development tools", "programming languages", "frameworks & technologies", "platforms",
        "software proficiency", "it skills", "programming skills", "software skills", "technology experience",
        "engineering skills", "professional skills", "summary of skills", "specialized skills", "it proficiency",
        "capabilities", "technical skills required"
    ]

    for i, (line, fsize) in enumerate(lines):
        line_strip = line.strip()
        if not line_strip:
            continue

        normalized_line = re.sub(r'^[•*o\-]+\s*', '', line_strip)

        # Start collecting if we match the section
        if not collecting:
            keyword_match = any(
                re.search(rf"\b{re.escape(kw)}\b", normalized_line, re.IGNORECASE)
                for kw in section_keywords
            )

            is_heading_by_font = False
            if fsize > 0:
                if base_fontsize is None:
                    base_fontsize = fsize
                elif fsize >= base_fontsize * fontsize_threshold:
                    is_heading_by_font = True

            if keyword_match or is_heading_by_font:
                collecting = True
                base_fontsize = fsize
                continue

        elif collecting:
            # Check if the current line is a heading-style line (stop signal)
            next_line_maybe_heading = (
                line_strip.isupper() or
                (re.match(r'^[A-Z][a-z]+(\s[A-Z][a-z]+)*[:]?$', normalized_line) and len(normalized_line.split()) <= 5)
            )

            # Or if next line is a known heading
            if i + 1 < len(lines):
                next_line, next_fsize = lines[i + 1]
                next_line_strip = next_line.strip()
                next_normalized = re.sub(r'^[•*o\-]+\s*', '', next_line_strip)

                next_keyword_match = any(
                    re.search(rf"\b{re.escape(kw)}\b", next_normalized, re.IGNORECASE)
                    for kw in all_section_keywords
                )

                next_is_heading_font = (
                    base_fontsize and next_fsize >= base_fontsize * fontsize_threshold
                )

                if next_keyword_match or next_is_heading_font:
                    break

            if next_line_maybe_heading:
                break

            # Keep only reasonable bullet lines (avoid paragraphs)
            if len(normalized_line.split()) <= 12:
                normalized_bullet = re.sub(r'^[•*o\-]+\s*', '- ', line_strip)
                if not normalized_bullet.startswith('- '):
                    normalized_bullet = '- ' + normalized_bullet
                items.append(normalized_bullet)

    return items


# def extract_section_items(text, section_keywords):
#     lines = text.split('\n')
#     items = []
#     collecting = False

#     for i, line in enumerate(lines):
#         line_strip = line.strip()
#         # Normalize bullets like •, o, * into a standard -
#         normalized_line = re.sub(r'^[•*o\-]+\s*', '', line_strip)  # remove leading bullets for matching

#         # Check if current line contains any of the section keywords
#         if not collecting and any(
#             re.search(rf"\b{re.escape(kw)}\b", normalized_line, re.IGNORECASE) for kw in section_keywords
#         ):
#             collecting = True
#             continue

#         if collecting:
#             # Stop if we hit another likely section heading
#             next_line_maybe_heading = (
#                 line_strip.isupper() or
#                 (re.match(r'^[A-Z][a-z]+(\s[A-Z][a-z]+)*[:]?$', normalized_line) and len(normalized_line.split()) <= 5)
#             )
#             if next_line_maybe_heading:
#                 break

#             # Normalize and capture as a bullet point
#             if line_strip:
#                 normalized_bullet = re.sub(r'^[•*o\-]+\s*', '- ', line_strip)
#                 if not normalized_bullet.startswith('- '):
#                     normalized_bullet = '- ' + normalized_bullet
#                 items.append(normalized_bullet)

#     return items


def format_resume(text):
    lines = extract_text_and_headings(text)

    cert_keywords = [
        "certifications", "certification", "professional certifications", "technical certifications"
    ]
    project_keywords = [
        "projects", "project experience", "responsibilities", "work experience", "professional experience",
        "experience highlights", "career experience", "employment history", "project highlights","Academic Project"
    ]
    education_keywords = [
        "education", "academic background", "educational qualifications", "academic qualifications",
        "academic details", "academic information", "educational background",
    ]
    skill_keywords = [
        "skills", "Skill Set", "core skills", "key skills", "areas of expertise", "expertise", "relevant skills",
        "technical skills", "technical expertise", "technical proficiencies", "technology stack", "tech stack",
        "technical summary", "technologies", "technical competencies", "tools and technologies",
        "development tools", "programming languages", "frameworks & technologies", "platforms",
        "software proficiency", "it skills", "programming skills", "software skills", "technology experience",
        "engineering skills", "professional skills", "summary of skills", "specialized skills", "it proficiency",
        "capabilities", "technical skills required"
    ]

    certs = extract_section_items_with_fontsize(lines, cert_keywords)
    projects = extract_section_items_with_fontsize(lines, project_keywords)
    education = extract_section_items_with_fontsize(lines, education_keywords)
    skills = extract_section_items_with_fontsize(lines, skill_keywords)

    formatted_resume = "Certifications\n"
    formatted_resume += "\n".join(certs) if certs else "No certifications found."
    formatted_resume += "\n\nProjects or Responsibilities\n"
    formatted_resume += "\n".join(projects) if projects else "No projects found."
    formatted_resume += "\n\nEducation\n"
    formatted_resume += "\n".join(education) if education else "No education info found."
    formatted_resume += "\n\nSkills\n"
    formatted_resume += "\n".join(skills) if skills else "No skills found."

    return formatted_resume


@conversion_bp.route('/upload', methods=['POST'])
def upload():
    jd_file = request.files.get("jd")
    resumes = request.files.getlist("resumes")

    if not jd_file or not resumes:
        return jsonify({"error": "Both JD and resumes are required"}), 400
    
    # Process JD
    #jd_text = extract_text_and_headings(jd_file)
    jd_text = format_resume(jd_file)
    jd_filename = os.path.splitext(jd_file.filename)[0] + "_formatted.txt"
    jd_path = os.path.join(JD_FOLDER, jd_filename)
    with open(jd_path, "w", encoding="utf-8") as f:
        f.write(jd_text)
    # Process Resumes
    saved_files = []
    for resume in resumes:
        #resume_text = extract_text_and_headings(resume)
        resume_text = format_resume(resume)
        formatted_name = os.path.splitext(resume.filename)[0] + "_formatted.txt"
        formatted_path = os.path.join(RESUME_FOLDER, formatted_name)
        with open(formatted_path, "w", encoding="utf-8") as f:
            f.write(resume_text)
        saved_files.append(formatted_name)

    return jsonify({
        "message": "Files formatted and saved",
        "jd_file": jd_filename,
        "resumes": saved_files
    })