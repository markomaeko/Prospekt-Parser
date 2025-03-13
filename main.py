import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime

class BrochureParser:
    def __init__(self, url):
        self.url = url
        self.brochures = []
        self.notice = ""

    def fetch_page(self):
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching the page: {e}")
            raise


    def parse_date_range(self, date_text):
        try:
            # Edge case: "von day.weekday day.month.year" format
            if "von" in date_text:  
                match = re.search(r'\d{2}\.\d{2}\.\d{4}', date_text)
                valid_from = datetime.strptime(match.group(), '%d.%m.%Y').strftime('%Y-%m-%d') if match else "Unknown"
                valid_to = "Unknown"
            # Standard case: "day.month.year - day.month.year"
            else:  
                date_parts = [d.strip() for d in date_text.split('-')]
                valid_from, valid_to = [
                    datetime.strptime(d, '%d.%m.%Y').strftime('%Y-%m-%d') for d in date_parts
                ]
        except Exception as e:
            print(f"Error parsing date range: {e}")
            valid_from, valid_to = "Unknown", "Unknown"

        return valid_from, valid_to

    def parse_page(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        brochure_items = soup.select('.letak-description')
    
        for item in brochure_items:
            title = item.select_one('.grid-item-content strong').get_text(strip=True) if item.select_one('.grid-item-content strong') else "Unknown"
            picture_tag = item.select_one('.grid-logo picture img')
            thumbnail = picture_tag.get('data-src', picture_tag.get('src', '')).strip() if picture_tag else ""
            shop_name = picture_tag.get('alt', '').replace("Logo", "").strip() if picture_tag else "Unknown"
            date_range_text = item.select_one('.grid-item-content small.hidden-sm').get_text(strip=True) if item.select_one('.grid-item-content small.hidden-sm') else ""
            valid_from, valid_to = self.parse_date_range(date_range_text)
            parsed_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.brochures.append({
                "title": title,
                "thumbnail": thumbnail,
                "shop_name": shop_name,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "parsed_time": parsed_time
            })

    def check_output_completeness(self):
        issues = []
        for brochure in self.brochures:
            for key, value in brochure.items():
                if value == "Unknown" or value == "" or value == []:
                    issues.append(f"Shop '{brochure['shop_name']}': '{key}' is incomplete or missing.")
            
        if issues:
            self.notice = "Notice: Not everything is complete. There might be missing or incorrect data.\n"
            self.notice += "\n".join(issues)


    def save_to_json(self, filename):
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(self.brochures, file, ensure_ascii=False, indent=4)
        if self.notice:
            print(self.notice)

    def run(self, output_file):
        self.parse_page(self.fetch_page())
        self.check_output_completeness()
        self.save_to_json(output_file)

if __name__ == "__main__":
    parser = BrochureParser("https://www.prospektmaschine.de/hypermarkte/")
    parser.run("brochures.json")
    print("Data has been saved to brochures.json")
    