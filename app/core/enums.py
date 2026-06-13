from enum import Enum

class TenantEnum(str, Enum):
    """
    Immutable system Enum of all authorized namespaces.
    No vector database query will execute unless the tenant resolves to one of these.
    """
    STARFOLIO = "starfolio"
    SCOUTING_REPORT = "scouting_report"
    # Add future tenants here
