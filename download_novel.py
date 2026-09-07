# from gevent import monkey
# monkey.patch_all()

import re
from kakuyomub.main import main as download
from kakuyomub.works import Works

url = input("Paste the kakuyomu.jp novel URL: ")
# Remove all whitespace and non-printable characters
url = re.sub(r'\s+', '', url)

# Accept either a full URL or just the numeric ID
match = re.search(r'/works/(\d+)', url) or re.fullmatch(r'\d+', url)
if not match:
    print(f"Couldn't find a work ID. Got: {repr(url)}")
    print("Expected something like: https://kakuyomu.jp/works/16817330668128729529")
    exit(1)

work_id = match.group(1) if match.lastindex else match.group(0)

action = input("Download [a]ll episodes or [s]pecific episodes? [a]: ").strip().lower()

if action == 's':
    print("\nFetching episode list...")
    w = Works(work_id, download=False)
    episodes = w.list_episodes()
    print(f"\nEpisodes for: {w.title}\n")
    for idx, (ep_id, title) in enumerate(episodes, 1):
        print(f"[{idx:03d}] {ep_id} - {title}")
    
    selected = input("\nEnter episode IDs to download (comma-separated): ")
    episode_ids = [eid.strip() for eid in selected.split(',') if eid.strip()]
    
    if not episode_ids:
        print("No episode IDs provided. Exiting.")
        exit(1)
    
    print(f"\nDownloading {len(episode_ids)} selected episode(s)...")
    download(work_id, "./", episodes=episode_ids)
else:
    print(f"Downloading work {work_id}...")
    download(work_id)

print("Done! The EPUB has been saved in the current folder.")
