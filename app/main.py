"""
FastAPI Application Entry Point

RESPONSIBILITIES:
- Initialize FastAPI app with middleware
- Configure CORS for frontend access
- Mount API routers
- Setup startup/shutdown events
- Global exception handling

ARCHITECTURE:
- Clean separation: main.py only does app setup
- Business logic is in api/ and services/
- This file is the "glue" that connects everything
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import sys
import time

from app.core.config import settings, validate_config, is_production
from app.db.session import check_db_connection, close_db_connections, get_pool_stats

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================
# APPLICATION INITIALIZATION
# ============================================

def create_application() -> FastAPI:
    """
    Application factory pattern.
    
    WHY FACTORY PATTERN:
    - Easier to test (can create app with different configs)
    - Cleaner separation of concerns
    - Can create multiple app instances if needed
    
    RETURNS:
        Configured FastAPI application instance
    """
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        docs_url="/api/docs" if not is_production() else None,  # Hide docs in prod
        redoc_url="/api/redoc" if not is_production() else None,
        description="Production-grade audit trail management system"
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Setup event handlers
    setup_event_handlers(app)
    
    # Include routers (will be added later)
    setup_routers(app)
    
    return app


# ============================================
# MIDDLEWARE CONFIGURATION
# ============================================

def setup_middleware(app: FastAPI) -> None:
    """
    Configure application middleware.
    
    WHY MIDDLEWARE:
    - Process all requests/responses in one place
    - CORS, logging, timing, etc.
    - Runs before route handlers
    """
    
    # CORS Middleware
    # WHY: Frontend (React) on different port needs permission to call API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,  # Which domains can access
        allow_credentials=True,  # Allow cookies (for session-based auth if needed)
        allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
        allow_headers=["*"],  # Allow all headers
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """
        Log all incoming requests and their processing time.
        
        WHY:
        - Debugging and monitoring
        - Performance analysis
        - Security audit trail
        
        LOGS:
        - Request method and path
        - Processing time
        - Response status code
        """
        start_time = time.time()
        
        # Log incoming request
        logger.info(f"➡️  {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"⬅️  {request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.2f}s"
        )
        
        # Add processing time to response headers (useful for debugging)
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


# ============================================
# EXCEPTION HANDLERS
# ============================================

def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup global exception handlers.
    
    WHY:
    - Consistent error response format
    - Better error messages for debugging
    - Hide internal errors in production
    - Log all exceptions for monitoring
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Handle Pydantic validation errors.
        
        WHY:
        - Return user-friendly error messages
        - Include field-level errors for forms
        
        EXAMPLE ERROR:
        {
            "error": "Validation Error",
            "detail": [
                {
                    "field": "email",
                    "message": "value is not a valid email address"
                }
            ]
        }
        """
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.warning(f"❌ Validation error: {errors}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "detail": errors,
                "timestamp": time.time()
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        """
        Handle database errors.
        
        WHY:
        - Hide internal database details in production
        - Log full error for debugging
        - Return generic error to user
        
        SECURITY:
        - Never expose database schema in error messages
        - Could reveal table names, column names, etc.
        """
        logger.error(
            f"❌ Database error on {request.method} {request.url.path}: {str(exc)}",
            exc_info=True
        )
        
        # Generic error message (don't expose DB details)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Database Error",
                "detail": "An error occurred while processing your request. Please try again later.",
                "timestamp": time.time()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Catch-all exception handler.
        
        WHY:
        - Prevent unhandled exceptions from crashing the app
        - Log unexpected errors
        - Return consistent error format
        
        DEBUGGING:
        - Full stack trace logged
        - Request details logged
        """
        logger.error(
            f"❌ Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred. Our team has been notified.",
                "timestamp": time.time()
            }
        )


# ============================================
# EVENT HANDLERS
# ============================================

def setup_event_handlers(app: FastAPI) -> None:
    """
    Setup startup and shutdown event handlers.
    
    WHY:
    - Initialize resources on startup
    - Clean up resources on shutdown
    - Validate configuration before accepting requests
    """
    
    @app.on_event("startup")
    async def startup_event():
        """
        Run on application startup.
        
        CHECKS:
        - Validate configuration
        - Check database connection
        - Initialize any caches
        
        FAIL FAST:
        - If any check fails, app won't start
        - Better than runtime failures
        """
        logger.info("🚀 Starting Audit Trail System...")
        
        # Validate configuration
        try:
            validate_config()
        except Exception as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            sys.exit(1)
        
        # Check database connection
        if not check_db_connection():
            logger.error("❌ Cannot connect to database. Exiting.")
            sys.exit(1)
        
        # Log connection pool stats
        pool_stats = get_pool_stats()
        logger.info(f"📊 Database pool: {pool_stats}")
        
        logger.info("✅ Application started successfully")
        logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
        logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """
        Run on application shutdown.
        
        WHY:
        - Gracefully close database connections
        - Flush any pending logs
        - Clean up resources
        """
        logger.info("🛑 Shutting down Audit Trail System...")
        
        # Close database connections
        close_db_connections()
        
        logger.info("✅ Shutdown complete")


# ============================================
# ROUTER CONFIGURATION
# ============================================

def setup_routers(app: FastAPI) -> None:
    """
    Include all API routers.
    
    WHY SEPARATE ROUTERS:
    - Organize endpoints by domain (auth, tasks, audit)
    - Easier to maintain and test
    - Can version APIs easily
    
    NOTE:
    - Routers will be created in next step
    - For now, this is just the structure
    """
    
    # Health check endpoint (no router needed)
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint for monitoring.
        
        WHY:
        - Load balancers need this to check if app is alive
        - Kubernetes liveness/readiness probes
        - Simple way to test if API is up
        
        RETURNS:
        - 200 OK if healthy
        - Database connection status
        - Current timestamp
        """
        db_healthy = check_db_connection()
        pool_stats = get_pool_stats()
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "pool_stats": pool_stats,
            "timestamp": time.time(),
            "version": settings.APP_VERSION
        }
    
    # API routers will be added here:
    # from app.api import auth, tasks, audit, users
    # app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    # app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
    # app.include_router(audit.router, prefix="/api/audit", tags=["Audit Logs"])
    # app.include_router(users.router, prefix="/api/users", tags=["Users"])


# ============================================
# CREATE APPLICATION INSTANCE
# ============================================

app = create_application()


# ============================================
# MAIN ENTRY POINT (for direct execution)
# ============================================

if __name__ == "__main__":
    """
    Run the application directly.
    
    DEVELOPMENT ONLY:
    - Use `uvicorn app.main:app --reload` instead
    - This is here for convenience
    
    PRODUCTION:
    - Use proper ASGI server (uvicorn, gunicorn+uvicorn)
    - Never use --reload in production
    """
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,  # Auto-reload only in debug mode
        log_level="debug" if settings.DEBUG else "info"
    )