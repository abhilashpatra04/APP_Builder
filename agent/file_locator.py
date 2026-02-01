import re
from pathlib import Path
from typing import Optional


class FileLocator:
    def __init__(self, project_files: list[str]):
        self.project_files = project_files
        self.file_keywords = self._build_keyword_map()

    def _build_keyword_map(self) -> dict[str, list[str]]:
        keyword_map = {}
        
        for filepath in self.project_files:
            filename = Path(filepath).stem.lower()
            keywords = self._extract_keywords(filename)
            keywords.append(filename)
            keywords.append(Path(filepath).name.lower())
            
            keyword_map[filepath] = keywords
        
        return keyword_map

    def _extract_keywords(self, filename: str) -> list[str]:
        words = re.split(r'[_\-.]', filename)
        words = [w.lower() for w in words if len(w) > 2]
        
        camel_words = re.findall(r'[A-Z][a-z]+|[a-z]+', filename)
        words.extend([w.lower() for w in camel_words if len(w) > 2])
        
        return list(set(words))

    def identify_files(self, user_message: str, max_files: int = 3) -> list[str]:
        message_lower = user_message.lower()
        
        for filepath in self.project_files:
            filename = Path(filepath).name.lower()
            if filename in message_lower:
                return [filepath]
        
        scores = {}
        
        for filepath, keywords in self.file_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
                    if len(keyword) > 5:
                        score += 1
            
            ext = Path(filepath).suffix.lower()
            if self._is_relevant_extension(message_lower, ext):
                score += 1
            
            if score > 0:
                scores[filepath] = score

        sorted_files = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [f[0] for f in sorted_files[:max_files]]

    def _is_relevant_extension(self, message: str, ext: str) -> bool:
        extension_hints = {
            ".css": ["style", "color", "background", "font", "margin", "padding", "css"],
            ".jsx": ["component", "button", "form", "render", "react", "jsx"],
            ".tsx": ["component", "typescript", "tsx"],
            ".py": ["api", "route", "endpoint", "python", "function", "class"],
            ".html": ["page", "html", "template", "layout"],
            ".js": ["script", "function", "javascript", "logic"]
        }
        
        hints = extension_hints.get(ext, [])
        return any(hint in message for hint in hints)

    def get_file_context(self, filepath: str) -> dict:
        return {
            "path": filepath,
            "name": Path(filepath).name,
            "extension": Path(filepath).suffix,
            "keywords": self.file_keywords.get(filepath, [])
        }
