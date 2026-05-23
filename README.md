# Multi-tenant RAG Engine

This project aims to provide a unified vector database solution for multiple AI applications. By leveraging collections or namespaces within a single vector database instance, we can effectively separate data for different websites or applications.

## Core Architecture

- **Vector Database**: A single container instance serving as the storage layer, using namespaces to maintain data isolation.
- **Central Processing Engine**: A central container responsible for:
    - Receiving user queries.
    - Orchestrating AI API calls.
    - Handling embedding model generation (converting website data to vector embeddings).
    - Communicating with the LLM to generate context-aware, accurate responses based on the retrieved data.

## RAG Principle

This engine follows the Retrieval-Augmented Generation (RAG) principle. It retrieves relevant knowledge from the vector database for a specific tenant/website and feeds it to the LLM as context, ensuring answers are grounded in real-time, tenant-specific information.
