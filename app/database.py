"""
Database Session Management

WHY THIS EXISTS:
- Manages database connections lifecycle
- Provides session dependency for FastAPI endpoints
- Handles connection pooling for performance
- Ensures sessions are properly closed (no connection leaks)

ARCHITECTURE DECISION:
- Using SQLAlchemy ORM (vs raw SQL) for:
  * Type safety
  * Automatic migrations with Alembic
  * Protection against SQL injection
  * Cross-database compatibility
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from app.core.config import settings

# Configure logging for database operations
logger = logging.getLogger(__name__)


# ============================================
# DATABASE ENGINE
# ============================================

"""
WHY create_engine here:
- Single engine instance (connection pool) shared across app
- Pool configuration from settings
- Echo=False in production (don't log every SQL query)
"""

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,  # Concurrent connections
    max_overflow=settings.DB_MAX_OVERFLOW,  # Extra connections when busy
    pool_timeout=settings.DB_POOL_TIMEOUT,  # Wait time for connection
    pool_pre_ping=True,  # Verify connection before using (handles stale connections)
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)


# ============================================
# DATABASE EVENT LISTENERS (for debugging)
# ============================================

@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """
    Called when a new database connection is created.
    
    WHY:
    - Log connection events for debugging
    - Set connection-level settings if needed
    """
    logger.debug("🔌 New database connection established")


@event.listens_for(engine, "close")
def receive_close(dbapi_conn, connection_record):
    """Called when a connection is closed."""
    logger.debug("🔌 Database connection closed")


# ============================================
# SESSION FACTORY
# ============================================

"""
WHY SessionLocal:
- Factory pattern for creating database sessions
- Each request gets its own session (thread-safe)
- autocommit=False: We control when to commit (explicit is better)
- autoflush=False: We control when to flush changes
"""

SessionLocal = sessionmaker(
    autocommit=False,  # Manual commit (safer, explicit transactions)
    autoflush=False,   # Manual flush (better control)
    bind=engine,       # Bind to our engine
)


# ============================================
# BASE CLASS FOR MODELS
# ============================================

"""
WHY declarative_base:
- All SQLAlchemy models inherit from this
- Provides metadata registry for tables
- Enables Alembic migrations
"""

Base = declarative_base()


# ============================================
# DATABASE DEPENDENCY (for FastAPI)
# ============================================

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    
    WHY THIS PATTERN:
    - Session is created per request
    - Automatically closed after request (even if exception occurs)
    - Prevents connection leaks
    
    USAGE IN ENDPOINTS:
        @app.get("/tasks")
        def get_tasks(db: Session = Depends(get_db)):
            tasks = db.query(Task).all()
            return tasks
    
    TRANSACTION HANDLING:
    - Commits are done explicitly in service layer
    - Rollback happens automatically on exception
    
    ERROR HANDLING:
    - If database connection fails, exception propagates to FastAPI
    - FastAPI returns 500 error to client
    - Connection is still properly closed in finally block
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # Log the error with context
        logger.error(
            f"❌ Database error during request: {str(e)}",
            exc_info=True  # Include stack trace
        )
        # Rollback any failed transaction
        db.rollback()
        raise  # Re-raise to let FastAPI handle the HTTP response
    finally:
        # Always close the session (even on exceptions)
        db.close()
        logger.debug("✅ Database session closed")


# ============================================
# DATABASE INITIALIZATION
# ============================================

def init_db() -> None:
    """
    Initialize database tables.
    
    WHY:
    - Creates all tables defined in models
    - Used during first-time setup
    - In production, use Alembic migrations instead
    
    WHEN TO USE:
    - Development: Quick setup
    - Testing: Fresh database for each test
    - Production: Use Alembic migrations (safer, versioned)
    
    USAGE:
        from app.db.session import init_db
        init_db()  # Creates all tables
    """
    logger.info("🏗️  Creating database tables...")
    
    try:
        # Import all models so they're registered with Base
        # WHY: SQLAlchemy needs to know about models before creating tables
        from app.models import user, task, audit_log  # noqa
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(
            f"❌ Failed to create database tables: {str(e)}",
            exc_info=True
        )
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is working.
    
    WHY:
    - Validate database connectivity at startup
    - Fail fast if database is unreachable
    - Useful for health checks
    
    RETURNS:
        bool: True if connection successful, False otherwise
    
    USAGE:
        if not check_db_connection():
            logger.error("Cannot connect to database!")
            sys.exit(1)
    """
    try:
        db = SessionLocal()
        # Try a simple query
        db.execute("SELECT 1")
        db.close()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(
            f"❌ Database connection failed: {str(e)}",
            exc_info=True
        )
        return False


# ============================================
# CONNECTION POOL MONITORING (for production)
# ============================================

def get_pool_stats() -> dict:
    """
    Get database connection pool statistics.
    
    WHY:
    - Monitor connection pool usage
    - Detect connection leaks
    - Optimize pool size
    
    USAGE:
        stats = get_pool_stats()
        print(f"Active connections: {stats['checked_out']}")
    
    MONITORING:
    - If checked_out approaches pool_size, increase pool_size
    - If overflow frequently used, increase max_overflow
    """
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin(),
    }


# ============================================
# GRACEFUL SHUTDOWN
# ============================================

def close_db_connections():
    """
    Close all database connections gracefully.
    
    WHY:
    - Called on application shutdown
    - Prevents "too many connections" errors
    - Ensures data is flushed
    
    USAGE:
        import atexit
        atexit.register(close_db_connections)
    """
    logger.info("🔌 Closing database connections...")
    engine.dispose()
    logger.info("✅ All database connections closed")