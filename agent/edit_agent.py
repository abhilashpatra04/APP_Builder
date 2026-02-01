from typing import Optional

from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from agent.tools import write_file, read_file
from agent.file_locator import FileLocator


edit_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


class EditAgent:
    def __init__(self, project_files: list[str]):
        self.project_files = project_files
        self.file_locator = FileLocator(project_files)
        self.tools = [read_file, write_file]

    def process_edit_request(self, user_message: str) -> dict:
        affected_files = self.file_locator.identify_files(user_message)
        
        # Load content for identified files (or sample if none found)
        file_contents = {}
        files_to_load = affected_files if affected_files else self.project_files[:5]
        
        for filepath in files_to_load:
            content = read_file.invoke({"path": filepath})
            file_contents[filepath] = content

        prompt = self._build_edit_prompt(user_message, file_contents, affected_files)
        
        agent = create_react_agent(edit_llm, self.tools)
        
        try:
            messages = [
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]}
            ]
            result = agent.invoke({"messages": messages})
            
            new_contents = {}
            for filepath in affected_files:
                new_content = read_file.invoke({"path": filepath})
                if new_content != file_contents.get(filepath):
                    new_contents[filepath] = {
                        "before": file_contents.get(filepath, ""),
                        "after": new_content
                    }
            
            last_message = result.get("messages", [])[-1] if result.get("messages") else None
            output = last_message.content if last_message else ""
            
            return {
                "status": "success",
                "affected_files": affected_files,
                "changes": new_contents,
                "agent_output": output
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent_output": f"An error occurred: {str(e)}",
                "affected_files": affected_files
            }

    def _build_edit_prompt(self, user_message: str, file_contents: dict, affected_files: list) -> dict:
        files_text = "\n\n".join([
            f"### {filepath}\n```\n{content}\n```"
            for filepath, content in file_contents.items()
        ])
        
        # Group files by directory for structure info
        file_structure = {}
        for f in self.project_files:
            parts = f.split('/')
            dir_path = '/'.join(parts[:-1]) if len(parts) > 1 else '.'
            if dir_path not in file_structure:
                file_structure[dir_path] = []
            file_structure[dir_path].append(parts[-1])
        
        structure_text = "\n".join([
            f"📁 {dir}: {len(files)} files ({', '.join(files)})"
            for dir, files in sorted(file_structure.items())
        ])

        system = f"""You are an expert code assistant with 15+ years of experience.

PROJECT STRUCTURE ({len(self.project_files)} total files):
{structure_text}

LOADED FILE CONTENTS:
{files_text}

YOUR CAPABILITIES:
1. ANSWER QUESTIONS: Answer questions about the project structure or code.
2. EDIT CODE: If the user requests changes, use write_file(path, content) to save.

RULES:
- For questions, just answer directly without calling any tools.
- For edits, use write_file(path, content) to save changes.
- Keep answers concise and helpful."""

        is_edit = any(word in user_message.lower() for word in ['change', 'edit', 'update', 'add', 'remove', 'fix', 'modify', 'make'])
        
        if is_edit and affected_files:
            user = f"USER REQUEST: {user_message}\n\nMake the requested changes and use write_file to save."
        else:
            user = f"USER QUESTION: {user_message}"

        return {"system": system, "user": user}


def process_edit(user_message: str, project_files: list[str]) -> dict:
    agent = EditAgent(project_files)
    return agent.process_edit_request(user_message)
