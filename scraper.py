import requests
from bs4 import BeautifulSoup
import json

# Function to extract all surf spot URLs
def extract_surf_spot_urls(base_url):
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        spot_links = soup.find_all('a', class_='elementor-button-link')
        spot_urls = [link.get('href') for link in spot_links if link.get('href')]
        return list(set(spot_urls))
    except Exception as e:
        return {"error": f"Error fetching the page: {e}"}

# Function to extract details of each surf spot
def extract_surf_spot_info(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        text_editor_divs = soup.find_all('div', class_='elementor-widget-text-editor')
        categories = [
            "Type of Bottom",
            "Direction of Wave",
            "Best Wind Direction",
            "Best Swell Direction",
            "Swell Size",
            "Length of Wave",
            "Best Season"
        ]

        extracted_info = {
            category: text_editor_divs[idx].get_text(strip=True) if idx < len(text_editor_divs) else "Not available"
            for idx, category in enumerate(categories)
        }

        def get_spot_description():
            container = soup.find('div', class_='elementor-element-2d7b5d4')
            if container:
                paragraphs = container.find_all('p')
                return "\n".join([p.get_text(strip=True) for p in paragraphs])
            return "Spot description not available."

        extracted_info["Spot Description"] = get_spot_description()

        star_containers = soup.find_all('div', class_='elementor-widget-star-rating')
        categories_stars = ["Consistency", "Crowd Factor", "Localism"]
        if len(star_containers) >= 3:
            star_ratings = {
                categories_stars[i]: sum(
                    1 for star in star_containers[i].find_all('i') if 'elementor-star-full' in star.get('class', [])
                )
                for i in range(len(categories_stars))
            }
        else:
            star_ratings = "Not enough star rating containers found."
        extracted_info["Star Ratings"] = star_ratings

        def get_box_colors(container_class):
            container = soup.find('div', class_=container_class)
            if not container:
                return f"Container with class {container_class} not found."
            rects = container.find_all('rect')
            color_mapping = {
                "fill:#000000;stroke-width:1;opacity:0.1;": "light",
                "fill:#000000;": "dark",
                "fill:#9E9B9B;": "grey"
            }
            return [color_mapping.get(rect.get('style', ''), "unknown") for rect in rects]

        extracted_info["Surf Level Box Colors"] = get_box_colors('elementor-widget-rating')
        extracted_info["Best Tide Box Colors"] = get_box_colors('elementor-widget-tideRating')

        return extracted_info
    except Exception as e:
        return {"error": f"Error fetching the page: {e}"}

# Main function to scrape all spots
def scrape_all_surf_spots():
    base_url = "https://www.ericeirasurfhouse.com/surf-spots/"
    print("Extracting surf spot URLs...")
    surf_spot_urls = extract_surf_spot_urls(base_url)

    if isinstance(surf_spot_urls, dict) and "error" in surf_spot_urls:
        print(surf_spot_urls["error"])
        return

    print(f"Found {len(surf_spot_urls)} surf spots.")
    all_spot_info = []
    for url in surf_spot_urls:
        print(f"Scraping details for {url}...")
        spot_info = extract_surf_spot_info(url)
        if "error" in spot_info:
            print(f"  Error for {url}: {spot_info['error']}")
        else:
            all_spot_info.append({"url": url, "details": spot_info})
    return all_spot_info

# Function to save data to JSON
def save_to_json(data, filename="surf_spots.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Data saved to {filename}")

# Run the script
if __name__ == "__main__":
    surf_spot_data = scrape_all_surf_spots()
    if surf_spot_data:
        save_to_json(surf_spot_data)
