import time
import requests
import re
import random
import smtplib
import dns.resolver
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from kaggle_secrets import UserSecretsClient

# ============================================================
# CONFIGURATION
# ============================================================
secrets = UserSecretsClient()
B2B_URL = secrets.get_secret("B2B_SCRIPT_URL")
B2C_URL = secrets.get_secret("B2C_SCRIPT_URL")

START_TIME = time.time()
SEVEN_HOURS = 7 * 3600

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

JUNK_DOMAINS = [
    "example.com", "schema.org", "google.com", "microsoft.com",
    "bing.com", "jquery.com", "cloudflare.com", "amazonaws.com",
    "sentry.io", "wix.com", "wordpress.com", "squarespace.com",
    "apple.com", "youtube.com", "facebook.com", "twitter.com",
    "instagram.com", "tiktok.com", "linkedin.com", "w3.org"
]

# ============================================================
# B2B SOURCES
# ============================================================
B2B_SOURCES = {
    "yellowpages": {
        "niches": ["HVAC", "Solar Energy", "Plumbers", "Roofer", "Dentists",
                   "Law Firms", "Gym", "Interior Designers", "Car Detailing",
                   "Logistics", "Trucking", "Accountants", "Real Estate Agency",
                   "Insurance Agency", "Marketing Agency", "IT Services",
                   "Cleaning Services", "Landscaping", "Photography", "Catering"],
        "locations": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
                      "Philadelphia", "San Antonio", "Dallas", "Dubai", "Toronto",
                      "London", "Sydney", "Miami", "Atlanta", "Seattle"]
    },
    "yelp": {
        "niches": ["restaurants", "dentists", "lawyers", "gyms", "plumbers",
                   "electricians", "contractors", "accountants", "photographers",
                   "catering", "cleaning", "landscaping", "auto repair", "salons"],
        "locations": ["New York", "Los Angeles", "Chicago", "San Francisco",
                      "Miami", "Seattle", "Boston", "Denver", "Austin", "Portland"]
    },
    "bbb": {
        "niches": ["hvac", "plumbing", "roofing", "law", "dental", "accounting",
                   "marketing", "it-services", "cleaning", "landscaping"],
        "locations": ["new-york", "los-angeles", "chicago", "houston", "phoenix",
                      "philadelphia", "dallas", "miami", "atlanta", "seattle"]
    },
    "clutch": {
        "niches": ["digital-marketing", "seo", "web-design", "mobile-app-development",
                   "software-development", "it-managed-services", "cloud-consulting",
                   "ai-development", "ecommerce-development", "social-media-marketing"],
    },
    "bark": {
        "niches": ["web-designer", "seo-consultant", "marketing-consultant",
                   "accountant", "business-consultant", "graphic-designer",
                   "photographer", "videographer", "personal-trainer", "lawyer"],
        "locations": ["london", "new-york", "toronto", "sydney", "dubai"]
    }
}

# ============================================================
# B2C SOURCES
# ============================================================
B2C_SOURCES = {
    "reddit": {
        "niches": ["entrepreneur", "smallbusiness", "digitalnomad", "marketing",
                   "freelance", "ecommerce", "dropshipping", "affiliatemarketing",
                   "personalfinance", "investing", "realestate", "fitness",
                   "weightloss", "keto", "yoga", "skincare", "fashion",
                   "gaming", "photography", "travel"]
    },
    "quora": {
        "niches": ["Digital Marketing", "Entrepreneurship", "Personal Finance",
                   "Weight Loss", "Fitness", "Real Estate", "E-commerce",
                   "Freelancing", "Photography", "Travel", "Fashion", "Skincare"]
    },
    "medium": {
        "niches": ["marketing", "entrepreneurship", "technology", "fitness",
                   "personal-finance", "photography", "travel", "design",
                   "programming", "self-improvement"]
    },
    "producthunt": {
        "niches": ["productivity", "marketing", "developer-tools", "design-tools",
                   "social-media", "analytics", "email-marketing", "ai"]
    },
    "github": {
        "niches": ["machine-learning", "web-development", "python", "javascript",
                   "data-science", "automation", "api", "saas"]
    }
}

