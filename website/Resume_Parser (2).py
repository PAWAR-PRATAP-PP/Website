from flask import Flask, request, jsonify
import json
import re
import requests
from docx import Document
import PyPDF2
import gender_guesser.detector as gender
import face_recognition
#import cv2
import os
import numpy as np
import spacy
from datetime import datetime, timedelta
from dateutil import parser
from dotenv import load_dotenv
from openai import OpenAI
import nltk

nltk.download('stopwords')

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OpenAIKey", "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"))

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")

PREDEFINED_SKILLS = set()

# ----------- Resume Parser Functions -----------

def rrf_data(rrfid):
    session_url = f"https://test207.ekatm.co.in/api/LoginApi/GenerateToken?UserLoginId=300022&Password=123&PlantId=1"
    rrf_url = f"https://test207.ekatm.co.in/api/RecruitmentFormAPI/getFillRRFView?rrfId={rrfid}"

    with requests.Session() as session:
        headers = {'Cookie': 'ASP.NET_SessionId=a42gx5atqxhgc20lnm12xb4r'}
        response = session.get(session_url, headers=headers)
        if response.status_code == 200:
            session_key = response.json()
        else:
            raise ConnectionError(f"Failed to establish session: {response.status_code}")
        headers['Authorization'] = f'Bearer {session_key}|300022|1'
        response = session.get(rrf_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
        else:
            raise ConnectionError(f"Failed to retrieve RRF data: {response.status_code}")
        data = json.loads(data)
        skills = [item.get("SkillSet") for item in data.get('_dtSkills', []) if item.get("SkillSet")]
        experience = data.get('_dtDetails', [{}])[0].get('TotalExp', 0)
    return skills, experience

def process_file(file_path):
    text = ''
    if file_path.endswith('.pdf'):
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() or ''
    elif file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    elif file_path.endswith('.docx'):
        doc = Document(file_path)
        text = ' '.join([p.text for p in doc.paragraphs])
    return text

def extract_name(text):
    name_pattern = r'^[A-Z][a-zA-Z\s-]+(?:\s[A-Z][a-zA-Z\s-]+)*'
    match = re.search(name_pattern, text, re.MULTILINE)
    if match:
        full_name = match.group(0).strip()
        name_parts = full_name.split()
        return name_parts[0], ' '.join(name_parts[1:2]) if len(name_parts) > 1 else None
    return "Name not found", None

def extract_emails(text):
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, re.sub(r'CONTACT', '', text))

def extract_phone_numbers(text):
    text = text.replace(" ", "")
    pattern = r'\+?[0-9]{1,4}[ -]?[0-9]{1,4}[ -]?[0-9]{4,15}|\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}'
    return [re.sub(r'[^\d+]', '', number) for number in re.findall(pattern, text)]

def extract_experience(text):
    patterns = [
        r'(\d+(\.\d+)?)\s?year[s]?\s?experience',
        r'(\d+(\.\d+)?)\s?yr[s]?\s?experience'
    ]
    years = 0
    for pattern in patterns:
        for match in re.findall(pattern, text, re.IGNORECASE):
            try: years += float(match[0])
            except: pass
    return round(years, 1)

def get_gender_from_name(first_name):
    d = gender.Detector()
    g = d.get_gender(first_name.strip())
    return "Male" if g in ['male', 'mostly_male'] else "Female" if g in ['female', 'mostly_female'] else "Unknown"

def calculate_skill_match(extracted_skills, required_skills):
    es = set(map(str.lower, extracted_skills))
    rs = set(map(str.lower, required_skills))
    matched = [s for s in rs if s.lower() in es]
    return round((len(matched) / len(rs)) * 100, 2) if rs else 0, matched

