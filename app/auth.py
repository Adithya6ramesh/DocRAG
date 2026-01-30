from fastapi import Header, HTTPException

def get_tenant_id(x_tenant_id: str = Header(None)):
    if not x_tenant_id:
        raise HTTPException(
            status_code=401,
            detail="X-Tenant-ID header missing"
        )
    return x_tenant_id