# ============================================================
# EMAIL UTILITIES
# ============================================================
def is_junk_email(email):
    return any(junk in email.lower() for junk in JUNK_DOMAINS)

def extract_emails_from_text(text):
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}', text)
    return list(set([e for e in emails if not is_junk_email(e) and len(e) < 60]))

def verify_email_smtp(email):
    try:
        domain = email.split("@")[1]
        records = dns.resolver.resolve(domain, "MX")
        mx = str(records[0].exchange)
        server = smtplib.SMTP(timeout=10)
        server.connect(mx)
        server.helo("verify.com")
        server.mail("verify@verify.com")
        code, _ = server.rcpt(email)
        server.quit()
        return code == 250
    except:
        return False

def update_sheet_status(sheet_url, email, action):
    try:
        requests.post(sheet_url, json={"action": action, "email": email}, timeout=10)
    except:
        pass

def save_lead(sheet_url, payload):
    try:
        response = requests.post(sheet_url, json=payload, timeout=10)
        if "Added" in response.text:
            print(f"    [SAVED] {payload.get('email')}")
            return True
        elif "Duplicate" in response.text:
            print(f"    [DUPLICATE] {payload.get('email')}")
        return False
    except Exception as e:
        print(f"    [SHEET ERROR] {e}")
        return False

# ============================================================
# WEBSITE EMAIL EXTRACTOR
# ============================================================
def get_emails_from_website(url):
    emails, phones = [], []
    pages = [url]
    for suffix in ["/contact", "/contact-us", "/about", "/about-us", "/reach-us"]:
        pages.append(url.rstrip("/") + suffix)

    for page in pages:
        try:
            res = requests.get(page, headers=HEADERS, timeout=8)
            if res.status_code != 200:
                continue
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text()
            found = extract_emails_from_text(text)
            ph = re.findall(r'(\+?\d[\d\s\-().]{8,15}\d)', text)
            clean_phones = list(set([re.sub(r'[\s\-().]', '', p) for p in ph
                                     if 7 <= len(re.sub(r'\D', '', p)) <= 15]))
            if found:
                emails.extend(found)
                phones.extend(clean_phones)
                break
            time.sleep(0.5)
        except:
            continue
    return list(set(emails)), list(set(phones))

# ============================================================
# B2B SCRAPERS
# ============================================================
def scrape_yellowpages(niche, location):
    leads = []
    url = f"https://www.yellowpages.com/search?search_terms={quote(niche)}&geo_location_terms={quote(location)}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        listings = soup.select("div.v-card")
        for listing in listings:
            name = listing.select_one("a.business-name")
            phone = listing.select_one("div.phones")
            website = listing.select_one("a.track-visit-website")
            name = name.text.strip() if name else "N/A"
            phone = phone.text.strip() if phone else "N/A"
            website = website["href"] if website else None
            emails = []
            if website and "yellowpages.com" not in website:
                emails, phones = get_emails_from_website(website)
            for email in emails:
                leads.append({
                    "title": "Business Owner",
                    "location": location,
                    "business_type": niche,
                    "source": website or "yellowpages.com",
                    "email": email,
                    "phone": phone
                })
        time.sleep(2)
    except Exception as e:
        print(f"    [YELLOWPAGES ERROR] {e}")
    return leads

