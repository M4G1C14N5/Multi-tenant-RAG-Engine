import json
import os
import re
import uuid
from typing import Any, Dict, List, Tuple


def resolve_starfolio_dir() -> str:
    """
    Resolve the Starfolio checkout directory.

    Preference order:
    - explicit STARFOLIO_DIR env var
    - bind mount at /mnt/starfolio
    - old local fallbacks
    """
    candidates = [
        os.getenv("STARFOLIO_DIR"),
        "/mnt/starfolio",
        os.path.expanduser("~/starfolio"),
        "/home/pluto/starfolio",
    ]

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    raise FileNotFoundError(
        "Could not find the Starfolio repository. Set STARFOLIO_DIR or mount it at /mnt/starfolio."
    )


def resolve_starfolio_paths() -> Tuple[str, str, str]:
    starfolio_dir = resolve_starfolio_dir()
    resume_tsx_path = os.path.join(starfolio_dir, "src/data/resume.tsx")
    projects_json_path = os.path.join(starfolio_dir, "src/data/projects-generated.json")
    return starfolio_dir, resume_tsx_path, projects_json_path


def extract_from_tsx(file_path: str) -> Tuple[Dict[str, str], List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Extract basic information, work experience, and education from resume.tsx.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Could not find {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    name_match = re.search(r'name:\s*"([^"]+)"', content)
    summary_match = re.search(r'summary:\s*"([^"]+)"', content)
    location_match = re.search(r'location:\s*"([^"]+)"', content)

    basic_info = {
        "name": name_match.group(1) if name_match else "Unknown",
        "summary": summary_match.group(1) if summary_match else "",
        "location": location_match.group(1) if location_match else "",
    }

    work_experiences: List[Dict[str, str]] = []
    work_blocks = re.findall(
        r'company:\s*"([^"]+)".*?title:\s*"([^"]+)".*?start:\s*"([^"]+)".*?end:\s*"([^"]+)".*?description:\s*"([^"]+)"',
        content,
        re.DOTALL,
    )
    for company, title, start, end, description in work_blocks:
        work_experiences.append(
            {
                "company": company,
                "title": title,
                "start": start,
                "end": end,
                "description": description,
            }
        )

    education: List[Dict[str, str]] = []
    edu_blocks = re.findall(
        r'school:\s*"([^"]+)".*?degree:\s*"([^"]+)".*?start:\s*"([^"]+)".*?end:\s*"([^"]+)"',
        content,
        re.DOTALL,
    )
    for school, degree, start, end in edu_blocks:
        education.append(
            {
                "school": school,
                "degree": degree,
                "start": start,
                "end": end,
            }
        )

    return basic_info, work_experiences, education


def extract_projects(file_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_chunks(
    basic_info: Dict[str, str],
    work: List[Dict[str, str]],
    education: List[Dict[str, str]],
    projects: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """
    Convert structured Starfolio data into semantic text chunks for embeddings.
    """
    chunks: List[Dict[str, str]] = []
    name = basic_info.get("name", "Unknown")

    summary_text = f"{name} is located in {basic_info.get('location', '')}. Summary: {basic_info.get('summary', '')}"
    chunks.append({"type": "summary", "text": summary_text})

    for experience in work:
        work_text = (
            f"Work Experience for {name}: {experience['title']} at {experience['company']} "
            f"from {experience['start']} to {experience['end']}. "
            f"Responsibilities: {experience['description']}"
        )
        chunks.append({"type": "work", "text": work_text})

    for record in education:
        edu_text = (
            f"Education for {name}: Attended {record['school']}, earning a {record['degree']} "
            f"from {record['start']} to {record['end']}."
        )
        chunks.append({"type": "education", "text": edu_text})

    for project in projects:
        tech_stack = ", ".join(project.get("technologies", []))
        proj_text = (
            f"Project by {name}: '{project.get('title')}' created on {project.get('dates')}. "
            f"Description: {project.get('description')}. Technologies used: {tech_stack}."
        )
        chunks.append({"type": "project", "text": proj_text})

    return chunks


def create_openai_client():
    from openai import OpenAI

    return OpenAI(api_key=os.getenv("OPENAI_API_KEY", "mock-key"))


def create_qdrant_client():
    from qdrant_client import QdrantClient

    return QdrantClient(os.getenv("QDRANT_HOST", "localhost"), port=int(os.getenv("QDRANT_PORT", "6333")))


def ensure_collection(qdrant_client, collection_name: str, vector_size: int = 1536) -> None:
    from qdrant_client.http import models

    collections = qdrant_client.get_collections().collections
    if any(c.name == collection_name for c in collections):
        return

    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE,
        ),
    )


def get_embedding(openai_client, text: str, model: str = "text-embedding-3-small") -> List[float]:
    if getattr(openai_client, "api_key", None) == "mock-key":
        return [0.0] * 1536

    response = openai_client.embeddings.create(input=text, model=model)
    return response.data[0].embedding


def upload_chunks(
    qdrant_client,
    openai_client,
    collection_name: str,
    tenant_id: str,
    chunks: List[Dict[str, str]],
) -> Dict[str, Any]:
    from qdrant_client.http import models

    ensure_collection(qdrant_client, collection_name)

    points = []
    for chunk in chunks:
        vector = get_embedding(openai_client, chunk["text"])
        payload = {
            "tenant_id": tenant_id,
            "type": chunk["type"],
            "text": chunk["text"],
        }
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload,
            )
        )

    qdrant_client.upsert(collection_name=collection_name, points=points)
    return {"tenant_id": tenant_id, "chunk_count": len(points), "collection": collection_name}
