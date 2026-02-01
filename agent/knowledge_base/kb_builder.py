import subprocess
import hashlib
import ast
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

from agent.knowledge_base.curated_repos import get_high_priority_repos


@dataclass
class CodeChunk:
    id: str
    code: str
    file_path: str
    chunk_type: str
    category: str
    repo_url: str


class TechStackKnowledgeBuilder:
    def __init__(self, base_path: str = ".appbuilder"):
        self.base_path = Path(base_path)
        self.kb_path = self.base_path / "knowledge_bases"

    def build_tech_kb(self, tech_stack: str, max_repos: Optional[int] = None) -> dict:
        if chromadb is None:
            raise ImportError("chromadb required. Run: pip install chromadb")

        repos = get_high_priority_repos(tech_stack)
        if max_repos:
            repos = repos[:max_repos]

        tech_kb_path = self.kb_path / tech_stack
        chroma_path = tech_kb_path / "chroma"
        repos_path = tech_kb_path / "repos"
        
        chroma_path.mkdir(parents=True, exist_ok=True)
        repos_path.mkdir(parents=True, exist_ok=True)

        client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        collection = client.get_or_create_collection(
            name=f"{tech_stack}_patterns",
            metadata={"tech_stack": tech_stack}
        )

        total_chunks = 0
        for repo_info in repos:
            try:
                repo_path = self._clone_repo(repo_info["url"], repos_path)
                chunks = self._extract_chunks(repo_path, repo_info, tech_stack)
                
                for chunk in chunks:
                    collection.upsert(
                        documents=[chunk.code],
                        metadatas=[{
                            "file_path": chunk.file_path,
                            "chunk_type": chunk.chunk_type,
                            "category": chunk.category,
                            "repo": chunk.repo_url
                        }],
                        ids=[chunk.id]
                    )
                    total_chunks += 1
                    
            except Exception as e:
                print(f"Error processing {repo_info['url']}: {e}")

        return {"tech_stack": tech_stack, "total_chunks": total_chunks, "repos_processed": len(repos)}

    def _clone_repo(self, url: str, repos_path: Path) -> Path:
        repo_name = url.split("/")[-1].replace(".git", "")
        repo_path = repos_path / repo_name

        if repo_path.exists():
            return repo_path

        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(repo_path)],
            capture_output=True,
            check=True
        )
        return repo_path

    def _extract_chunks(self, repo_path: Path, repo_info: dict, tech_stack: str) -> list[CodeChunk]:
        chunks = []
        extract_paths = repo_info.get("extract_paths", ["**/*"])
        category = repo_info.get("category", "general")

        for pattern in extract_paths:
            if pattern.startswith("!"):
                continue
            for file_path in repo_path.glob(pattern):
                if not file_path.is_file():
                    continue
                new_chunks = self._parse_file(file_path, tech_stack, category, repo_info["url"])
                chunks.extend(new_chunks)

        return chunks

    def _parse_file(self, file_path: Path, tech_stack: str, category: str, repo_url: str) -> list[CodeChunk]:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        suffix = file_path.suffix.lower()
        
        if tech_stack == "python" or suffix == ".py":
            return self._parse_python(content, str(file_path), category, repo_url)
        elif tech_stack in ("react", "vue") or suffix in (".tsx", ".jsx", ".vue"):
            return self._parse_jsx_vue(content, str(file_path), category, repo_url)
        elif suffix in (".ts", ".js", ".mjs"):
            return self._parse_javascript(content, str(file_path), category, repo_url)
        else:
            return self._parse_generic(content, str(file_path), category, repo_url)

    def _parse_python(self, content: str, file_path: str, category: str, repo_url: str) -> list[CodeChunk]:
        chunks = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._parse_generic(content, file_path, category, repo_url)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                chunk_code = ast.get_source_segment(content, node)
                if chunk_code and len(chunk_code) > 50:
                    chunks.append(CodeChunk(
                        id=self._generate_id(file_path, node.name),
                        code=chunk_code,
                        file_path=file_path,
                        chunk_type="function",
                        category=category,
                        repo_url=repo_url
                    ))
            elif isinstance(node, ast.ClassDef):
                chunk_code = ast.get_source_segment(content, node)
                if chunk_code and len(chunk_code) > 100:
                    chunks.append(CodeChunk(
                        id=self._generate_id(file_path, node.name),
                        code=chunk_code,
                        file_path=file_path,
                        chunk_type="class",
                        category=category,
                        repo_url=repo_url
                    ))

        return chunks if chunks else self._parse_generic(content, file_path, category, repo_url)

    def _parse_jsx_vue(self, content: str, file_path: str, category: str, repo_url: str) -> list[CodeChunk]:
        chunks = []
        
        component_pattern = r'(?:export\s+(?:default\s+)?)?(?:function|const)\s+(\w+)\s*[=\(]'
        matches = re.finditer(component_pattern, content)
        
        for match in matches:
            start = match.start()
            depth = 0
            end = start
            
            for i, char in enumerate(content[start:], start):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            
            chunk_code = content[start:end]
            if len(chunk_code) > 100:
                chunks.append(CodeChunk(
                    id=self._generate_id(file_path, match.group(1)),
                    code=chunk_code,
                    file_path=file_path,
                    chunk_type="component",
                    category=category,
                    repo_url=repo_url
                ))

        return chunks if chunks else self._parse_generic(content, file_path, category, repo_url)

    def _parse_javascript(self, content: str, file_path: str, category: str, repo_url: str) -> list[CodeChunk]:
        return self._parse_jsx_vue(content, file_path, category, repo_url)

    def _parse_generic(self, content: str, file_path: str, category: str, repo_url: str) -> list[CodeChunk]:
        if len(content) < 100:
            return []
        
        chunk_size = 2000
        chunks = []
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            if len(chunk) > 100:
                chunks.append(CodeChunk(
                    id=self._generate_id(file_path, str(i)),
                    code=chunk,
                    file_path=file_path,
                    chunk_type="generic",
                    category=category,
                    repo_url=repo_url
                ))

        return chunks

    def _generate_id(self, file_path: str, identifier: str) -> str:
        return hashlib.md5(f"{file_path}:{identifier}".encode()).hexdigest()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m agent.knowledge_base.kb_builder <tech_stack>")
        print("Example: python -m agent.knowledge_base.kb_builder react")
        sys.exit(1)
    
    tech_stack = sys.argv[1]
    max_repos = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    builder = TechStackKnowledgeBuilder()
    result = builder.build_tech_kb(tech_stack, max_repos)
    print(f"Built KB: {result}")
