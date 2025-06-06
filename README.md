# ATS Resume Scanner

A web-based Applicant Tracking System (ATS) Resume Scanner built with Flask. This project allows users to upload multiple resumes and a job description (JD), then analyzes and scores each resume based on skill match, certifications, projects, and experience using NLP (spaCy) and PDF/DOCX parsing.

---

## Features

- Upload multiple resumes (PDF, DOCX, TXT) and a job description.
- Extracts and matches skills, certifications, projects, and experience from resumes.
- Uses spaCy's `en_core_web_lg` model for advanced NLP.
- Scores and ranks resumes based on JD requirements.
- User-friendly web interface built with HTML, CSS, and JavaScript.
- RESTful API endpoints for integration.

---

## Project Structure

```
ATS project/
│
├── app/
│   ├── jdfolder/
│   └── resumes/
├── static/
│   ├── styles.css
│   └── Scripts.js
├── templates/
│   └── index.html
├── conversion_module.py
├── scoring_module.py
├── main.py
├── requirements.txt
└── README.md
```

---

## Installation

1. **Clone the repository:**
   ```
   git clone https://github.com/lellur/ATS.git
   cd ATS\ project
   ```

2. **Create and activate a virtual environment (recommended):**
   ```
   python -m venv venv
   venv\Scripts\activate   # On Windows
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Download spaCy language model:**
   ```
   python -m spacy download en_core_web_lg
   ```

---

## Usage

1. **Start the Flask server:**
   ```
   python main.py
   ```

2. **Open your browser and go to:**
   ```
   http://127.0.0.1:5000/
   ```

3. **Upload resumes and a JD, and view the ATS scan results.**

---

## API Endpoints

- `POST /api/upload`  
  Upload resumes and JD for processing.

- `GET /api/score`  
  Get scoring and analysis results for uploaded resumes.

---

## Requirements

See [`requirements.txt`](requirements.txt) for all dependencies.

---

## Notes

- Place your static files (CSS/JS) in the `static/` folder.
- Place your HTML templates in the `templates/` folder.
- Temporary and processed files are stored in `app/jdfolder/` and `app/resumes/`.

---

## License

MIT License

---

## Acknowledgements

- [spaCy](https://spacy.io/)
- [Flask](https://flask.palletsprojects.com/)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [python-docx](https://python-docx.readthedocs.io/)