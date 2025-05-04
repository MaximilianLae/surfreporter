import re
from typing import List, Dict, Any
import openai
from pinecone import Pinecone
from config import PINECONE_API_KEY, OPENAI_API_KEY


class SurfSpotRetriever:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY

        pc = Pinecone(api_key=PINECONE_API_KEY, environment="us-east1-aws")
        self.index = pc.Index("surfspots-openai-embedding")

    def _build_metadata_filter(
        self,
        preferred_direction: str,
        preferred_bottom: str
    ) -> Dict[str, Any]:
        """Use EXACT MATCH filtering"""
        return {
            "direction_of_wave": {"$eq": preferred_direction.strip().capitalize()},
            "type_of_bottom":    {"$eq": preferred_bottom.strip().capitalize()}
        }

    def retrieve_spots(
        self,
        user_query: str,
        preferred_direction: str,
        preferred_bottom: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Combined metadata filtering and semantic search.
        Returns sorted list of spots with relevance scores.
        """
        # 1) Embed the user's query via OpenAI
        resp = openai.embeddings.create(
            model="text-embedding-3-large",
            input=user_query
        )
        query_embedding = resp.data[0].embedding

        # 2) Build metadata filter
        metadata_filter = self._build_metadata_filter(
            preferred_direction,
            preferred_bottom
        )

        # 3) Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            filter=metadata_filter,
            include_metadata=True
        )

        # 4) Extract and format matches
        return self._format_results(results.matches)

    def _format_results(self, matches: List[Any]) -> List[Dict[str, Any]]:
        """Standardize result format and add calculated fields"""
        formatted = []
        for match in matches:
            meta = match.metadata
            formatted.append({
                "spot_id":        match.id,
                "name":           meta["name"],
                "description":    meta["spot_description"],
                "wave_direction": meta["direction_of_wave"],
                "bottom_type":    meta["type_of_bottom"],
                "relevance_score": match.score,
                "surf_level":     self._extract_surf_level(meta["spot_description"]),
                "crowd_factor":   self._extract_crowd_info(meta["spot_description"])
            })
        # sort highest score first
        return sorted(formatted, key=lambda x: x["relevance_score"], reverse=True)

    def _extract_surf_level(self, description: str) -> str:
        """Parse surf level with support for ranges and multiple skill levels"""
        clean_desc = description.lower().replace("-", " ").replace("pro", "expert")

        # Range pattern matching
        range_pattern = r"(?:from|for|suitable for)\s+(\w+)(?:\s+to\s+|\s+-\s+)(\w+)"
        m = re.search(range_pattern, clean_desc)
        if m:
            min_level = self._standardize_level(m.group(1))
            max_level = self._standardize_level(m.group(2))
            return f"{min_level} to {max_level}"

        # Individual level detection
        levels = []
        level_keywords = {
            'beginner':    'Beginner',
            'novice':      'Beginner',
            'intermediate':'Intermediate',
            'advanced':    'Advanced',
            'expert':      'Expert'
        }
        for kw, lvl in level_keywords.items():
            if re.search(rf"\b{kw}\b", clean_desc):
                levels.append(lvl)
        if levels:
            order = ['Beginner', 'Intermediate', 'Advanced', 'Expert']
            unique = sorted(set(levels), key=lambda x: order.index(x))
            return " to ".join(unique)

        return "Not Specified"

    def _standardize_level(self, level: str) -> str:
        """Normalize level names"""
        mapping = {
            'beginner': 'Beginner',
            'novice':   'Beginner',
            'intermediate': 'Intermediate',
            'advance':  'Advanced',  # handle typo
            'advanced': 'Advanced',
            'expert':   'Expert',
            'pro':      'Expert'
        }
        return mapping.get(level.strip().lower(), 'Not Specified')

    def _extract_crowd_info(self, description: str) -> str:
        """Parse crowd factor with support for various phrasings"""
        clean_desc = description.lower()
        patterns = {
            'High':   r"(high|very busy|crowded)\s+(crowd|people|surfers)",
            'Medium': r"(moderate|average|regular)\s+(crowd|people|surfers)",
            'Low':    r"(low|light|few|quiet)\s+(crowd|people|surfers)"
        }
        for label, pat in patterns.items():
            if re.search(pat, clean_desc):
                return label
        return "Not Specified"