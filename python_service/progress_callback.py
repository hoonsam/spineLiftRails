"""
Progress callback system for real-time updates to Rails
"""
import httpx
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ProgressCallback:
    """Handles progress updates and sends them back to Rails"""
    
    def __init__(self, callback_url: Optional[str] = None, job_id: Optional[str] = None):
        self.callback_url = callback_url
        self.job_id = job_id
        self.start_time = datetime.now()
        self.last_progress = 0
        
    async def update(self, progress: int, message: str, data: Optional[Dict[str, Any]] = None):
        """
        Send progress update to Rails
        
        Args:
            progress: Progress percentage (0-100)
            message: Status message
            data: Additional data to send
        """
        if not self.callback_url:
            logger.debug(f"Progress: {progress}% - {message}")
            return
            
        # Only send updates if progress changed significantly (every 5%)
        if abs(progress - self.last_progress) < 5 and progress < 100:
            return
            
        self.last_progress = progress
        
        payload = {
            "job_id": self.job_id,
            "progress": progress,
            "message": message,
            "elapsed_time": (datetime.now() - self.start_time).total_seconds(),
            "data": data or {}
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.callback_url,
                    json=payload,
                    timeout=5.0
                )
                if response.status_code != 200:
                    logger.warning(f"Failed to send progress update: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending progress update: {e}")
            
    async def complete(self, result: Dict[str, Any]):
        """Send completion notification"""
        await self.update(100, "Processing complete", result)
        
    async def error(self, error_message: str):
        """Send error notification"""
        await self.update(-1, f"Error: {error_message}", {"error": True})