def scrape_yelp(niche, location):
    leads = []
    url = f"https://www.yelp.com/search?find_desc={quote(niche)}&find_loc={quote(location)}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        businesses = soup.select("div.businessName__09f24__EYSZE, h3.css-1agk4wl")
        links = soup.select("a.css-1m051bw")
        for link in links[:15]:
            href = link.get("href", "")
            if "/biz/" in href:
                full_url = f"https://www.yelp.com{href}"
                try:
                    biz_res = requests.get(full_url, headers=HEADERS, timeout=10)
                    biz_soup = BeautifulSoup(biz_res.text, "html.parser")
                    text = biz_soup.get_text()
                    emails = extract_emails_from_text(text)
                    phones = re.findall(r'(\+?\d[\d\s\-().]{8,15}\d)', text)
                    phone = re.sub(r'[\s\-().]', '', phones[0]) if phones else "N/A"
                    for email in emails:
                        leads.append({
                            "title": "Business Owner",
                            "location": location,
                            "business_type": niche,
                            "source": full_url,
                            "email": email,
                            "phone": phone
                        })
                    time.sleep(1)
                except:
                    continue
        time.sleep(2)
    except Exception as e:
        print(f"    [YELP ERROR] {e}")
    return leads

def scrape_bbb(niche, location):
    leads = []
    url = f"https://www.bbb.org/search?find_text={quote(niche)}&find_loc={location}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.select("div.MuiGrid-root a[href*='/profile/']")
        for card in cards[:10]:
            href = card.get("href", "")
            full_url = f"https://www.bbb.org{href}"
            try:
                biz_res = requests.get(full_url, headers=HEADERS, timeout=10)
                biz_soup = BeautifulSoup(biz_res.text, "html.parser")
                text = biz_soup.get_text()
                emails = extract_emails_from_text(text)
                phones = re.findall(r'(\+?\d[\d\s\-().]{8,15}\d)', text)
                phone = re.sub(r'[\s\-().]', '', phones[0]) if phones else "N/A"
                for email in emails:
                    leads.append({
                        "title": "Business Owner",
                        "location": location,
                        "business_type": niche,
                        "source": full_url,
                        "email": email,
                        "phone": phone
                    })
                time.sleep(1)
            except:
                continue
        time.sleep(2)
    except Exception as e:
        print(f"    [BBB ERROR] {e}")
    return leads

def scrape_clutch(niche):
    leads = []
    url = f"https://clutch.co/directory/{niche}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        profiles = soup.select("li.provider-list-item a.company_title")
        for profile in profiles[:10]:
            href = profile.get("href", "")
            full_url = f"https://clutch.co{href}" if href.startswith("/") else href
            try:
                biz_res = requests.get(full_url, headers=HEADERS, timeout=10)
                biz_soup = BeautifulSoup(biz_res.text, "html.parser")
                website_link = biz_soup.select_one("a.website-link__item")
                if website_link:
                    website = website_link.get("href", "")
                    emails, phones = get_emails_from_website(website)
                    phone = phones[0] if phones else "N/A"
                    for email in emails:
                        leads.append({
                            "title": "Manager",
                            "location": "Global",
                            "business_type": niche.replace("-", " ").title(),
                            "source": website,
                            "email": email,
                            "phone": phone
                        })
                time.sleep(1)
            except:
                continue
        time.sleep(2)
    except Exception as e:
        print(f"    [CLUTCH ERROR] {e}")
    return leads

def scrape_bark(niche, location):
    leads = []
    url = f"https://www.bark.com/en/us/{niche}/{location}/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        profiles = soup.select("a.profile-link")
        for profile in profiles[:10]:
            href = profile.get("href", "")
            full_url = f"https://www.bark.com{href}" if href.startswith("/") else href
            try:
                pro_res = requests.get(full_url, headers=HEADERS, timeout=10)
                pro_soup = BeautifulSoup(pro_res.text, "html.parser")
                text = pro_soup.get_text()
                emails = extract_emails_from_text(text)
                phones = re.findall(r'(\+?\d[\d\s\-().]{8,15}\d)', text)
                phone = re.sub(r'[\s\-().]', '', phones[0]) if phones else "N/A"
                for email in emails:
                    leads.append({
                        "title": "Service Provider",
                        "location": location,
                        "business_type": niche.replace("-", " ").title(),
                        "source": full_url,
                        "email": email,
                        "phone": phone
                    })
                time.sleep(1)
            except:
                continue
        time.sleep(2)
    except Exception as e:
        print(f"    [BARK ERROR] {e}")
    return leads

