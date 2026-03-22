---
name: trend-scraping
created_by: heisenberg
created_at: 2026-03-20
version: 1
success_rate: 88%
---

# TikTok Trend Scraping

## What This Skill Does
Fetches trending sounds, viral hooks, and competitor data from TikTok.

## Data Sources

### 1. Trending Sounds (Creative Center)
```python
# Scrape __NEXT_DATA__ from Creative Center HTML (no API key needed)
resp = requests.get("https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/en")
match = re.search(r'__NEXT_DATA__[^{]*({.*?})</script>', resp.text)
sounds = json.loads(match.group(1))["props"]["pageProps"]["data"]["soundList"]
```
Works from Singapore VM. Blocked from some other IPs.

### 2. Hashtag Videos (tikwm)
```python
# Step 1: Get challenge_id
r = requests.get("https://tikwm.com/api/challenge/search", params={"keywords": "studytok"})
cid = r.json()["data"]["challenge_list"][0]["id"]

# Step 2: Get top videos
r2 = requests.get("https://tikwm.com/api/challenge/posts", params={"challenge_id": cid, "count": 20})
videos = r2.json()["data"]["videos"]
```

### 3. Audio Download (tikwm)
```python
# Get exact audio from a video
r = requests.get(f"https://tikwm.com/api/?url=https://www.tiktok.com/@x/video/{vid_id}")
music_url = r.json()["data"]["music_info"]["play"]
audio = requests.get(music_url)
```

## Key Finding
Chopin Nocturne No. 2 is used in 5 of the top 30 StudyTok videos. It's public domain (royalty free) and doesn't get muted.
