"""
Manual test for error recovery with retry logic.
This script demonstrates the retry behavior by forcing failures.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.graph import agent

def test_error_recovery_manual():
    """
    Manual test to verify retry logic works.
    
    To test:
    1. Temporarily modify agent/graph.py coder_agent to force failures
    2. Run this script
    3. Observe retry attempts with exponential backoff
    4. Remove the forced failure code
    """
    
    print("=" * 60)
    print("🧪 Manual Error Recovery Test")
    print("=" * 60)
    print()
    print("Instructions:")
    print("1. Edit agent/graph.py, in coder_agent function")
    print("2. Add BEFORE line 99 (react_agent.invoke):")
    print()
    print("   # TEMPORARY: Force failure for testing")
    print("   if attempt < 2:  # Fail first 2 attempts")
    print("       raise Exception('Simulated failure')")
    print()
    print("3. Save and run: python test_error_recovery.py")
    print("4. Expected: See 2 failures, then success")
    print("5. Remove the test code when done")
    print()
    print("=" * 60)
    
    choice = input("\\nReady to test? (y/n): ")
    
    if choice.lower() != 'y':
        print("Test cancelled. Add the test code and try again!")
        return
    
    print("\\n🚀 Starting test generation...")
    print("-" * 60)
    
    try:
        result = agent.invoke(
            {"user_prompt": "Build a simple HTML page with a single button that says Hello"},
            {"recursion_limit": 100}
        )
        
        print("-" * 60)
        print("✅ Test completed!")
        print()
        print("Check the output above for:")
        print("  - ⚠️  Attempt 1/3 failed messages")
        print("  - 🔄 Retrying in Xs... messages")
        print("  - 💾 Saved checkpoint messages")
        print()
        print("Checkpoint file location:")
        checkpoint_path = Path(".appbuilder/checkpoints")
        if checkpoint_path.exists():
            for cp in checkpoint_path.glob("*.json"):
                print(f"  📁 {cp}")
                # Load and check attempts
                import json
                data = json.loads(cp.read_text())
                for file in data.get('files', []):
                    attempts = file.get('attempts', 0)
                    if attempts > 0:
                        print(f"     File: {file['file']}")
                        print(f"     Attempts: {attempts}")
                        print(f"     Last error: {file.get('last_error', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_error_recovery_manual()
