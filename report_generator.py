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
        self.model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')
        
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
        return (
            f"Spot: {spot['name']}\n"
            f"Description: {spot['description'][:200]}...\n"
            f"Surf Level: {spot['surf_level']}\n"
            f"Crowd Factor: {spot['crowd_factor']}\n"
            f"Wave Size: {self._get_wave_size(spot['name'])}\n"
            f"Water Temp: {self._get_water_temp()}\n"
            f"Best Tide: {self._extract_tide_info(spot['description'])}"
        )

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
        found = set()
        lower_desc = description.lower()
        for kw, label in tide_keywords.items():
            if kw in lower_desc:
                found.add(label)
        return ", ".join(sorted(found)) if found else "Not specified"

    def _format_forecast(self) -> str:
        """Enhanced forecast formatting with dynamic descriptions"""
        forecast_text = "General Forecast Overview:\n"
        for day, data in self.forecast.items():
            forecast_text += (
                f"{day.capitalize()}:\n"
                f"- Wave Height: {data['swell_height_min']}-{data['swell_height_max']}m\n"
                f"- Swell Period: {data['swell_period_min']}-{data['swell_period_max']}s\n"
                f"- Swell Direction: {data['primary_wave_direction']}\n"
                f"- Water Temperature: {data['sea_surface_temp_min']}-{data['sea_surface_temp_max']}°C\n\n"
            )
        return forecast_text

    def _build_merged_spot_details(self) -> str:
        """
        Merge each spot's details with relevant forecast data into a cohesive block.
        You can later improve this function by, for example, matching forecast
        conditions to a spot's preferred tide if needed.
        """
        details = "Surf Spot Details:\n"
        for spot in self.spots:
            details += self._format_spot_info(spot) + "\n\n"
        return details.strip()

    def generate_report(self, user_query: str) -> str:
        """
        Build a prompt that clearly delineates a general forecast section
        and a surf spot section, and instruct the model to create a flowing,
        integrated narrative.
        """
        # Build sections of the prompt
        forecast_overview = self._format_forecast()
        spot_details = self._build_merged_spot_details()

        prompt = f"""
        You are a professional surf reporter tasked with creating a cohesive weekend surf report.
        The report should flow as a single narrative that naturally integrates both the general forecast conditions
        and the detailed characteristics of each surf spot.

        {forecast_overview}

        {spot_details}

        Using the above data, please write a 300-400 word surf report that:
        - Explains the forecasted conditions (e.g., wave heights, water temperatures, and tide timings)
        - Integrates each spot's features (surf level, crowd factor, etc.) with the forecast,
        offering an analysis of how well the conditions suit the spot.
        - Provides recommendations for surfers of various skill levels.
        - Uses smooth transitions to connect the general forecast with the spot-specific details.

        User Query: {user_query}
        """
        response = self.model.generate_content(
            contents=prompt,
            safety_settings=self.safety_settings,
            generation_config={
                "temperature": 0.3,  # Lower temperature for more factual output
                "max_output_tokens": 1500
            }
        )
        return response.text