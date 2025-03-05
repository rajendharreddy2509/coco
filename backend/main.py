from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from chatbot import router as chatbot_router
from speech import router as speech_router
from pdf_processing import router as pdf_router

def create_app():
    """Initialize and configure the FastAPI application."""
    app = FastAPI()

    # Configure CORS for Next.js frontend
    configure_cors(app)

    # Include all routers
    register_routers(app)

    return app

def configure_cors(app):
    """Set up CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def register_routers(app):
    """Register all API routers."""
    app.include_router(auth_router)
    app.include_router(chatbot_router)  # ✅ Only included once
    app.include_router(speech_router)
    app.include_router(pdf_router)

app = create_app()

@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "✅ API is running!"}
