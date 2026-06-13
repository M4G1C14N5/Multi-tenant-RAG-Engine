import os
import json
import re

# Paths
STARFOLIO_DIR = os.path.expanduser("~/starfolio")
RESUME_TSX_PATH = os.path.join(STARFOLIO_DIR, "src/data/resume.tsx")
PROJECTS_JSON_PATH = os.path.join(STARFOLIO_DIR, "src/data/projects-generated.json")

def extract_from_tsx(file_path):
    """
    Extracts text fields from the resume.tsx file using Regex.
    In a production Airflow environment, this logic would live in the 'Extract' node.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Could not find {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract basic info
    name_match = re.search(r'name:\s*"([^"]+)"', content)
    summary_match = re.search(r'summary:\s*"([^"]+)"', content)
    location_match = re.search(r'location:\s*"([^"]+)"', content)
    
    basic_info = {
        "name": name_match.group(1) if name_match else "Unknown",
        "summary": summary_match.group(1) if summary_match else "",
        "location": location_match.group(1) if location_match else "",
    }
    
    # Extract Work Experience
    work_experiences = []
    work_blocks = re.findall(r'company:\s*"([^"]+)".*?title:\s*"([^"]+)".*?start:\s*"([^"]+)".*?end:\s*"([^"]+)".*?description:\s*"([^"]+)"', content, re.DOTALL)
    for w in work_blocks:
        work_experiences.append({
            "company": w[0],
            "title": w[1],
            "start": w[2],
            "end": w[3],
            "description": w[4]
        })
        
    # Extract Education
    education = []
    edu_blocks = re.findall(r'school:\s*"([^"]+)".*?degree:\s*"([^"]+)".*?start:\s*"([^"]+)".*?end:\s*"([^"]+)"', content, re.DOTALL)
    for e in edu_blocks:
        education.append({
            "school": e[0],
            "degree": e[1],
            "start": e[2],
            "end": e[3]
        })

    return basic_info, work_experiences, education

def extract_projects(file_path):
    """Extracts project data from the generated JSON file."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_chunks(basic_info, work, education, projects):
    """
    Converts structured data into semantic text chunks for vector embeddings.
    """
    chunks = []
    
    name = basic_info.get("name")
    
    # Chunk 1: Summary & Basic Info
    summary_text = f"{name} is located in {basic_info.get('location')}. Summary: {basic_info.get('summary')}"
    chunks.append({"type": "summary", "text": summary_text})
    
    # Chunks 2: Work Experience
    for idx, w in enumerate(work):
        work_text = f"Work Experience for {name}: {w['title']} at {w['company']} from {w['start']} to {w['end']}. Responsibilities: {w['description']}"
        chunks.append({"type": "work", "text": work_text})
        
    # Chunks 3: Education
    for idx, e in enumerate(education):
        edu_text = f"Education for {name}: Attended {e['school']}, earning a {e['degree']} from {e['start']} to {e['end']}."
        chunks.append({"type": "education", "text": edu_text})
        
    # Chunks 4: Projects
    for idx, p in enumerate(projects):
        tech_stack = ", ".join(p.get('technologies', []))
        proj_text = f"Project by {name}: '{p.get('title')}' created on {p.get('dates')}. Description: {p.get('description')}. Technologies used: {tech_stack}."
        chunks.append({"type": "project", "text": proj_text})
        
    return chunks

def run_preprocessing_pipeline():
    print("🚀 Starting Starfolio Preprocessing Pipeline Test...")
    
    print("1. Extracting data from resume.tsx...")
    basic_info, work, education = extract_from_tsx(RESUME_TSX_PATH)
    print(f"   -> Extracted basic info for: {basic_info.get('name')}")
    print(f"   -> Extracted {len(work)} work experiences.")
    print(f"   -> Extracted {len(education)} education records.")
    
    print("2. Extracting projects from JSON...")
    projects = extract_projects(PROJECTS_JSON_PATH)
    print(f"   -> Extracted {len(projects)} projects.")
    
    print("3. Generating semantic chunks...")
    chunks = generate_chunks(basic_info, work, education, projects)
    print(f"   -> Successfully generated {len(chunks)} text chunks!\n")
    
    print("=== SAMPLE CHUNKS PREVIEW ===")
    for chunk in chunks[:5]: # Show first 5 chunks
        print(f"[{chunk['type'].upper()}]: {chunk['text']}\n")
        
    print("=== PREPROCESSING COMPLETE ===")

if __name__ == "__main__":
    run_preprocessing_pipeline()
