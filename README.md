# Multi-tenant RAG Engine

This project aims to provide a unified vector database solution for multiple AI applications. By leveraging collections or namespaces within a single vector database instance, we can effectively separate data for different websites or applications.

## Mandatory Architectural Constraints

### 1. Secure Vector DB Namespace Validation
- **Constraint:** Never allow the central processing engine or query handler to blindly pass user-supplied string variables directly to the vector database collection or namespace parameter.
- **Implementation Rules:**
  - Strict **Enum checking and Token verification** must be implemented directly at the API gateway layer (e.g., FastAPI).
  - The incoming user authorization token (JWT/OAuth) must be parsed and validated to resolve the `tenant_id`. 
  - This resolved identity must match against a hardcoded, immutable system Enum of authorized namespaces (e.g., `TenantEnum.STARFOLIO`). If a requested namespace string does not map directly to a valid enum token or lacks the respective role scope, the lifecycle terminates immediately with an explicit `HTTP 403 Forbidden` error.

### 2. Event-Driven Airflow Trigger Strategy (Zero Wasted Compute)
- **Constraint:** Avoid time-interval cron scheduling for dynamic multi-tenant file formats. Wasting compute cycles polling unchanged data is strictly prohibited.
- **Implementation Rules:**
  - Standard ingestion DAGs must rely on **Event-Driven Scheduling** (leveraging Airflow 3+ AssetWatchers / HTTP event triggers or a lightweight Webhook receiver endpoint).
  - Tasks are designed to consume external payloads sent via secured webhooks from source platforms (e.g., a Starfolio file-commit hook). 
  - DAG logic immediately executes downstream nodes (`Extract` → `Preprocess` → `Embed` → `Upsert to Namespace`) *only* when an explicit backend file change or web event packet is received and cryptographically verified.

## Core Architecture

- **Ingestion Scripts**: Runs daily and takes data from projects' databases
- **Vector Database**: A single container instance serving as the storage layer, using namespaces to maintain data isolation.
- **Central Processing Engine**: A central container responsible for:
    - Receiving user queries.
    - Orchestrating AI API calls.
    - Handling embedding model generation (converting website data to vector embeddings).
    - Communicating with the LLM to generate context-aware, accurate responses based on the retrieved data.

## RAG Principle

This engine follows the Retrieval-Augmented Generation (RAG) principle. It retrieves relevant knowledge from the vector database for a specific tenant/website and feeds it to the LLM as context, ensuring answers are grounded in real-time, tenant-specific information.

## Use Case: Starfolio Assistant Integration

The first challenge is integrating an AI assistant into the existing [Starfolio](https://github.com/M4G1C14N5/starfolio) website:
- **UI Integration**: Adding a floating chat button in the bottom-right corner that opens an overlay interface.
- **Data Challenge**: Transforming the pre-existing content of the Starfolio website into a format suitable for the vector database (embedding generation) so the assistant can answer questions based on your portfolio and blog content.
