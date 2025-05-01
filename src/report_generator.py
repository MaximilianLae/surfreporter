from typing import List, Dict, Any
from openai import OpenAI
from config import OPENAI_API_KEY

class SurfReportGenerator:
    def __init__(
        self,
        spots: List[Dict],
        forecast: Dict,
        generation_model: str = 'gpt-4o',
        temperature: float = 0.3,
        max_tokens: int = 1500
    ):
        self.spots = spots
        self.forecast = forecast
        self.model = generation_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def _format_spot_info(self, spot: Dict) -> str:
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
        sizes = []
        for day in ['saturday', 'sunday']:
            if day in self.forecast:
                d = self.forecast[day]
                sizes.append(f"{day.capitalize()}: {d['swell_height_min']}-{d['swell_height_max']}m")
        return " | ".join(sizes)

    def _get_water_temp(self) -> str:
        temps = []
        for day in ['saturday', 'sunday']:
            if day in self.forecast:
                d = self.forecast[day]
                temps.append(f"{d['sea_surface_temp_min']}-{d['sea_surface_temp_max']}°C")
        return "/".join(sorted(set(temps)))

    def _extract_tide_info(self, description: str) -> str:
        tide_keywords = {'low tide':'Low', 'mid tide':'Mid', 'high tide':'High'}
        found = {label for kw,label in tide_keywords.items() if kw in description.lower()}
        return ", ".join(sorted(found)) or "Not specified"

    def _format_forecast(self) -> str:
        txt = "General Forecast Overview:\n"
        for day,data in self.forecast.items():
            txt += (
                f"{day.capitalize()}:\n"
                f"- Wave Height: {data['swell_height_min']}-{data['swell_height_max']}m\n"
                f"- Swell Period: {data['swell_period_min']}-{data['swell_period_max']}s\n"
                f"- Swell Direction: {data['primary_wave_direction']}\n"
                f"- Water Temp: {data['sea_surface_temp_min']}-{data['sea_surface_temp_max']}°C\n\n"
            )
        return txt

    def _build_merged_spot_details(self) -> str:
        details = "Surf Spot Details:\n"
        for spot in self.spots:
            details += self._format_spot_info(spot) + "\n\n"
        return details.strip()

    def generate_report(self, user_query: str) -> str:
        forecast_text = self._format_forecast()
        spot_text = self._build_merged_spot_details()

        prompt = (
            "You are a professional surf reporter tasked with creating a cohesive weekend surf report.\n\n"
            f"{forecast_text}\n"
            f"{spot_text}\n\n"
            "Using the above data, please write a 300-400 word surf report that:\n"
            "- Explains the forecasted conditions (e.g., wave heights, water temperatures, and tide timings)\n"
            "- Integrates each spot's features (surf level, crowd factor, etc.) with the forecast\n"
            "- Provides recommendations for surfers of various skill levels\n"
            "- Uses smooth transitions to connect the forecast with spot details\n\n"
            "Pay close attention to faithfulness, answer relevancy, and context relevancy.\n\n"
            "Pay a lot of attention to the query that the user gives so you react really to his preferences, this means the user should get the feeling that you react really personally to his query and preferences so he gets the feeling that the report is very personalized."
            f"User Query: {user_query}"
        )

        # Build the two “messages” for the OpenAI call
        role0 = "system" if self.model.startswith("gpt-4") else "developer"
        first_msg = {"role": role0, "content": [{"type":"input_text","text":prompt}]}
        user_msg  = {"role": "user", "content": [{"type":"input_text","text":user_query}]}
        reasoning = {} if self.model.startswith("gpt-4") else {"effort":"medium"}

        # Base kwargs for both models
        call_kwargs = {
            "model": self.model,
            "input": [first_msg, user_msg],
            "text": {"format": {"type": "text"}},
            "reasoning": reasoning,
            "tools": [],
            "store": True,
        }

        # Only GPT-4-family supports these parameters
        if not self.model.startswith("o3-mini"):
            call_kwargs.update({
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "top_p": 1,
            })

        resp = self.client.responses.create(**call_kwargs)

        # Extract the assistant’s text from resp.output
        for item in resp.output:
            if getattr(item, "type", None) == "message":
                return "".join(c.text for c in item.content)

        return ""
