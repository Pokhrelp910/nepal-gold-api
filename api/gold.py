from http.server import BaseHTTPRequestHandler
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
    with urllib.request.urlopen(req, timeout=10) as resp:
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

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = fetch_rates()
            response_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            # Cache on Vercel CDN for 1 hour (3600 seconds)
            self.send_header("Cache-Control", "s-maxage=3600, stale-while-revalidate")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)
        except Exception as e:
            err = {"status": "error", "message": str(e)}
            err_bytes = json.dumps(err).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(err_bytes)))
            self.end_headers()
            self.wfile.write(err_bytes)
