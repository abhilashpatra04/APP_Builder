"""
Checkpoint Management System for APP_Builder

Manages state persistence for file-based code generation:
- Saves file-level progress to disk
- Enables resume from failure
- Tracks dependencies for proper ordering
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a file task in the execution queue."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FileSpec(BaseModel):
    """Specification for a file to be generated (HTML, CSS, JS, etc.)."""
    id: str = Field(description="Unique identifier (e.g., 'file_001')")
    file: str = Field(description="Target file path")
    file_type: str = Field(description="Type of file: html, css, js, json, etc.")
    description: str = Field(description="Purpose of the file")
    content_spec: str = Field(description="Detailed content specification")
    dependencies: list[str] = Field(default_factory=list, description="IDs of files this depends on")
    
    # Execution state
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    attempts: int = Field(default=0, description="Number of generation attempts")
    last_error: Optional[str] = Field(default=None, description="Last error message if failed")
    generated_content: Optional[str] = Field(default=None, description="The generated content")


class Checkpoint(BaseModel):
    """
    Persistent checkpoint for file-based code generation.
    Saved to disk after each file completion for resume capability.
    """
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str = Field(description="Name of the project being generated")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Global context shared across all files (interface contracts)
    global_context: str = Field(default="", description="DOM contracts, data attributes, shared state")
    
    # Files to generate
    files: list[FileSpec] = Field(default_factory=list)
    
    # Execution order (by dependencies)
    execution_order: list[str] = Field(default_factory=list, description="File IDs in execution order")
    
    # Metadata
    total_files: int = Field(default=0)
    completed_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    
    def save(self, path: str | Path) -> None:
        """Save checkpoint to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.updated_at = datetime.now().isoformat()
        self._update_counts()
        path.write_text(self.model_dump_json(indent=2))
    
    @classmethod
    def load(cls, path: str | Path) -> "Checkpoint":
        """Load checkpoint from disk."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {path}")
        data = json.loads(path.read_text())
        return cls.model_validate(data)
    
    @classmethod
    def load_or_create(cls, path: str | Path, project_name: str = "") -> "Checkpoint":
        """Load existing checkpoint or create new one."""
        path = Path(path)
        if path.exists():
            return cls.load(path)
        return cls(project_name=project_name)
    
    def _update_counts(self) -> None:
        """Update completion counters."""
        self.total_files = len(self.files)
        self.completed_count = sum(1 for f in self.files if f.status == TaskStatus.COMPLETED)
        self.failed_count = sum(1 for f in self.files if f.status == TaskStatus.FAILED)
    
    def get_file_by_id(self, file_id: str) -> Optional[FileSpec]:
        """Get a file by its ID."""
        for f in self.files:
            if f.id == file_id:
                return f
        return None
    
    def is_file_completed(self, file_id: str) -> bool:
        """Check if a file is completed."""
        f = self.get_file_by_id(file_id)
        return f is not None and f.status == TaskStatus.COMPLETED
    
    def get_next_pending(self) -> Optional[FileSpec]:
        """
        Get the next file to execute based on execution order.
        Only returns files whose dependencies are all completed.
        """
        for file_id in self.execution_order:
            f = self.get_file_by_id(file_id)
            if f is None or f.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            deps_satisfied = all(
                self.is_file_completed(dep_id)
                for dep_id in f.dependencies
            )
            
            if deps_satisfied:
                return f
        
        return None
    
    def mark_running(self, file_id: str) -> None:
        """Mark a file as currently running."""
        f = self.get_file_by_id(file_id)
        if f:
            f.status = TaskStatus.RUNNING
            f.attempts += 1
    
    def mark_completed(self, file_id: str, content: str = "") -> None:
        """Mark a file as successfully completed."""
        f = self.get_file_by_id(file_id)
        if f:
            f.status = TaskStatus.COMPLETED
            f.generated_content = content
            f.last_error = None
    
    def mark_failed(self, file_id: str, error: str) -> None:
        """Mark a file as failed."""
        f = self.get_file_by_id(file_id)
        if f:
            f.status = TaskStatus.FAILED
            f.last_error = error
    
    def reset_for_retry(self, file_id: str) -> None:
        """Reset a failed file to pending for retry."""
        f = self.get_file_by_id(file_id)
        if f:
            f.status = TaskStatus.PENDING
    
    def is_complete(self) -> bool:
        """Check if all files are completed or failed."""
        return all(
            f.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            for f in self.files
        )
    
    def get_progress(self) -> str:
        """Get a human-readable progress string."""
        self._update_counts()
        return f"{self.completed_count}/{self.total_files} completed, {self.failed_count} failed"


def get_checkpoint_path(project_name: str, base_dir: str = ".appbuilder") -> Path:
    """Get the checkpoint file path for a project."""
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)
    return Path(base_dir) / "checkpoints" / f"{safe_name}.json"
