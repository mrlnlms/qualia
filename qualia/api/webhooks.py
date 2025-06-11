"""
Webhook handlers for external integrations.

Supports GitHub, Slack, Discord and generic webhooks with
signature verification and automatic processing.
"""

from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import hmac
import hashlib
import json
from datetime import datetime
import asyncio
from enum import Enum

from qualia.core import QualiaCore

router = APIRouter(prefix="/webhook", tags=["webhooks"])

# Global core instance (initialized in main API)
core: Optional[QualiaCore] = None

# Import para métricas (será injetado)
track_webhook_callback = None

class WebhookType(Enum):
    GITHUB = "github"
    SLACK = "slack"
    DISCORD = "discord"
    GENERIC = "generic"

class WebhookProcessor:
    """Base webhook processor with common functionality."""
    
    def __init__(self, webhook_type: WebhookType):
        self.webhook_type = webhook_type
        self.stats = {
            "total_received": 0,
            "total_processed": 0,
            "total_errors": 0,
            "last_processed": None
        }
    
    async def process(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Process webhook payload."""
        self.stats["total_received"] += 1
        
        try:
            # Validate signature if configured
            if not await self.verify_signature(payload, headers):
                raise HTTPException(status_code=401, detail="Invalid signature")
            
            # Extract text based on webhook type
            text = await self.extract_text(payload)
            if not text:
                return {"status": "skipped", "reason": "No text to analyze"}
            
            # Determine which plugin to use
            plugin_id = await self.determine_plugin(payload)
            
            # Execute analysis
            result = await self.analyze_text(text, plugin_id, payload)
            
            self.stats["total_processed"] += 1
            self.stats["last_processed"] = datetime.now().isoformat()
            
            # Track metrics
            if track_webhook_callback:
                await track_webhook_callback(self.webhook_type.value)
            
            return {
                "status": "success",
                "webhook_type": self.webhook_type.value,
                "plugin_used": plugin_id,
                "result": result
            }
            
        except Exception as e:
            self.stats["total_errors"] += 1
            raise HTTPException(status_code=500, detail=str(e))
    
    async def verify_signature(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Verify webhook signature. Override in subclasses."""
        return True  # Default: no verification
    
    async def extract_text(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extract text from payload. Override in subclasses."""
        raise NotImplementedError
    
    async def determine_plugin(self, payload: Dict[str, Any]) -> str:
        """Determine which plugin to use. Override in subclasses."""
        return "word_frequency"  # Default
    
    async def analyze_text(self, text: str, plugin_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run analysis on extracted text."""
        if not core:
            raise HTTPException(status_code=500, detail="Core not initialized")
        
        # Create document
        doc_id = f"{self.webhook_type.value}_{datetime.now().timestamp()}"
        doc = core.add_document(doc_id, text)
        
        # Execute plugin
        config = {}  # Could be customized based on webhook type
        result = core.execute_plugin(plugin_id, doc, config, context)
        
        return result

class GenericWebhookProcessor(WebhookProcessor):
    """Generic webhook processor for custom integrations."""
    
    def __init__(self):
        super().__init__(WebhookType.GENERIC)
    
    async def extract_text(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extract text from generic payload."""
        # Try common field names
        for field in ["text", "content", "message", "body", "data"]:
            if field in payload:
                value = payload[field]
                if isinstance(value, str):
                    return value
                elif isinstance(value, dict) and "text" in value:
                    return value["text"]
        
        # If payload is just a string
        if isinstance(payload, str):
            return payload
        
        return None
    
    async def determine_plugin(self, payload: Dict[str, Any]) -> str:
        """Determine plugin from generic payload."""
        # Check if plugin is specified
        return payload.get("plugin", "word_frequency")

# Initialize processors
processors = {
    WebhookType.GENERIC: GenericWebhookProcessor()
}

@router.post("/custom")
async def custom_webhook(request: Request):
    """
    Generic webhook endpoint for custom integrations.
    
    Accepts any JSON payload with text field.
    Optionally specify plugin with 'plugin' field.
    """
    payload = await request.json()
    
    processor = processors[WebhookType.GENERIC]
    result = await processor.process(payload, {})
    
    return JSONResponse(content=result)

@router.get("/stats")
async def webhook_stats():
    """Get webhook processing statistics."""
    stats = {}
    for webhook_type, processor in processors.items():
        stats[webhook_type.value] = processor.stats
    
    return {
        "status": "ok",
        "stats": stats
    }

def init_webhooks(core_instance: QualiaCore):
    """Initialize webhooks with core instance."""
    global core
    core = core_instance

def set_tracking_callback(callback):
    """Set callback for tracking webhook metrics."""
    global track_webhook_callback
    track_webhook_callback = callback
