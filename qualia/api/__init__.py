"""
Qualia Core REST API

Expõe as funcionalidades do Qualia Core via HTTP REST API.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import tempfile
import json
from pathlib import Path
import base64
import io

from qualia.core import QualiaCore, Document

# Initialize FastAPI app
app = FastAPI(
    title="Qualia Core API",
    description="REST API for Qualia Core - Análise Qualitativa Framework",
    version="0.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Qualia Core
core = QualiaCore()
core.discover_plugins()

# Pydantic models for request/response
class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Text content to analyze")
    config: Dict[str, Any] = Field(default_factory=dict, description="Plugin configuration parameters")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")

class ProcessRequest(BaseModel):
    text: str = Field(..., description="Text content to process")
    config: Dict[str, Any] = Field(default_factory=dict, description="Plugin configuration parameters")

class VisualizeRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description="Data to visualize (usually from analyzer output)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Visualization configuration")
    output_format: str = Field("png", description="Output format: png, svg, html")

class PipelineStep(BaseModel):
    plugin_id: str
    config: Dict[str, Any] = Field(default_factory=dict)

class PipelineRequest(BaseModel):
    text: str = Field(..., description="Text content to process through pipeline")
    steps: List[PipelineStep] = Field(..., description="Pipeline steps to execute")

class PluginInfo(BaseModel):
    id: str
    name: str
    type: str
    description: str
    version: str
    provides: List[str]
    requires: List[str]
    parameters: Dict[str, Any]

# Helper functions
def plugin_to_info(plugin_id: str) -> PluginInfo:
    """Convert plugin metadata to API response model"""
    plugin = core.plugins.get(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")
    
    meta = plugin.meta()
    return PluginInfo(
        id=meta.id,
        name=meta.name,
        type=meta.type.value,
        description=meta.description,
        version=meta.version,
        provides=meta.provides,
        requires=meta.requires,
        parameters=meta.parameters
    )

# API Endpoints
@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "name": "Qualia Core API",
        "version": "0.1.0",
        "description": "REST API for qualitative analysis",
        "endpoints": {
            "plugins": "/plugins",
            "analyze": "/analyze/{plugin_id}",
            "process": "/process/{plugin_id}",
            "visualize": "/visualize/{plugin_id}",
            "pipeline": "/pipeline"
        }
    }

@app.get("/plugins", response_model=List[PluginInfo])
def list_plugins(plugin_type: Optional[str] = None):
    """List all available plugins"""
    plugins = []
    for plugin_id, plugin in core.plugins.items():
        meta = plugin.meta()
        if plugin_type and meta.type.value != plugin_type:
            continue
        plugins.append(plugin_to_info(plugin_id))
    return plugins

@app.get("/plugins/{plugin_id}", response_model=PluginInfo)
def get_plugin(plugin_id: str):
    """Get detailed information about a specific plugin"""
    return plugin_to_info(plugin_id)

@app.post("/analyze/{plugin_id}")
async def analyze(plugin_id: str, request: AnalyzeRequest):
    """Execute an analyzer plugin on text"""
    try:
        # Create document
        doc = core.add_document(f"api_doc_{plugin_id}", request.text)
        
        # Execute plugin
        result = core.execute_plugin(plugin_id, doc, request.config, request.context)
        
        return {
            "status": "success",
            "plugin_id": plugin_id,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analyze/{plugin_id}/file")
async def analyze_file(
    plugin_id: str,
    file: UploadFile = File(...),
    config: str = Form("{}"),
    context: str = Form("{}")
):
    """Execute an analyzer plugin on uploaded file"""
    try:
        # Parse JSON strings from form data
        config_dict = json.loads(config)
        context_dict = json.loads(context)
        
        # Read file content
        content = await file.read()
        text = content.decode('utf-8')
        
        # Create document
        doc = core.add_document(f"api_upload_{file.filename}", text)
        
        # Execute plugin
        result = core.execute_plugin(plugin_id, doc, config_dict, context_dict)
        
        return {
            "status": "success",
            "plugin_id": plugin_id,
            "filename": file.filename,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/process/{plugin_id}")
async def process(plugin_id: str, request: ProcessRequest):
    """Execute a document processor plugin"""
    try:
        # Create document
        doc = core.add_document(f"api_process_{plugin_id}", request.text)
        
        # Execute plugin
        result = core.execute_plugin(plugin_id, doc, request.config)
        
        # For document processors, the result is usually the processed text
        if isinstance(result, Document):
            result = result.content
        
        return {
            "status": "success",
            "plugin_id": plugin_id,
            "processed_text": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/visualize/{plugin_id}")
async def visualize(plugin_id: str, request: VisualizeRequest):
    """Execute a visualizer plugin"""
    try:
        # Create temporary output file
        suffix = f".{request.output_format}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            output_path = Path(tmp.name)
        
        # Execute visualizer
        plugin = core.plugins.get(plugin_id)
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")
        
        # Visualizers expect: render(data, config, output_path)
        plugin.render(request.data, request.config, output_path)
        
        # Return file based on format
        if request.output_format in ["png", "svg"]:
            # Return as base64 for images
            with open(output_path, "rb") as f:
                content = base64.b64encode(f.read()).decode()
            
            # Clean up
            output_path.unlink()
            
            return {
                "status": "success",
                "plugin_id": plugin_id,
                "format": request.output_format,
                "data": content,
                "encoding": "base64"
            }
        elif request.output_format == "html":
            # Return HTML as text
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Clean up
            output_path.unlink()
            
            return {
                "status": "success",
                "plugin_id": plugin_id,
                "format": "html",
                "data": content,
                "encoding": "utf-8"
            }
        else:
            # For other formats, return file
            return FileResponse(
                output_path,
                media_type=f"application/{request.output_format}",
                filename=f"visualization.{request.output_format}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/pipeline")
async def execute_pipeline(request: PipelineRequest):
    """Execute a pipeline of plugins"""
    try:
        # Create document
        doc = core.add_document("api_pipeline", request.text)
        
        # Convert steps to pipeline config format
        pipeline_config = {
            "name": "API Pipeline",
            "steps": [
                {
                    "plugin": step.plugin_id,
                    "config": step.config
                }
                for step in request.steps
            ]
        }
        
        # Execute pipeline
        results = core.execute_pipeline(doc, pipeline_config)
        
        return {
            "status": "success",
            "pipeline": pipeline_config["name"],
            "steps_executed": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "plugins_loaded": len(core.plugins),
        "plugin_types": {
            "analyzers": len([p for p in core.plugins.values() if p.meta().type.value == "analyzer"]),
            "visualizers": len([p for p in core.plugins.values() if p.meta().type.value == "visualizer"]),
            "document_processors": len([p for p in core.plugins.values() if p.meta().type.value == "document"])
        }
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": f"Internal server error: {str(exc)}"
        }
    )

# Run with: uvicorn qualia.api:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)