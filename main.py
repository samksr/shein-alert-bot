print("SYSTEM: Initializing imports...", flush=True)
import asyncio
import json
import os
import sys
import traceback
import scraper
import config
from telegram import Bot

SEEN_FILE = "/tmp/seen_ids.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen(seen_set):
    try:
        with open(SEEN_FILE, 'w') as f:
            json.dump(list(seen_set), f)
    except Exception as e:
        print(f"Error saving file: {e}", flush=True)

async def main():
    print(f"🚀 SYSTEM: Main Loop Started. Speed: {config.CHECK_INTERVAL}s", flush=True)
    
    try:
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        print("SYSTEM: Bot Token Loaded.", flush=True)
        
        seen_products = load_seen()
        
        # Test Connection on Startup
        products, error = scraper.fetch_products_api(config.TARGET_URL)
        print(f"SYSTEM: Startup Check Result: {len(products)} products found. Error: {error}", flush=True)
        
        if error == "OK" and products:
            latest = products[0]
            for chat_id in config.TELEGRAM_CHAT_IDS:
                try:
                    await bot.send_message(chat_id=chat_id, text=f"✅ <b>BOT ONLINE</b>\nLatest Item: {latest['name']}", parse_mode='HTML')
                except Exception as e:
                    print(f"Telegram Send Error: {e}", flush=True)
        else:
             print(f"SYSTEM: Startup Failed - {error}", flush=True)

        while True:
            try:
                products, error = scraper.fetch_products_api(config.TARGET_URL)
                
                if error != "OK":
                    print(f"Fetch Error: {error}", flush=True)
                
                new_batch = []
                for p in products:
                    if p['code'] not in seen_products:
                        new_batch.append(p)
                        seen_products.add(p['code'])
                
                if new_batch:
                    print(f"🔥 Found {len(new_batch)} NEW items!", flush=True)
                    save_seen(seen_products)
                    
                    for p in new_batch:
                        scraper.add_to_wishlist(p['code'])
                        stock_status = "✅ In Stock" if p['in_stock'] else "❌ Out of Stock"
                        msg = (
                            f"🚨 <b>DROP ALERT</b>\n"
                            f"📦 <b>{p['name']}</b>\n"
                            f"💰 ₹{p['price']}\n"
                            f"📏 {p['sizes']}\n"
                            f"📊 {stock_status}\n"
                            f"🔗 <a href='{p['url']}'>BUY NOW</a>"
                        )
                        for chat_id in config.TELEGRAM_CHAT_IDS:
                            try: await bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')
                            except: pass
            except Exception as e:
                print(f"Inner Loop Error: {e}", flush=True)

            await asyncio.sleep(config.CHECK_INTERVAL)

    except Exception as e:
        print(f"CRITICAL MAIN ERROR: {e}", flush=True)
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"CRITICAL STARTUP ERROR: {e}", flush=True)
        traceback.print_exc()
