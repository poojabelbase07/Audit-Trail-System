"""
Application Configuration Module

WHY THIS EXISTS:
- Centralizes all configuration (database, auth, CORS, etc.)
- Validates environment variables at startup (fail fast principle)
- Provides type-safe config access throughout the application
- Separates dev/staging/prod configs cleanly

SECURITY NOTES:
- Never commit .env files with real secrets
- Use secrets management (AWS Secrets Manager, Vault) in production
- SECRET_KEY should be 32+ random characters
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Pydantic validates types and required fields automatically.
    If a required field is missing, the app won't start (fail fast).
    """
    
    # ============================================
    # APPLICATION SETTINGS
    # ============================================
    APP_NAME: str = "Audit Trail System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True
    
    # ============================================
    # DATABASE SETTINGS
    # ============================================
    # WHY: PostgreSQL chosen for ACID compliance (critical for audit logs)
    DATABASE_URL: str
    # Example: postgresql://admin:admin123@localhost:5432/audit_trail_db
    
    # Connection pool settings
    # WHY: Reusing connections improves performance under load
    DB_POOL_SIZE: int = 10  # Max number of connections to keep open
    DB_MAX_OVERFLOW: int = 20  # Additional connections when pool is full
    DB_POOL_TIMEOUT: int = 30  # Seconds to wait for available connection
    
    # ============================================
    # SECURITY SETTINGS
    # ============================================
    # WHY: JWT for stateless authentication (horizontally scalable)
    SECRET_KEY: str  # MUST be set in .env - used for JWT signing
    ALGORITHM: str = "HS256"  # HMAC-SHA256 for JWT signing
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Password hashing
    # WHY: bcrypt with high cost factor protects against brute force
    BCRYPT_ROUNDS: int = 12  # Higher = more secure but slower
    
    # ============================================
    # CORS SETTINGS
    # ============================================
    # WHY: Control which frontend domains can access the API
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React dev server
    ]
    # In production, replace with actual domain: ["https://app.yourdomain.com"]
    
    # ============================================
    # REDIS SETTINGS (for caching and rate limiting)
    # ============================================
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_TTL: int = 3600  # Cache TTL in seconds (1 hour)
    
    # ============================================
    # RATE LIMITING
    # ============================================
    # WHY: Prevent abuse and DoS attacks
    RATE_LIMIT_PER_MINUTE: int = 60  # Requests per minute per user
    
    # ============================================
    # AUDIT LOG SETTINGS
    # ============================================
    # WHY: Control retention and storage policies
    AUDIT_LOG_RETENTION_DAYS: int = 365  # Keep logs for 1 year
    MAX_AUDIT_LOGS_PER_REQUEST: int = 100  # Pagination limit
    
    # ============================================
    # TASK LIMITS (prevent abuse)
    # ============================================
    MAX_TASKS_PER_DAY: int = 50  # Per user
    MAX_TASK_TITLE_LENGTH: int = 200
    MAX_TASK_DESCRIPTION_LENGTH: int = 5000
    
    class Config:
        """
        Pydantic configuration for environment variable loading.
        
        WHY env_file:
        - Loads variables from .env file automatically
        - Keeps secrets out of code
        - Easy to change between environments
        """
        env_file = ".env"
        case_sensitive = True  # DATABASE_URL != database_url


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    WHY lru_cache:
    - Settings are loaded only once (not on every request)
    - Improves performance
    - Singleton pattern ensures consistency
    
    USAGE:
        from app.core.config import get_settings
        settings = get_settings()
        print(settings.DATABASE_URL)
    
    ERROR HANDLING:
    - If required env vars missing, Pydantic raises ValidationError
    - App crashes immediately (fail fast - better than runtime errors)
    """
    return Settings()


# Convenience exports
settings = get_settings()


# ============================================
# ENVIRONMENT-SPECIFIC HELPERS
# ============================================

def is_production() -> bool:
    """Check if running in production environment."""
    return settings.ENVIRONMENT == "production"

def is_development() -> bool:
    """Check if running in development environment."""
    return settings.ENVIRONMENT == "development"


# ============================================
# CONFIGURATION VALIDATION
# ============================================

def validate_config():
    """
    Validate critical configuration at startup.
    
    WHY:
    - Catch misconfigurations before they cause runtime errors
    - Security checks (e.g., weak SECRET_KEY)
    - Database connectivity check
    
    WHEN CALLED:
    - In main.py on application startup
    """
    
    # Check SECRET_KEY strength
    if len(settings.SECRET_KEY) < 32:
        raise ValueError(
            "SECRET_KEY must be at least 32 characters. "
            "Generate one with: openssl rand -hex 32"
        )
    
    # Warn about DEBUG in production
    if is_production() and settings.DEBUG:
        print("⚠️  WARNING: DEBUG=True in production is a security risk!")
    
    # Validate DATABASE_URL format
    if not settings.DATABASE_URL.startswith("postgresql://"):
        raise ValueError(
            "DATABASE_URL must start with postgresql:// "
            f"Got: {settings.DATABASE_URL[:20]}..."
        )
    
    print("✅ Configuration validated successfully")