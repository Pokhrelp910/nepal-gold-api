"""
Nepal Gold and Silver Price Updater
Fetches latest rates from Hamro Patro and saves to gold.json
"""

import urllib.request
import re
import json
from datetime import datetime

def fetch_rates():
    url = "https://www.hamropatro.com/gold"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8")

    matches = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL)
    
    for chunk in matches:
        if "HalMark Gold" in chunk:
            unescaped = chunk.encode("utf-8").decode("unicode_escape")
            start_idx = unescaped.find('[{"name":')
            if start_idx != -1:
                count = 0
                end_idx = -1
                for i in range(start_idx, len(unescaped)):
                    if unescaped[i] == '[':
                        count += 1
                    elif unescaped[i] == ']':
                        count -= 1
                        if count == 0:
                            end_idx = i + 1
                            break
                if end_idx != -1:
                    raw_items = json.loads(unescaped[start_idx:end_idx])
                    
                    result = {
                        "status": "success",
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "source": "Hamro Patro / FENEGOSIDA",
                        "rates": []
                    }
                    
                    for item in raw_items:
                        name = item.get("name")
                        symbol = item.get("symbol")
                        prices = {}
                        date = None
                        for p in item.get("prices", []):
                            p_name = p.get("name")
                            price_obj = p.get("price", {})
                            prices[p_name] = price_obj.get("price")
                            if not date:
                                date = price_obj.get("date")
                        
                        result["rates"].append({
                            "name": name,
                            "symbol": symbol,
                            "date": date,
                            "prices": prices
                        })
                    return result
    raise Exception("Rate data not found in page")

if __name__ == "__main__":
    print("Fetching latest rates from Hamro Patro...")
    data = fetch_rates()
    with open("gold.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("SUCCESS: gold.json updated successfully!")
    print(json.dumps(data, indent=2, ensure_ascii=False))