@app.route('/resume_parser', methods=['POST'])
def process_resume():
    data = request.json
    file_path, rrfid = data.get('file_path'), data.get('rrfid')
    if not file_path or not rrfid:
        return jsonify({'error': 'Missing file_path or rrfid'}), 400

    rrf_skills, rrf_experience = rrf_data(rrfid)
    PREDEFINED_SKILLS.update(rrf_skills)

    try:
        text = process_file(file_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    first_name, last_name = extract_name(text)
    emails = extract_emails(text)
    phones = extract_phone_numbers(text)
    experience = extract_experience(text)
    extracted_skills = [s for s in PREDEFINED_SKILLS if s.lower() in text.lower()]
    skill_match, matched = calculate_skill_match(extracted_skills, PREDEFINED_SKILLS)

    return jsonify({
        'NAME': first_name,
        'SURNAME': last_name,
        'EMAIL': ', '.join(emails),
        'GENDER': get_gender_from_name(first_name),
        'PHONE': ', '.join(phones),
        'experience': experience,
        'skill_match_percentage': skill_match,
        'matching_skills': ', '.join(matched),
    })

# ----------- Face Recognition Functions -----------

KNOWN_FACES_FOLDER = "D:\\MyWork\\saved_images"

def load_known_faces(folder):
    encodings, names = [], []
    for f in os.listdir(folder):
        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
            img = face_recognition.load_image_file(os.path.join(folder, f))
            enc = face_recognition.face_encodings(img)
            if enc:
                encodings.append(enc[0])
                names.append(f)
    return encodings, names

def recognize_face(image_path):
    known_encodings, known_names = load_known_faces(KNOWN_FACES_FOLDER)
    if not known_encodings:
        return {"error": "No known faces loaded."}

    image = face_recognition.load_image_file(image_path)
    input_enc = face_recognition.face_encodings(image)
    if not input_enc:
        return {"error": "No face found in the input image."}

    input_encoding = input_enc[0]
    results = face_recognition.compare_faces(known_encodings, input_encoding)
    distances = face_recognition.face_distance(known_encodings, input_encoding)

    if results and any(results):
        idx = np.argmin(distances)
        return {
            "matched_name": known_names[idx],
            "matching_percentage": round(100 - (distances[idx] * 100), 2)
        }
    return {"match_found": False}

@app.route('/face_recognition', methods=['POST'])
def face_recognition_api():
    data = request.json
    path = data.get('input_image_path')
    if not path:
        return jsonify({'error': 'Missing input_image_path'}), 400
    try:
        return jsonify(recognize_face(path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ----------- Expense Claim Extraction -----------

def remove_quotes_around_numbers(text):
    return re.sub(r'"(\d+)"', r'\1', text)


def extract_date(text):
    try:
        date_pattern = r"(\d{2}[./-]\d{2}[./-]\d{4})"
        match = re.search(date_pattern, text)
        if match:
            date_str = match.group(0).replace("/", "-").replace(".", "-")
            return date_str
        else:
            doc = nlp(text)
            current_date = datetime.now().date()
            previous_date = current_date - timedelta(days=1)

            for ent in doc.ents:
                if ent.label_ == "DATE":
                    try:
                        if ent.text.lower() == "today":
                            return str(current_date)
                        elif ent.text.lower() == "yesterday":
                            return str(previous_date)
                        else:
                            return str(parser.parse(ent.text, fuzzy=True).date())
                    except Exception:
                        continue
    except Exception:
        pass
    return str(datetime.now().date())


def decide_mode(mode_of_travel):
    if not mode_of_travel or mode_of_travel.lower() == "none":
        return None, None
    mode_of_travel = mode_of_travel.lower()
    if mode_of_travel in ["car", "four wheeler", "4 wheeler"]:
        return "4 wheeler", "car"
    elif mode_of_travel in ["airplane", "aeroplane", "plane", "flight", "air"]:
        return "none", "airplane"
    elif mode_of_travel in ["bike", "two wheeler", "2 wheeler", "scooty"]:
        return "2 wheeler", "bike"
    return "none", mode_of_travel


def extract_strings_between_braces(input_string):
    return re.findall(r'\{([^}]+)\}', input_string)


def enclose_in_curly_braces(input_string):
    if not input_string.startswith("{"):
        input_string = "{" + input_string
    if not input_string.endswith("}"):
        input_string = input_string + "}"
    return input_string


@app.route('/claim_expenses', methods=['POST'])
def claim_expenses():
    try:
        data = request.get_json()
        value = data.get("value", "")

        if len(value) < 25:
            return jsonify({
                "start_location": 'null',
                "end_location": 'null',
                "date": 'null',
                "mode": 'null',
                "vehicle": 'null',
                "payment": 'null',
                "expenses": [
                    {"travelling": 'null'},
                    {"lodging": 'null'},
                    {"food": 'null'},
                    {"maintenance": 'null'},
                    {"laundry": 'null'},
                    {"phone": 'null'},
                    {"entertainment": 'null'},
                    {"tips": 'null'},
                    {"other": 'null'},
                ]
            })

        system_message = {
            "role": "system",
            "content": (
                "You are an assistant that extracts structured expense data from text. "
                "Respond only with a JSON object with keys: START, END, LODGING, MODE, PAYMENT, FOOD, TRAVEL, "
                "MAINTENANCE, LAUNDRY, PHONE, OTHER, ENTERTAINMENT, TIPS. "
                "Use integers for expense values or null if not mentioned. "
                "Do not add any explanations or extra text."
            )
        }

        user_message = {
            "role": "user",
            "content": (
                f"Extract the expenses and travel details from the following sentence:\n\"{value}\"\n"
                "If any field is missing, use null."
            )
        }

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[system_message, user_message],
            max_tokens=300,
            temperature=0.0,
        )

        parsed_text = response.choices[0].message.content.strip()
        # Remove quotes around numbers if any
        cleaned_text = remove_quotes_around_numbers(parsed_text)

        
        within_brackets = extract_strings_between_braces(cleaned_text)
        if within_brackets:
            cleaned_text = "{" + within_brackets[0] + "}"

        
        cleaned_text = enclose_in_curly_braces(cleaned_text)

        data = json.loads(cleaned_text)

        mode_of_journey,vehicle_type = decide_mode(data.get("MODE"))

        response_data = {
            "start_location": data.get("START", 'null'),
            "end_location": data.get("END", 'null'),
            "date": extract_date(value),
            "mode": mode_of_journey,
            "vehicle": vehicle_type,
            "payment": data.get("PAYMENT", 'null'),
            "expenses": [
                {"travelling": data.get("TRAVEL", 'null')},
                {"lodging": data.get("LODGING", 'null')},
                {"food": data.get("FOOD", 'null')},
                {"maintenance": data.get("MAINTENANCE", 'null')},
                {"laundry": data.get("LAUNDRY", 'null')},
                {"phone": data.get("PHONE", 'null')},
                {"entertainment": data.get("ENTERTAINMENT", 'null')},
                {"tips": data.get("TIPS", 'null')},
                {"other": data.get("OTHER", 'null')}
            ]
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({
            "error": f"Failed to process request: {str(e)}"
        }), 500


if __name__ == '__main__':
    app.run(debug=True)