# ============================================================
# B2C SCRAPERS
# ============================================================
def scrape_reddit(niche):
    leads = []
    url = f"https://www.reddit.com/r/{niche}/new.json?limit=50"
    try:
        res = requests.get(url, headers={"User-Agent": "LeadBot/1.0"}, timeout=15)
        data = res.json()
        posts = data.get("data", {}).get("children", [])
        for post in posts:
            text = post["data"].get("selftext", "") + " " + post["data"].get("title", "")
            emails = extract_emails_from_text(text)
            for email in emails:
                leads.append({
                    "location": "Global",
                    "platform": f"Reddit r/{niche}",
                    "email": email,
                    "phone": "N/A"
                })
        time.sleep(2)
    except Exception as e:
        print(f"    [REDDIT ERROR] {e}")
    return leads

def scrape_quora(niche):
    leads = []
    url = f"https://www.quora.com/topic/{quote(niche)}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text()
        emails = extract_emails_from_text(text)
        for email in emails:
            leads.append({
                "location": "Global",
                "platform": "Quora",
                "email": email,
                "phone": "N/A"
            })
        time.sleep(2)
    except Exception as e:
        print(f"    [QUORA ERROR] {e}")
    return leads

def scrape_medium(niche):
    leads = []
    url = f"https://medium.com/tag/{niche}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        author_links = soup.select("a[href*='@']")
        for link in author_links[:10]:
            href = link.get("href", "")
            if "/@" in href:
                full_url = f"https://medium.com{href}" if href.startswith("/") else href
                try:
                    pro_res = requests.get(full_url, headers=HEADERS, timeout=10)
                    text = BeautifulSoup(pro_res.text, "html.parser").get_text()
                    emails = extract_emails_from_text(text)
                    for email in emails:
                        leads.append({
                            "location": "Global",
                            "platform": "Medium",
                            "email": email,
                            "phone": "N/A"
                        })
                    time.sleep(1)
                except:
                    continue
        time.sleep(2)
    except Exception as e:
        print(f"    [MEDIUM ERROR] {e}")
    return leads

def scrape_github(niche):
    leads = []
    url = f"https://github.com/search?q={quote(niche)}&type=users"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        user_links = soup.select("a.mr-1")
        for link in user_links[:10]:
            username = link.text.strip()
            if username:
                profile_url = f"https://github.com/{username}"
                try:
                    pro_res = requests.get(profile_url, headers=HEADERS, timeout=10)
                    text = BeautifulSoup(pro_res.text, "html.parser").get_text()
                    emails = extract_emails_from_text(text)
                    for email in emails:
                        leads.append({
                            "location": "Global",
                            "platform": "GitHub",
                            "email": email,
                            "phone": "N/A"
                        })
                    time.sleep(1)
                except:
                    continue
        time.sleep(2)
    except Exception as e:
        print(f"    [GITHUB ERROR] {e}")
    return leads

def scrape_producthunt(niche):
    leads = []
    url = f"https://www.producthunt.com/topics/{niche}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text()
        emails = extract_emails_from_text(text)
        for email in emails:
            leads.append({
                "location": "Global",
                "platform": "ProductHunt",
                "email": email,
                "phone": "N/A"
            })
        time.sleep(2)
    except Exception as e:
        print(f"    [PRODUCTHUNT ERROR] {e}")
    return leads

