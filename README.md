# Multi-tenant RAG Engine

This project aims to provide a unified vector database solution for multiple AI applications. By leveraging collections or namespaces within a single vector database instance, we can effectively separate data for different websites or applications.

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
