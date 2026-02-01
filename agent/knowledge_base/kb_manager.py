import json
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None


class KnowledgeBaseManager:
    def __init__(self, base_path: str = ".appbuilder"):
        self.base_path = Path(base_path)
        self.registry_path = self.base_path / "config" / "tech_stack_registry.json"
        self.registry = self._load_registry()
        self._loaded_collections: dict = {}

    def _load_registry(self) -> dict:
        if not self.registry_path.exists():
            return {"tech_stacks": {}}
        return json.loads(self.registry_path.read_text())

    def _save_registry(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(json.dumps(self.registry, indent=2))

    def get_available_techs(self) -> list[str]:
        return list(self.registry.get("tech_stacks", {}).keys())

    def get_tech_info(self, tech_stack: str) -> Optional[dict]:
        return self.registry.get("tech_stacks", {}).get(tech_stack)

    def _get_collection(self, tech_stack: str):
        if chromadb is None:
            raise ImportError("chromadb not installed. Run: pip install chromadb")
        
        if tech_stack in self._loaded_collections:
            return self._loaded_collections[tech_stack]

        tech_info = self.get_tech_info(tech_stack)
        if not tech_info:
            raise ValueError(f"Unknown tech stack: {tech_stack}")

        kb_path = Path(tech_info["kb_path"]) / "chroma"
        kb_path.mkdir(parents=True, exist_ok=True)
        
        client = chromadb.PersistentClient(
            path=str(kb_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_or_create_collection(
            name=f"{tech_stack}_patterns",
            metadata={"tech_stack": tech_stack}
        )
        
        self._loaded_collections[tech_stack] = collection
        return collection

    def query_single_tech(
        self,
        tech_stack: str,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None
    ) -> list[dict]:
        collection = self._get_collection(tech_stack)
        
        where_filter = None
        if category:
            where_filter = {"category": category}

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )

        return self._format_results(results, tech_stack)

    def query_multiple_techs(
        self,
        tech_stacks: list[str],
        query: str,
        n_results_per_tech: int = 3
    ) -> dict[str, list[dict]]:
        results = {}
        
        with ThreadPoolExecutor(max_workers=len(tech_stacks)) as executor:
            futures = {
                executor.submit(
                    self.query_single_tech, tech, query, n_results_per_tech
                ): tech
                for tech in tech_stacks
            }
            for future in futures:
                tech = futures[future]
                try:
                    results[tech] = future.result()
                except Exception as e:
                    results[tech] = [{"error": str(e)}]

        return results

    def _format_results(self, raw_results: dict, tech_stack: str) -> list[dict]:
        if not raw_results or not raw_results.get("documents"):
            return []

        formatted = []
        documents = raw_results["documents"][0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        for i, doc in enumerate(documents):
            formatted.append({
                "code": doc,
                "tech_stack": tech_stack,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "relevance_score": 1 - (distances[i] if i < len(distances) else 0)
            })

        return formatted

    def get_stats(self) -> dict:
        stats = {}
        for tech in self.get_available_techs():
            info = self.get_tech_info(tech)
            stats[tech] = {
                "total_chunks": info.get("total_chunks", 0),
                "total_repos": info.get("total_repos", 0),
                "status": info.get("status", "inactive")
            }
        return stats

    def update_tech_stats(self, tech_stack: str, chunks: int, repos: int) -> None:
        if tech_stack in self.registry["tech_stacks"]:
            self.registry["tech_stacks"][tech_stack]["total_chunks"] = chunks
            self.registry["tech_stacks"][tech_stack]["total_repos"] = repos
            self._save_registry()
