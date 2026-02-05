import subprocess
import json
import urllib.parse
import config
from typing import List, Dict, Any, Tuple

def add_to_wishlist(product_id: str):
    try:
        api_url = "https://www.sheinindia.in/api/user/wishlist/add"
        data = json.dumps({"productCode": product_id})
        curl_cmd = [
            'curl', '-s', '-L', '-X', 'POST',
            '-H', 'user-agent: Mozilla/5.0 (Linux; Android 10; K)',
            '-H', 'content-type: application/json',
            '-H', 'x-tenant-id: SHEIN',
            '-H', f'cookie: {config.SHEIN_COOKIES}',
            '-d', data,
            '--max-time', '5',
            api_url
        ]
        subprocess.run(curl_cmd, capture_output=True)
    except:
        pass

def fetch_products_api(filtered_url: str) -> Tuple[List[Dict[str, Any]], str]:
    try:
        category_code = "sverse-5939-37961"
        if "c/" in filtered_url:
            parts = filtered_url.split("c/")
            if len(parts) > 1:
                category_code = parts[1].split("?")[0]
        
        params = {'sort': '7', 'limit': '60', 'fields': 'SITE', 'currentPage': '0', 'format': 'json'}
        query_string = urllib.parse.urlencode(params)
        api_url = f"https://www.sheinindia.in/api/category/{category_code}?{query_string}"
        
        curl_cmd = [
            'curl', '-s', '-L',
            '-H', 'user-agent: Mozilla/5.0 (Linux; Android 10; K)',
            '-H', 'accept: application/json',
            '-H', 'x-tenant-id: SHEIN',
            '-H', f'cookie: {config.SHEIN_COOKIES}',
            '--max-time', '10',
            api_url
        ]
        
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return [], f"cURL Failed: {result.stderr}"

        if "<html" in result.stdout.lower() or "denied" in result.stdout.lower():
            return [], "BLOCKED (HTML Response)"

        try:
            data = json.loads(result.stdout)
        except:
             return [], "INVALID JSON"

        products = data.get('products', [])
        clean_list = []
        for p in products:
            sizes = []
            in_stock = False
            if 'multiLevelSize' in p:
                for s in p['multiLevelSize']:
                    if s.get('storageStock', 0) > 0:
                        sizes.append(s.get('sizeLocalName', 'Unknown'))
                        in_stock = True
            elif 'storageStock' in p and p['storageStock'] > 0:
                in_stock = True
                sizes = ["One Size"]
            
            if not sizes: sizes = ["Check Link"]

            clean_list.append({
                'code': str(p.get('code')),
                'name': p.get('name', 'Unknown'),
                'price': p.get('price', {}).get('value', '0'),
                'url': f"https://www.sheinindia.in/p/{p.get('code')}",
                'sizes': ", ".join(sizes),
                'in_stock': in_stock
            })
        return clean_list, "OK"
            
    except Exception as e:
        return [], str(e)
