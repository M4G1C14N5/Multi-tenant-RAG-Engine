from fastapi import FastAPI, Depends
from app.api.dependencies import verify_tenant_namespace
from app.core.enums import TenantEnum

app = FastAPI(title="Multi-tenant RAG Engine Gateway")

@app.get("/query")
def query_vector_database(query: str, namespace: TenantEnum = Depends(verify_tenant_namespace)):
    """
    Example endpoint. The 'namespace' is guaranteed to be a valid TenantEnum
    because it passed through the 'verify_tenant_namespace' dependency.
    """
    
    # At this point, it is mathematically impossible for 'namespace' to be a malicious string.
    # It is safely passed to the central processing engine / vector db client.
    
    return {
        "status": "success",
        "message": f"Querying vector database for: '{query}'",
        "secured_namespace": namespace.value
    }
