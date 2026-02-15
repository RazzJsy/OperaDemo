import os
import shutil
from typing import List, Optional
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from src.rag.pipeline import RAGPipeline
from src.validation.validator import ValidationLevel

app = FastAPI(
    title="OperaDemo",
    description="RAG-powered financial document Q&A with small models",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline: Optional[RAGPipeline] = None

UPLOAD_DIR = Path("./uploaded_documents")
UPLOAD_DIR.mkdir(exist_ok=True)

class QueryRequest(BaseModel):
    question: str
    validate: bool = True

class QueryResponse(BaseModel):
    question: str
    answer: str
    validation_level: Optional[str]
    confidence_score: Optional[float]
    sources: List[dict]
    warnings: List[str]
    metadata: dict

class HealthResponse(BaseModel):
    status: str
    pipeline_ready: bool
    documents_loaded: bool
    llm_available: bool


@app.on_event("startup")
async def startup_event():
    """Initialize RAG pipeline on application startup"""
    global pipeline
    
    print("\n" + "="*60)
    print("Starting OperaDemo API")
    print("="*60)
    
    try:
        pipeline = RAGPipeline()
        
        sample_dir = Path("./sample_documents")
        
        if sample_dir.exists() and any(sample_dir.glob("*.pdf")):
            print("\nLoading sample documents...")
            pipeline.load_documents(str(sample_dir))
        
        if UPLOAD_DIR.exists() and any(UPLOAD_DIR.glob("*.pdf")):
            print("\nLoading previously uploaded documents...")
            pipeline.load_documents(str(UPLOAD_DIR), append=True)
        
        print("\nAPI Ready!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nError initializing pipeline: {e}")
        print("="*60 + "\n")

@app.get("/", response_class=FileResponse)
async def root():
    return FileResponse("templates/api-dashboard.html")

@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload and index PDF documents
    """
    global pipeline
    
    if not pipeline:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    saved_files = []
    for file in files:
        if not file.filename.endswith('.pdf'):
            continue
        
        file_path = UPLOAD_DIR / file.filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        saved_files.append(str(file_path))
    
    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid PDF files uploaded")
    
    try:
        pipeline.load_documents(str(UPLOAD_DIR), append=True)
        stats = pipeline.get_pipeline_stats()
        
        return {
            "status": "success",
            "files_processed": len(saved_files),
            "total_chunks": stats["retriever"]["total_chunks"],
            "message": "Documents uploaded and indexed successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query indexed documents
    """
    global pipeline
    
    if not pipeline:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    try:
        response = pipeline.query(
            question=request.question,
            validate=request.validate
        )
        
        return QueryResponse(
            question=response.query,
            answer=response.answer,
            validation_level=response.validation.level.value if response.validation else None,
            confidence_score=response.validation.confidence_score if response.validation else None,
            sources=[
                {
                    "text": s["text"],
                    "source": s["source"],
                    "page": s["page"],
                    "combined_score": s.get("combined_score", 0.0),
                    "bm25_score": s.get("bm25_score", 0.0),
                    "dense_score": s.get("dense_score", 0.0)
                }
                for s in response.sources
            ],
            warnings=response.validation.warnings if response.validation else [],
            metadata=response.metadata
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    global pipeline
    
    pipeline_ready = pipeline is not None
    documents_loaded = pipeline._documents_loaded if pipeline else False
    llm_available = pipeline.llm_provider.health_check() if pipeline else False
    
    return HealthResponse(
        status="healthy" if pipeline_ready else "initializing",
        pipeline_ready=pipeline_ready,
        documents_loaded=documents_loaded,
        llm_available=llm_available
    )


@app.get("/stats")
async def get_stats():
    """
    Get pipeline statistics
    """
    global pipeline
    
    if not pipeline:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    return pipeline.get_pipeline_stats()


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )