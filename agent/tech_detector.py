import json
from pathlib import Path
from typing import Optional

from langchain_groq import ChatGroq


class TechStackDetector:
    def __init__(self, registry_path: str = ".appbuilder/config/tech_stack_registry.json"):
        self.registry_path = Path(registry_path)
        self.registry = self._load_registry()
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

    def _load_registry(self) -> dict:
        if not self.registry_path.exists():
            return {"tech_stacks": {}}
        return json.loads(self.registry_path.read_text())

    def detect(self, user_prompt: str) -> dict:
        available_techs = self._get_tech_summary()
        
        detection_prompt = f"""Analyze this project request and identify required technologies.

User Request: {user_prompt}

Available Tech Stacks:
{json.dumps(available_techs, indent=2)}

Respond ONLY with valid JSON (no markdown, no explanation):
{{
    "frontend": "react" | "vue" | "vanilla" | null,
    "backend": "python" | "nodejs" | null,
    "database": "postgresql" | "mongodb" | "sqlite" | null,
    "deployment": "docker" | null,
    "reasoning": "1-2 sentence explanation of why these techs were chosen"
}}"""

        response = self.llm.invoke(detection_prompt)
        
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            detection = json.loads(content)
        except json.JSONDecodeError:
            detection = self._fallback_detection(user_prompt)

        detection["all_techs"] = self._expand_tech_list(detection)
        return detection

    def _get_tech_summary(self) -> dict:
        summary = {}
        for tech_id, info in self.registry.get("tech_stacks", {}).items():
            summary[tech_id] = {
                "name": info["name"],
                "keywords": info["keywords"][:5]
            }
        return summary

    def _expand_tech_list(self, detection: dict) -> list[str]:
        techs = []
        for key in ["frontend", "backend", "database", "deployment"]:
            value = detection.get(key)
            if value and value != "null" and value in self.registry.get("tech_stacks", {}):
                techs.append(value)
        return techs

    def _fallback_detection(self, prompt: str) -> dict:
        prompt_lower = prompt.lower()
        
        frontend = None
        if any(kw in prompt_lower for kw in ["react", "jsx", "next"]):
            frontend = "react"
        elif any(kw in prompt_lower for kw in ["vue", "nuxt"]):
            frontend = "vue"
        elif any(kw in prompt_lower for kw in ["html", "web", "website"]):
            frontend = "vanilla"

        backend = None
        if any(kw in prompt_lower for kw in ["python", "fastapi", "flask", "django"]):
            backend = "python"
        elif any(kw in prompt_lower for kw in ["node", "express", "nestjs"]):
            backend = "nodejs"

        return {
            "frontend": frontend,
            "backend": backend,
            "database": None,
            "deployment": None,
            "reasoning": "Detected via keyword matching fallback"
        }


def detect_tech_stacks(prompt: str) -> dict:
    detector = TechStackDetector()
    return detector.detect(prompt)
