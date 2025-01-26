# report_generator.py
from typing import List, Dict, Any
import google.generativeai as genai
from config import GOOGLE_API_KEY
from datetime import datetime

class SurfReportGenerator:
    def __init__(self, spots: List[Dict], forecast: Dict):
        self.spots = spots
        self.forecast = forecast
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Configure safety settings (adjust as needed)
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
        ]

    def _format_spot_info(self, spot: Dict) -> str:
        """Include wave size and water temp in spot info"""
        return f"""
        {spot['name']}:
        - Surf Level: {spot['surf_level']}
        - Crowd Factor: {spot['crowd_factor']}
        - Wave Size Range: {self._get_wave_size(spot['name'])}
        - Water Temp: {self._get_water_temp()}
        - Best Tide: {self._extract_tide_info(spot['description'])}
        - Key Features: {spot['description'][:200]}...
        """

    def _get_wave_size(self, spot_name: str) -> str:
        """Get wave size range from forecast"""
        sizes = []
        for day in ['saturday', 'sunday']:
            if day in self.forecast:
                sizes.append(
                    f"{day.capitalize()}: {self.forecast[day]['swell_height_min']}-{self.forecast[day]['swell_height_max']}m"
                )
        return " | ".join(sizes)

    def _get_water_temp(self) -> str:
        """Get water temp range from forecast"""
        temps = []
        for day in ['saturday', 'sunday']:
            if day in self.forecast:
                temps.append(
                    f"{self.forecast[day]['sea_surface_temp_min']}-{self.forecast[day]['sea_surface_temp_max']}°C"
                )
        return "/".join(sorted(set(temps)))

    def _extract_tide_info(self, description: str) -> str:
        """Extract tide preferences from spot description"""
        tide_keywords = {
            'low tide': 'Low',
            'mid tide': 'Mid',
            'high tide': 'High'
        }
        for kw, label in tide_keywords.items():
            if kw in description.lower():
                return label
        return "Not specified"

    def _format_forecast(self) -> str:
        """Enhanced forecast formatting with emphasized wave sizes"""
        forecast_text = "Detailed Wave Forecast:\n"
        for day, data in self.forecast.items():
            forecast_text += (
                f"{day.capitalize()}:\n"
                f"- Wave Height: {data['swell_height_min']}-{data['swell_height_max']}m (shoulder-high to overhead)\n"
                f"- Swell Period: {data['swell_period_min']}-{data['swell_period_max']}s\n"
                f"- Swell Direction: {data['primary_wave_direction']}\n"
                f"- Water Temperature: {data['sea_surface_temp_min']}-{data['sea_surface_temp_max']}°C\n\n"
            )
        return forecast_text

    def generate_report(self, user_query: str) -> str:
        """Enhanced prompt with explicit wave size requirements"""
        prompt = f"""
        You're a professional surf reporter creating a weekend surf report. 
        Combine this spot information with the weather forecast to create a concise, 
        helpful report for the user. Focus on matching spot characteristics with 
        forecast conditions.

        Create a surf report that MUST INCLUDE:
        1. Specific wave heights in meters and relatable descriptions (e.g., 'knee-high', 'overhead')
        2. Water temperature ranges for both days
        3. Analysis of how forecasted conditions match each spot's requirements
        4. Tide timing recommendations where available
        5. Analyzes each spot's potential based on forecast
        6. Highlights best options for different skill levels
        7. Mentions any crowd/cautionary notes
        8. Keeps paragraphs short (2-3 sentences max)
        9. Total length: 300-400 words


        Example structure:
        "Saturday's NW swell (2.5-3.2m) will create powerful waves at reef breaks... 
        Water temps 15-16°C require 3/2mm wetsuits..."

        User Query: {user_query}
        Surf Spots: {[self._format_spot_info(spot) for spot in self.spots]}
        Forecast: {self._format_forecast()}
        """

        response = self.model.generate_content(
            contents=prompt,
            safety_settings=self.safety_settings,
            generation_config={
                "temperature": 0.3,  # More factual
                "max_output_tokens": 1500
            }
        )
        return response.text