"""Service for managing background tasks."""

import json
import uuid
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

import aiofiles
from loguru import logger


class TaskService:
    """Service for managing background tasks.
    
    This service provides functionality for creating, tracking, and managing
    long-running tasks, with support for progress reporting and persistence.
    """
    
    def __init__(self, storage_dir: str = "tasks"):
        """Initialize the task service.
        
        Args:
            storage_dir: Directory for storing task data
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.active_tasks = {}
    
    async def create_task(self, task_type: str, parameters: Dict[str, Any] = None) -> str:
        """Create a new task and return its ID.
        
        Args:
            task_type: Type of task (e.g., 'catalog_generation')
            parameters: Optional parameters for the task
            
        Returns:
            Task ID (UUID)
        """
        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "type": task_type,
            "parameters": parameters or {},
            "status": "pending",
            "progress": 0,
            "message": "Task created",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        # Save task data
        await self._save_task(task_id, task_data)
        
        # Store in memory
        self.active_tasks[task_id] = task_data
        
        logger.info(f"Created task {task_id} of type {task_type}")
        return task_id
    
    async def update_task_progress(
        self, 
        task_id: str, 
        progress: int, 
        message: str = None
    ) -> None:
        """Update task progress.
        
        Args:
            task_id: ID of the task to update
            progress: Progress percentage (0-100, or -1 for error)
            message: Optional progress message
        """
        task_data = await self.get_task(task_id)
        if not task_data:
            logger.error(f"Task not found: {task_id}")
            raise ValueError(f"Task not found: {task_id}")
            
        # Update progress and message
        task_data["progress"] = progress
        if message:
            task_data["message"] = message
        task_data["updated_at"] = datetime.now().isoformat()
        
        # Handle completion or error
        if progress == 100:
            task_data["status"] = "completed"
            task_data["completed_at"] = datetime.now().isoformat()
            logger.info(f"Task {task_id} completed")
        elif progress < 0:
            task_data["status"] = "error"
            task_data["error"] = message
            task_data["completed_at"] = datetime.now().isoformat()
            logger.error(f"Task {task_id} failed: {message}")
        elif task_data["status"] == "pending" and progress > 0:
            task_data["status"] = "running"
            logger.debug(f"Task {task_id} is now running")
        
        # Save updated task data
        await self._save_task(task_id, task_data)
        
        # Update in-memory cache
        self.active_tasks[task_id] = task_data
    
    async def set_task_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """Set the result data for a completed task.
        
        Args:
            task_id: ID of the task
            result: Result data
        """
        task_data = await self.get_task(task_id)
        if not task_data:
            logger.error(f"Task not found: {task_id}")
            raise ValueError(f"Task not found: {task_id}")
        
        # Update result
        task_data["result"] = result
        await self._save_task(task_id, task_data)
        
        # Update in-memory cache
        self.active_tasks[task_id] = task_data
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task data by ID.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task data dictionary or None if not found
        """
        # Check in-memory cache first
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
            
        # Try to load from storage
        task_path = self.storage_dir / f"{task_id}.json"
        if not task_path.exists():
            return None
            
        try:
            async with aiofiles.open(task_path, "r", encoding="utf-8") as f:
                content = await f.read()
                task_data = json.loads(content)
                
            # Update cache
            self.active_tasks[task_id] = task_data
            return task_data
        except Exception as e:
            logger.error(f"Error loading task {task_id}: {e}")
            return None
    
    async def list_tasks(
        self, 
        status: Optional[str] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filtering.
        
        Args:
            status: Optional status filter
            limit: Maximum number of tasks to return
            offset: Offset for pagination
            
        Returns:
            List of task data dictionaries
        """
        tasks = []
        
        # List files in storage directory
        try:
            task_files = list(self.storage_dir.glob("*.json"))
            
            # Process each file
            for idx, task_path in enumerate(
                sorted(task_files, key=lambda p: p.stat().st_mtime, reverse=True)
            ):
                if idx < offset:
                    continue
                    
                if len(tasks) >= limit:
                    break
                
                try:
                    async with aiofiles.open(task_path, "r", encoding="utf-8") as f:
                        content = await f.read()
                        task_data = json.loads(content)
                    
                    # Apply status filter if provided
                    if status is None or task_data.get("status") == status:
                        tasks.append(task_data)
                        
                        # Update cache
                        self.active_tasks[task_data["id"]] = task_data
                except Exception as e:
                    logger.error(f"Error loading task file {task_path}: {e}")
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
        
        return tasks
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            True if successful, False otherwise
        """
        task_path = self.storage_dir / f"{task_id}.json"
        if not task_path.exists():
            return False
            
        try:
            # Remove file
            os.remove(task_path)
            
            # Remove from cache
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                
            logger.info(f"Deleted task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False
    
    async def _save_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """Save task data to storage.
        
        Args:
            task_id: ID of the task
            task_data: Task data to save
        """
        task_path = self.storage_dir / f"{task_id}.json"
        try:
            async with aiofiles.open(task_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(task_data, indent=2))
        except Exception as e:
            logger.error(f"Error saving task {task_id}: {e}")
            raise 