import os
import time
import requests
import re
import random
import smtplib
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION FROM ENVIRONMENT SECRETS ---
SCRIPT_URL = os.getenv("SCRIPT_URL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or "lookscorner080@gmail.com"

# --- TIME LIMITS ---
START_TIME = time.time()
SEVEN_HOURS = 7 * 3600  # Scraping Phase
TOTAL_SESSION = 8 * 3600  # Total Session before GitHub Restart

# --- MASSIVE NICHE BANK ---
B2B_NICHES = [
    "HVAC", "Solar Energy", "Plumbers", "Roofer", "Logistics", "Trucking", 
    "Law Firms", "Dentists", "Gym Owners", "Interior Designers", 
    "Car Detailing", "SaaS Startups", "E-com Stores", "Digital Marketing", 
    "SEO Agencies", "Software Houses", "Recruitment Firms"
]

B2C_NICHES = [
    "Weight Loss", "Keto Diet", "Yoga Enthusiasts", "Skincare Lovers", 
    "Luxury Fashion", "Home Decor", "Parenting Tips", "Pet Training", 
    "Study Abroad IELTS", "Personal Finance", "Real Estate Investors", 
    "Career Coaching", "Gaming eSports"
]

LOCATIONS = ["London", "New York", "Dubai", "Toronto", "Sydney", "Karachi", "Texas", "Florida"]
PLATFORMS = ["site:facebook.com", "site:instagram.com", "site:urlebird.com", "site:reddit.com", "site:picuki.com"]

# --- DUPLICATE TRACKING (Local Session Cache) ---
seen_emails = set()

def generate_batch_queries(count=5):
    """Generates a randomized batch of 5 search queries"""
    queries = []
    email_domains = ["@gmail.com", "@yahoo.com", "@hotmail.com"]
    
    for _ in range(count):
        category = random.choice(["B2B", "B2C"])
        domain = random.choice(email_domains)
        
        if category == "B2B":
            niche = random.choice(B2B_NICHES)
            loc = random.choice(LOCATIONS)
            queries.append(f'"{niche}" {loc} "contact us" "{domain}"')
        else:
            niche = random.choice(B2C_NICHES)
            plat = random.choice(PLATFORMS)
            queries.append(f'{plat} "{niche}" "{domain}"')
    return queries

def extract_leads(text):
    """Regex to find emails and potential phone numbers"""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}'
    phone_pattern = r'\+?\d{10,13}'
    
    found_emails = re.findall(email_pattern, text)
    found_phones = re.findall(phone_pattern, text)
    
    return list(set(found_emails)), list(set(found_phones))

def hunter(query):
    """Executes search and handles data transmission to Google Sheets"""
    print(f"[SEARCHING] Query: {query}")
    try:
        search_url = f"https://www.bing.com/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        response = requests.get(search_url, headers=headers, timeout=15)
        emails, phones = extract_leads(response.text)
        
        for email in emails:
            # Step 1: Local Duplicate Check
            if email in seen_emails:
                print(f"[SKIP] Already processed in this session: {email}")
                continue
            
            seen_emails.add(email)
            
            # Prepare Payload for Google Apps Script
            payload = {
                "action": "add",
                "location": "Global/Web",
                "platform": "Search/Mirror",
                "email": email,
                "phone": phones[0] if phones else "N/A",
                "title": query[:40]
            }
            
            # Step 2: Remote Duplicate Check (Handled by Apps Script doPost)
            try:
                sheet_res = requests.post(SCRIPT_URL, json=payload, timeout=10)
                if "Added" in sheet_res.text:
                    print(f"[SUCCESS] Lead Saved: {email}")
                else:
                    print(f"[DUPLICATE] Exists in Sheet: {email}")
            except:
                print(f"[ERROR] Failed to connect to Google Sheets for {email}")

            time.sleep(2) # Prevent rate limiting on sheet writing

    except Exception as e:
        print(f"[SYSTEM ERROR] Hunter Exception: {e}")

def verification_phase():
    """8th Hour Cleanup: SMTP Verification Placeholder"""
    print("[PHASE 2] Starting SMTP Verification Mode...")
    # This logic will iterate through 'Pending' rows via API and update to 'Verified' or 'Delete'
    pass

if __name__ == "__main__":
    print("--- LEAD GENERATION AGENT STARTING ---")
    
    # 7-HOUR SCRAPING LOOP
    while (time.time() - START_TIME) < SEVEN_HOURS:
        batch = generate_batch_queries(5)
        
        for q in batch:
            hunter(q)
            
            # Slow & Smooth Pacing
            interval = random.randint(45, 90)
            print(f"[IDLE] Cooling down for {interval} seconds...")
            time.sleep(interval)

    # 8th-HOUR VALIDATION LOOP
    verification_phase()

    print("--- SESSION COMPLETE ---")
    print("Agent going to sleep for 10 minutes before GitHub Action restart.")
    time.sleep(600)
