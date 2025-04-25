# search.py
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import PINECONE_API_KEY, GOOGLE_API_KEY
from typing import List, Dict, Any
import re

class SurfSpotRetriever:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY
        )
        self.pinecone = Pinecone(api_key=PINECONE_API_KEY)
        self.index = self.pinecone.Index("surfspots")
    
    def _build_metadata_filter(self, 
                               preferred_direction: str, 
                               preferred_bottom: str) -> Dict[str, Any]:
        """Use EXACT MATCH filtering"""
        
        return {
            "direction_of_wave": {"$eq": preferred_direction.strip().capitalize()},
            "type_of_bottom": {"$eq": preferred_bottom.strip().capitalize()}
        }

    def retrieve_spots(self,
                      user_query: str,
                      preferred_direction: str,
                      preferred_bottom: str,
                      top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Combined metadata filtering and semantic search
        Returns sorted list of spots with relevance scores
        """
        # Generate embedding for the user's free-text query
        query_embedding = self.embeddings.embed_query(user_query)
        
        # Build metadata filter with partial matching
        metadata_filter = self._build_metadata_filter(
            preferred_direction, 
            preferred_bottom
        )
        
        # Execute Pinecone query
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            filter=metadata_filter,
            include_metadata=True
        )
        
        # Process and format results
        return self._format_results(results["matches"])

    def _format_results(self, matches: List[Dict]) -> List[Dict[str, Any]]:
        """Standardize result format and add calculated fields"""
        formatted = []
        for match in matches:
            meta = match["metadata"]
            formatted.append({
                "spot_id": match["id"],
                "name": meta["name"],
                "description": meta["spot_description"],
                "wave_direction": meta["direction_of_wave"],
                "bottom_type": meta["type_of_bottom"],
                "relevance_score": match["score"],
                "surf_level": self._extract_surf_level(meta["spot_description"]),
                "crowd_factor": self._extract_crowd_info(meta["spot_description"])
            })
        return sorted(formatted, key=lambda x: x["relevance_score"], reverse=True)

    def _extract_surf_level(self, description: str) -> str:
        """Parse surf level with support for ranges and multiple skill levels"""
        clean_desc = description.lower().replace("-", " ").replace("pro", "expert")
        
        # Range pattern matching
        range_pattern = r"(?:from|for|suitable for|from)\s+(\w+)(?:\s+to\s+|\s+-\s+)(\w+)"
        range_match = re.search(range_pattern, clean_desc)
        
        if range_match:
            min_level = self._standardize_level(range_match.group(1))
            max_level = self._standardize_level(range_match.group(2))
            return f"{min_level} to {max_level}"
        
        # Individual level detection
        levels = []
        level_keywords = {
            'beginner': 'Beginner',
            'novice': 'Beginner',
            'intermediate': 'Intermediate',
            'advanced': 'Advanced',
            'expert': 'Expert',
            'pro': 'Expert'
        }
        
        for keyword, level in level_keywords.items():
            if re.search(rf"\b{keyword}\b", clean_desc):
                levels.append(level)
        
        if levels:
            unique_levels = sorted(set(levels), key=lambda x: ['Beginner', 'Intermediate', 'Advanced', 'Expert'].index(x))
            return " to ".join(unique_levels)
        
        return "Not Specified"

    def _standardize_level(self, level: str) -> str:
        """Normalize level names"""
        level = level.strip().lower()
        return {
            'beginner': 'Beginner',
            'novice': 'Beginner',
            'intermediate': 'Intermediate',
            'advance': 'Advanced',  # Handle typo
            'advanced': 'Advanced',
            'expert': 'Expert',
            'pro': 'Expert'
        }.get(level, 'Not Specified')

    def _extract_crowd_info(self, description: str) -> str:
        """Parse crowd factor with support for various phrasings"""
        clean_desc = description.lower()
        
        crowd_patterns = {
            'high': r"(high|crowded|busy|very busy)\s+(crowd|people|surfers)",
            'medium': r"(moderate|average|normal|regular)\s+(crowd|people|surfers)",
            'low': r"(low|less|light|quiet|few)\s+(crowd|people|surfers)"
        }
        
        for level, pattern in crowd_patterns.items():
            if re.search(pattern, clean_desc):
                return level.capitalize()
        
        return "Not Specified"