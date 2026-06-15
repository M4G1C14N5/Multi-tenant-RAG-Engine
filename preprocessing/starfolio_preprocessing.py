import os

from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient

from app.core.enums import TenantEnum
from ingestion.starfolio_pipeline import (
    create_openai_client,
    create_qdrant_client,
    extract_from_tsx,
    extract_projects,
    generate_chunks,
    resolve_starfolio_paths,
    upload_chunks,
)


load_dotenv()

STARFOLIO_DIR, RESUME_TSX_PATH, PROJECTS_JSON_PATH = resolve_starfolio_paths()
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "tenant_data")
TENANT_ID = TenantEnum.STARFOLIO.value


def run_preprocessing_pipeline():
    basic_info, work, education = extract_from_tsx(RESUME_TSX_PATH)
    projects = extract_projects(PROJECTS_JSON_PATH)
    return generate_chunks(basic_info, work, education, projects)


def main() -> None:
    print(f"Using Starfolio source: {STARFOLIO_DIR}")
    print(f"Resume path: {RESUME_TSX_PATH}")
    print(f"Projects path: {PROJECTS_JSON_PATH}")

    chunks = run_preprocessing_pipeline()
    print(f"Prepared {len(chunks)} chunks for tenant '{TENANT_ID}'.")

    openai_client = create_openai_client()
    qdrant_client = create_qdrant_client()

    result = upload_chunks(
        qdrant_client=qdrant_client,
        openai_client=openai_client,
        collection_name=COLLECTION_NAME,
        tenant_id=TENANT_ID,
        chunks=chunks,
    )
    print(f"Upload complete: {result}")


if __name__ == "__main__":
    main()
