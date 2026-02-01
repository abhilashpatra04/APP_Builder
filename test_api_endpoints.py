#!/usr/bin/env python3
"""
Quick test script to populate API with existing projects for testing
Run this, then test your API endpoints without generating new projects
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from api.store import PROJECT_TRACKING
from agent.checkpoint import get_checkpoint_path

def setup_test_projects():
    """Load existing checkpoints into PROJECT_TRACKING for testing"""
    
    # Existing projects based on checkpoint files
    test_projects = {
        "calc-123": "Calculator App",
        "todo-456": "Colourful Modern Todo App", 
        "todo-789": "Colourful Todo App"
    }
    
    print("🧪 Setting up test projects...")
    print("=" * 50)
    
    for project_id, project_name in test_projects.items():
        checkpoint_path = get_checkpoint_path(project_name)
        
        if checkpoint_path.exists():
            PROJECT_TRACKING[project_id] = str(checkpoint_path)
            print(f"✅ {project_id:12} → {project_name}")
        else:
            print(f"❌ {project_id:12} → Not found: {checkpoint_path}")
    
    print("=" * 50)
    print(f"📊 Loaded {len(PROJECT_TRACKING)} projects")
    print("\n🎯 Test these endpoints now:")
    print(f"   curl http://localhost:8000/api/projects/calc-123/status")
    print(f"   curl http://localhost:8000/api/projects/todo-456/status")
    print(f"   curl http://localhost:8000/api/projects/todo-789/status")
    
    return PROJECT_TRACKING

if __name__ == "__main__":
    setup_test_projects()
