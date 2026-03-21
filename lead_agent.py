import os
import time
import requests
import re
import random
from urllib.parse import unquote
from bs4 import BeautifulSoup

from kaggle_secrets import UserSecretsClient
user_secrets = UserSecretsClient()

try:
    B2B_URL = user_secrets.get_secret("B2B_SCRIPT_URL")
    B2C_URL = user_secrets.get_secret("B2C_SCRIPT_URL")
    SENDER_EMAIL = user_secrets.get_secret("SENDER_EMAIL")
except Exception as e:
    print(f"⚠️ Secret Error: {e}")
    B2B_URL = None
    B2C_URL = None
    SENDER_EMAIL = "lookscorner080@gmail.com"

# --- TIME LIMITS ---
START_TIME = time.time()
SEVEN_HOURS = 7 * 3600

# --- MASSIVE NICHE BANK ---
B2B_NICHES = ["HVAC", "Solar Energy", "Plumbers", "Roofer", "Logistics", "Trucking", "Law Firms", "Dentists", "Gym Owners", "Interior Designers", "Car Detailing", "SaaS Startups", "E-com Stores", "Digital Marketing", "SEO Agencies", "Software Houses", "Recruitment Firms"]
B2C_NICHES = ["Weight Loss", "Keto Diet", "Yoga Enthusiasts", "Skincare Lovers", "Luxury Fashion", "Home Decor", "Parenting Tips", "Pet Training", "Study Abroad IELTS", "Personal Finance", "Real Estate Investors", "Career Coaching", "Gaming eSports"]
LOCATIONS = ["London", "New York", "Dubai", "Toronto", "Sydney", "Karachi", "Texas", "Florida"]
PLATFORMS = ["site:facebook.com", "site:instagram.com", "site:urlebird.com", "site:reddit.com", "site:picuki.com"]

def generate_batch_queries(count=5):
    queries = []
    email_providers = ["@gmail.com", "@yahoo.com", "@hotmail.com"]
    for _ in range(count):
        mode = random.choice(["B2B", "B2C"])
        domain = random.choice(email_providers)
        if mode == "B2B":
            n = random.choice(B2B_NICHES)
            l = random.choice(LOCATIONS)
            queries.append({
                "query": f'"{n}" {l} "contact us" "{domain}"',
                "mode": "B2B",
                "niche": n,
                "location": l
            })
        else:
            n = random.choice(B2C_NICHES)
            p = random.choice(PLATFORMS)
            queries.append({
                "query": f'{p} "{n}" "{domain}"',
                "mode": "B2C",
                "niche": n,
                "location": p.replace("site:", "")
            })
    return queries

def extract_leads(html):
    """Decode HTML and find emails + phones"""
    # Decode URL encoding (%40 → @)
    decoded = unquote(html)
    # Remove HTML tags
    soup = BeautifulSoup(decoded, "html.parser")
    text = soup.get_text()
    
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}', text)
    phones = re.findall(r'\+?\d{10,13}', text)
    
    # Filter out junk emails
    filtered_emails = [
        e for e in set(emails)
        if not any(skip in e for skip in ["w3.org", "example.com", "microsoft.com", "bing.com", "schema.org"])
    ]
    return filtered_emails, list(set(phones))

def hunter(query, category, niche, location):
    target_url = B2B_URL if category == "B2B" else B2C_URL

    print(f"🔎 Searching {category}: {query}")
    try:
        search_url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(search_url, headers=headers, timeout=15)

        emails, phones = extract_leads(res.text)

        if not emails:
            print(f"📭 No leads found for: {query}")
            return

        for i, email in enumerate(emails):
            phone = phones[i] if i < len(phones) else (phones[0] if phones else "N/A")
            payload = {
                "action": "add",
                "location": location,
                "platform": category,
                "email": email,
                "phone": phone,
                "title": niche
            }

            try:
                response = requests.post(target_url, json=payload, timeout=10)
                if "Added" in response.text:
                    print(f"✅ Saved to {category} Sheet: {email}")
                elif "Duplicate" in response.text:
                    print(f"⏭️ Duplicate in {category}: {email}")
                else:
                    print(f"⚠️ Sheet response: {response.text[:80]}")
            except Exception as e:
                print(f"⚠️ Error connecting to {category} Sheet: {e}")

            time.sleep(2)

    except Exception as e:
        print(f"⚠️ Search Error: {e}")

if __name__ == "__main__":
    print("🚀 Lead Agent Activated (7-Hour Mode)")

    while (time.time() - START_TIME) < SEVEN_HOURS:
        batch = generate_batch_queries(5)
        for q in batch:
            hunter(q["query"], q["mode"], q["niche"], q["location"])
            wait = random.randint(45, 90)
            print(f"😴 Waiting {wait}s...")
            time.sleep(wait)

    print("🏁 7 Hours Complete.")
    print("😴 Hibernating for 10 mins...")
    time.sleep(600)
