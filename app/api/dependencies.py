from fastapi import HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.enums import TenantEnum

security = HTTPBearer()

def verify_tenant_namespace(credentials: HTTPAuthorizationCredentials = Security(security)) -> TenantEnum:
    """
    Validates the user token, extracts the tenant ID, and ensures it matches an authorized Enum.
    """
    token = credentials.credentials
    
    # 1. Decode token (Mocked for now. In production, use python-jose to decode JWT)
    # payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # tenant_id = payload.get("tenant_id")
    
    # Mocking the decoded tenant_id for demonstration purposes
    tenant_id = token  # Pretending the raw token is the tenant_id string for testing
    
    # 2. Strict Enum Validation
    try:
        # This will raise a ValueError if tenant_id is not a valid TenantEnum
        validated_namespace = TenantEnum(tenant_id)
    except ValueError:
        # Terminate lifecycle immediately before hitting the vector DB
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or unauthorized namespace requested."
        )
        
    # 3. Return the sanitized, immutable Enum value
    return validated_namespace
