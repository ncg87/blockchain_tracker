from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import blocks, transactions, analytics, patterns

app = FastAPI(
    title="Blockchain Analytics API",
    description="API for accessing blockchain data and analytics",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(blocks.router, prefix="/api/v1/blocks", tags=["blocks"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(patterns.router, prefix="/api/v1/patterns", tags=["patterns"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Blockchain Analytics API"}