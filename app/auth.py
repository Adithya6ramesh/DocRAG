from fastapi import Depends, Header, HTTPException
import jwt
import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") 
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# Validate environment variables
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not SUPABASE_JWT_SECRET:
    print("Warning: Supabase environment variables not set. Authentication will be disabled.")
    print(f"SUPABASE_URL: {'✓' if SUPABASE_URL else '✗'}")
    print(f"SUPABASE_ANON_KEY: {'✓' if SUPABASE_ANON_KEY else '✗'}")
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
    """Extract and validate JWT token using Supabase API, return user_id as tenant_id"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token = authorization.replace("Bearer ", "")
        
        # Validate token with Supabase API
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise HTTPException(status_code=503, detail="Authentication service unavailable")
        
        import requests
        response = requests.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={"Authorization": f"Bearer {token}", "apikey": SUPABASE_ANON_KEY}
        )
        
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get("id")
            if user_id:
                logger.info(f"Auth successful for user: {user_id}")
                return user_id
            else:
                raise HTTPException(status_code=401, detail="Invalid token response")
        else:
            logger.error(f"Supabase auth failed: {response.status_code}")
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
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

# Flexible auth - accepts both JWT and X-Tenant-ID
def get_tenant_id_flexible(
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
) -> str:
    """Accept either JWT token or X-Tenant-ID header for authentication"""
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Auth header present: {authorization is not None}")
    logger.info(f"X-Tenant-ID present: {x_tenant_id is not None}")
    
    # Try JWT first (for logged-in users)
    if authorization:
        try:
            if not authorization.startswith("Bearer "):
                logger.error(f"Invalid header format: {authorization[:30]}")
                raise HTTPException(status_code=401, detail="Invalid authorization header format")
            
            token = authorization.replace("Bearer ", "")
            logger.info(f"Token (first 20 chars): {token[:20]}...")
            
            # Validate token with Supabase
            if not SUPABASE_URL or not SUPABASE_ANON_KEY:
                logger.error("Supabase credentials not configured")
                raise HTTPException(status_code=503, detail="Authentication service unavailable")
            
            # Verify token with Supabase API
            import requests
            response = requests.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={"Authorization": f"Bearer {token}", "apikey": SUPABASE_ANON_KEY}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get("id")
                if user_id:
                    logger.info(f"Auth successful, user_id: {user_id}")
                    return user_id
                else:
                    logger.error("No user ID in response")
                    raise HTTPException(status_code=401, detail="Invalid token response")
            else:
                logger.error(f"Supabase auth failed: {response.status_code} - {response.text}")
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Auth exception: {str(e)}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    # Fallback to X-Tenant-ID (for demo/testing)
    if x_tenant_id:
        return x_tenant_id
    
    # No authentication provided
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide either Authorization header or X-Tenant-ID"
    )
