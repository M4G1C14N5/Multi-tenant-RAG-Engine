from datetime import datetime
from pathlib import Path
import os

from airflow import DAG
from airflow.operators.python import PythonOperator

from ingestion.starfolio_pipeline import (
    extract_from_tsx,
    extract_projects,
    generate_chunks,
    resolve_starfolio_paths,
)


def extract_task(**context):
    _, resume_tsx_path, projects_json_path = resolve_starfolio_paths()
    basic_info, work, education = extract_from_tsx(resume_tsx_path)
    projects = extract_projects(projects_json_path)

    return {
        "basic_info": basic_info,
        "work": work,
        "education": education,
        "projects": projects,
    }


def preprocess_task(**context):
    payload = context["ti"].xcom_pull(task_ids="extract_starfolio_source")
    chunks = generate_chunks(
        payload["basic_info"],
        payload["work"],
        payload["education"],
        payload["projects"],
    )

    stage_dir = Path(os.getenv("STARFOLIO_STAGE_DIR", "/tmp/starfolio_ingestion"))
    stage_dir.mkdir(parents=True, exist_ok=True)
    stage_file = stage_dir / "chunks.json"
    stage_file.write_text(__import__("json").dumps(chunks, indent=2), encoding="utf-8")
    return {"stage_file": str(stage_file), "chunk_count": len(chunks)}


def upsert_task(**context):
    stage = context["ti"].xcom_pull(task_ids="preprocess_starfolio_chunks")
    return {
        "status": "ready_for_qdrant",
        "stage_file": stage["stage_file"],
        "chunk_count": stage["chunk_count"],
    }


default_args = {
    "owner": "pluto",
    "depends_on_past": False,
    "retries": 1,
}

with DAG(
    dag_id="starfolio_ingestion",
    description="Event-driven Starfolio ingestion pipeline for the multi-tenant RAG engine.",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["starfolio", "rag", "ingestion"],
) as dag:
    extract_starfolio_source = PythonOperator(
        task_id="extract_starfolio_source",
        python_callable=extract_task,
    )

    preprocess_starfolio_chunks = PythonOperator(
        task_id="preprocess_starfolio_chunks",
        python_callable=preprocess_task,
    )

    stage_for_qdrant = PythonOperator(
        task_id="stage_for_qdrant",
        python_callable=upsert_task,
    )

    extract_starfolio_source >> preprocess_starfolio_chunks >> stage_for_qdrant