# ============================================================
# VERIFICATION ENGINE
# ============================================================
def run_verification(sheet_url):
    print("\n[VERIFICATION] Fetching pending emails...")
    try:
        res = requests.get(sheet_url, timeout=10)
        pending = res.json()
        print(f"[VERIFICATION] {len(pending)} emails to verify")
        for item in pending:
            email = item if isinstance(item, str) else item.get("email", "")
            if not email:
                continue
            is_valid = verify_email_smtp(email)
            if is_valid:
                update_sheet_status(sheet_url, email, "update")
                print(f"    [VALID] {email}")
            else:
                update_sheet_status(sheet_url, email, "delete")
                print(f"    [REMOVED] {email}")
            time.sleep(1)
    except Exception as e:
        print(f"[VERIFICATION ERROR] {e}")

# ============================================================
# MAIN AGENT
# ============================================================
def run_b2b_round():
    source = random.choice(list(B2B_SOURCES.keys()))
    config = B2B_SOURCES[source]
    niche = random.choice(config["niches"])
    location = random.choice(config.get("locations", ["United States"]))

    print(f"\n[B2B] Source: {source.upper()} | Niche: {niche} | Location: {location}")

    if source == "yellowpages":
        leads = scrape_yellowpages(niche, location)
    elif source == "yelp":
        leads = scrape_yelp(niche, location)
    elif source == "bbb":
        leads = scrape_bbb(niche, location)
    elif source == "clutch":
        leads = scrape_clutch(niche)
    elif source == "bark":
        leads = scrape_bark(niche, location)
    else:
        leads = []

    saved = 0
    for lead in leads:
        payload = {
            "action": "add",
            "title": lead.get("title", "Business Owner"),
            "location": lead.get("location", "N/A"),
            "business_type": lead.get("business_type", "N/A"),
            "source": lead.get("source", "N/A"),
            "email": lead.get("email", ""),
            "phone": lead.get("phone", "N/A")
        }
        if save_lead(B2B_URL, payload):
            saved += 1

    print(f"[B2B] Saved {saved}/{len(leads)} leads")

def run_b2c_round():
    source = random.choice(list(B2C_SOURCES.keys()))
    config = B2C_SOURCES[source]
    niche = random.choice(config["niches"])

    print(f"\n[B2C] Source: {source.upper()} | Niche: {niche}")

    if source == "reddit":
        leads = scrape_reddit(niche)
    elif source == "quora":
        leads = scrape_quora(niche)
    elif source == "medium":
        leads = scrape_medium(niche)
    elif source == "github":
        leads = scrape_github(niche)
    elif source == "producthunt":
        leads = scrape_producthunt(niche)
    else:
        leads = []

    saved = 0
    for lead in leads:
        payload = {
            "action": "add",
            "location": lead.get("location", "Global"),
            "platform": lead.get("platform", source.title()),
            "email": lead.get("email", ""),
            "phone": lead.get("phone", "N/A")
        }
        if save_lead(B2C_URL, payload):
            saved += 1

    print(f"[B2C] Saved {saved}/{len(leads)} leads")

if __name__ == "__main__":
    print("=" * 60)
    print("LEAD AGENT ACTIVATED — 7 HOUR MODE")
    print("=" * 60)

    cycle = 0
    while (time.time() - START_TIME) < SEVEN_HOURS:
        cycle += 1
        print(f"\n[CYCLE {cycle}] Time elapsed: {int((time.time()-START_TIME)/60)} mins")

        run_b2b_round()
        wait = random.randint(30, 60)
        print(f"[WAIT] {wait}s")
        time.sleep(wait)

        run_b2c_round()
        wait = random.randint(30, 60)
        print(f"[WAIT] {wait}s")
        time.sleep(wait)

        # Run verification every 10 cycles
        if cycle % 10 == 0:
            run_verification(B2B_URL)
            run_verification(B2C_URL)

    print("\n[DONE] 7 Hours Complete")
    print("[FINAL VERIFICATION] Running...")
    run_verification(B2B_URL)
    run_verification(B2C_URL)
    print("[AGENT SHUTDOWN]")
