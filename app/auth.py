from fastapi import Depends, Header, HTTPException
import jwt
import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") 
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# Validate environment variables
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not SUPABASE_JWT_SECRET:
    print("Warning: Supabase environment variables not set. Authentication will be disabled.")
    print(f"SUPABASE_URL: {'✓' if SUPABASE_URL else '✗'}")
    print(f"SUPABASE_SERVICE_KEY: {'✓' if SUPABASE_SERVICE_KEY else '✗'}")
    print(f"SUPABASE_JWT_SECRET: {'✓' if SUPABASE_JWT_SECRET else '✗'}")
    supabase = None
else:
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_tenant_id_from_supabase(user_id: str) -> str:
    """Fetch tenant_id for authenticated user from Supabase"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    try:
        response = supabase.table("internal_users").select("tenant_id").eq("id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found in system")
        
        return str(response.data[0]["tenant_id"])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def get_current_tenant(authorization: str = Header(...)) -> str:
    """Extract and validate JWT token, return tenant_id"""
    if not supabase or not SUPABASE_JWT_SECRET:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token = authorization.replace("Bearer ", "")
        
        # Decode and validate JWT token
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        user_id = payload["sub"]
        
        # Get tenant_id from database
        tenant_id = get_tenant_id_from_supabase(user_id)
        
        return tenant_id
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")

# Legacy support - keep existing function for backward compatibility
def get_tenant_id(x_tenant_id: str = Header(None)) -> Optional[str]:
    """Legacy function - use get_current_tenant for new implementations"""
    if not x_tenant_id:
        raise HTTPException(
            status_code=401,
            detail="X-Tenant-ID header missing"
        )
    return x_tenant_id
