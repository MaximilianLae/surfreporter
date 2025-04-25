import json

# Transformation Functions
def describe_star_ratings(star_ratings):
    # Ensure star_ratings is a dictionary
    if not isinstance(star_ratings, dict):
        return "Invalid Star Ratings data format."
    
    # Define five-category mapping
    rating_descriptions = {
        1: "Very low",
        2: "Low",
        3: "Moderate",
        4: "High",
        5: "Very high"
    }
    
    # Extract individual ratings
    consistency = star_ratings.get("Consistency", 0)
    crowd_factor = star_ratings.get("Crowd Factor", 0)
    localism = star_ratings.get("Localism", 0)
    
    return {
        "Consistency": f"{rating_descriptions.get(consistency, 'No data')} consistency",
        "Crowd Factor": f"{rating_descriptions.get(crowd_factor, 'No data')} crowd factor",
        "Localism": f"{rating_descriptions.get(localism, 'No data')} sense of localism"
    }

def describe_surf_level(surf_level_array):
    # Define surf level categories (8 levels)
    surf_levels = ["beginner", "beginner-intermediate", "intermediate", 
                   "intermediate-advanced", "advanced", "advanced-pro", "pro", "expert-pro"]
    
    # Validate input
    if not isinstance(surf_level_array, list) or len(surf_level_array) != len(surf_levels):
        return "Invalid Surf Level data format."
    
    # Find indices of "dark" fields
    dark_indices = [i for i, value in enumerate(surf_level_array) if value == "dark"]
    
    if not dark_indices:
        return "Not suitable for any surf level."
    
    # Calculate center of mass and spread
    center_index = sum(dark_indices) / len(dark_indices)
    spread = max(dark_indices) - min(dark_indices)
    
    # Map indices to surf levels
    primary_level = surf_levels[round(center_index)]
    start_level = surf_levels[max(0, min(dark_indices))]
    end_level = surf_levels[min(len(surf_levels) - 1, max(dark_indices))]
    
    # Determine description
    if len(dark_indices) == len(surf_level_array):
        return "suitable for all surf levels"
    elif spread <= 2:
        return f"best suited for {primary_level}"
    else:
        return f"most suitable from {start_level} to {end_level}"

def describe_tide(tide_array):
    tide_phases = ["low tide", "mid-low tide", "mid tide", "mid-high tide", "high tide"]
    dark_indices = [i for i, value in enumerate(tide_array) if value == "dark"]
    if not dark_indices:
        return "This spot is not ideal for surfing."
    center_index = sum(dark_indices) / len(dark_indices)
    spread = max(dark_indices) - min(dark_indices)
    primary_phase = tide_phases[round(center_index * (len(tide_phases) - 1) / (len(tide_array) - 1))]
    if spread <= 1:
        return f"best surfable during {primary_phase}"
    elif spread <= 3:
        return f"surfable from {tide_phases[max(0, min(dark_indices))]} to {tide_phases[min(len(tide_phases) - 1, max(dark_indices))]}"
    else:
        return "surfable across most tide levels"

# Enrichment Function
def enrich_spot_description(spot):
    """Enrich the Spot Description with additional details."""
    details = spot["details"]

    # Base Spot Description
    description = details.get("Spot Description", "")

    # Star Ratings Description (ensure it's a dictionary)
    star_ratings = details.get("Star Ratings Description", {})
    if isinstance(star_ratings, str):
        star_ratings = {}

    consistency = star_ratings.get("Consistency", "No consistency information")
    crowd_factor = star_ratings.get("Crowd Factor", "No crowd factor information")
    localism = star_ratings.get("Localism", "No localism information")

    # Surf Level Description
    surf_level_description = details.get("Surf Level Description", "No surf level description available.")

    # Tide Description
    tide_description = details.get("Tide Description", "No tide description available.")

    # Combine all parts into an enriched description
    enriched_description = (
        f"{description}\n\n"
        f"The spot has {consistency}, {crowd_factor}, and {localism}.\n"
        f"Surf level: {surf_level_description}\n"
        f"Tide information: {tide_description}"
    )

    # Update the Spot Description in the original data
    details["Spot Description"] = enriched_description
    return spot

# Combined Workflow
def transform_and_enrich_surf_spots(input_file, output_file):
    # Load the JSON file
    with open(input_file, "r") as file:
        surf_spots = json.load(file)
    
    # Transform and enrich each surf spot
    for spot in surf_spots:
        details = spot["details"]
        
        # Apply transformations
        details["Star Ratings Description"] = describe_star_ratings(details["Star Ratings"])
        details["Surf Level Description"] = describe_surf_level(details["Surf Level Box Colors"])
        details["Tide Description"] = describe_tide(details["Best Tide Box Colors"])
        
        # Enrich the description
        enrich_spot_description(spot)
    
    # Save the transformed and enriched data to a new file
    with open(output_file, "w") as file:
        json.dump(surf_spots, file, indent=4, ensure_ascii=False)

# Example Usage
input_file = "surf_spots.json"
output_file = "surf_spots_enriched.json"
transform_and_enrich_surf_spots(input_file, output_file)

print("Surf spot descriptions have been transformed and enriched!")