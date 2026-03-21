import os
import time
import requests
import re
import random
import smtplib
from concurrent.futures import ThreadPoolExecutor

# --- SECRETS (GitHub/Kaggle se uthayega) ---
SCRIPT_URL = os.getenv("SCRIPT_URL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or "lookscorner080@gmail.com"

# --- CONFIGURATION ---
START_TIME = time.time()
SEVEN_HOURS = 7 * 3600
EIGHT_HOURS = 8 * 3600

# --- MASSIVE NICHE BANK (B2B & B2C) ---
B2B_NICHES = ["HVAC", "Solar Energy", "Plumbers", "Roofer", "Logistics", "Trucking", "Law Firms", "Dentists", "Gym Owners", "Interior Designers", "Car Detailing", "SaaS Startups", "E-com Stores", "Digital Marketing", "SEO Agencies", "Software Houses", "Recruitment Firms"]
B2C_NICHES = ["Weight Loss", "Keto Diet", "Yoga Enthusiasts", "Skincare Lovers", "Luxury Fashion", "Home Decor", "Parenting Tips", "Pet Training", "Study Abroad IELTS", "Personal Finance", "Real Estate Investors", "Career Coaching", "Gaming eSports"]
LOCATIONS = ["London", "New York", "Dubai", "Toronto", "Sydney", "Karachi", "Texas", "Florida"]
PLATFORMS = ["site:facebook.com", "site:instagram.com", "site:urlebird.com", "site:reddit.com", "site:picuki.com"]

def generate_random_queries(count=5):
    """Har baar 5 unique random queries banata hai"""
    queries = []
    for _ in range(count):
        mode = random.choice(["B2B", "B2C"])
        email_provider = random.choice(["@gmail.com", "@yahoo.com", "@hotmail.com"])
        
        if mode == "B2B":
            niche = random.choice(B2B_NICHES)
            loc = random.choice(LOCATIONS)
            queries.append(f'"{niche}" {loc} "contact us" "{email_provider}"')
        else:
            niche = random.choice(B2C_NICHES)
            plat = random.choice(PLATFORMS)
            queries.append(f'{plat} "{niche}" "{email_provider}"')
    return queries

def extract_leads(text):
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}', text)
    phones = re.findall(r'\+?\d{10,13}', text)
    return list(set(emails)), list(set(phones))

def send_to_sheet(data, action="add"):
    try:
        data['action'] = action
        requests.post(SCRIPT_URL, json=data, timeout=10)
    except: pass

def hunter(query):
    """Slow & Smooth Scraping"""
    print(f"🔎 Searching: {query}")
    try:
        # Bing/Google search simulate
        search_url = f"https://www.bing.com/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(search_url, headers=headers, timeout=15)
        
        emails, phones = extract_leads(res.text)
        
        for email in emails:
            payload = {
                "location": "Global",
                "platform": "Search/Mirror",
                "email": email,
                "phone": phones[0] if phones else "N/A",
                "title": query[:40],
                "type": "Mixed"
            }
            send_to_sheet(payload, action="add")
            print(f"✅ Lead Added: {email}")
            time.sleep(2) # Row likhne ke baad halka sa break
            
    except Exception as e:
        print(f"⚠️ Error in Hunter: {e}")

# --- EXECUTION ENGINE ---
if __name__ == "__main__":
    print("🚀 Agent Awake. Starting 7-Hour Scrape Mode...")
    
    while (time.time() - START_TIME) < SEVEN_HOURS:
        # Har round mein 5 queries
        batch_queries = generate_random_queries(5)
        
        for q in batch_queries:
            hunter(q)
            # Query ke darmiyan lamba break (Slow & Smooth)
            wait_time = random.randint(30, 60)
            print(f"😴 Sleeping for {wait_time}s to stay safe...")
            time.sleep(wait_time)

    # 8th Hour Verification Phase
    print("🧹 Switching to 8th Hour Verification Mode...")
    # (Yahan SMTP verification ka logic call hoga jo 'Pending' ko 'Verified' karega)
    
    print("😴 Mission Complete. Restarting via GitHub shortly.")
    time.sleep(600)
