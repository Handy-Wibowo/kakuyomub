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

print("\nOptions:")
print("  [a] Download all episodes")
print("  [s] Download specific episodes by ID")
print("  [r] Download a range of episodes by index")
print("  [n] Download the most recent N episodes")
action = input("Choose an option [a]: ").strip().lower() or 'a'

episodes = None
episode_range = None
recent = None

if action == 's':
    print("\nFetching episode list...")
    w = Works(work_id, download=False)
    episodes_list = w.list_episodes()
    print(f"\nEpisodes for: {w.title}\n")
    for idx, (ep_id, title) in enumerate(episodes_list, 1):
        print(f"[{idx:03d}] {ep_id} - {title}")
    
    selected = input("\nEnter episode IDs to download (comma-separated): ")
    episodes = [eid.strip() for eid in selected.split(',') if eid.strip()]
    
    if not episodes:
        print("No episode IDs provided. Exiting.")
        exit(1)

elif action == 'r':
    rng = input("Enter episode range (e.g., 1-10): ").strip()
    rng_match = re.fullmatch(r'(\d+)\s*-\s*(\d+)', rng)
    if not rng_match:
        print("Invalid range format. Expected: START-END")
        exit(1)
    episode_range = (int(rng_match.group(1)), int(rng_match.group(2)))

elif action == 'n':
    try:
        recent = int(input("How many recent episodes to download? ").strip())
    except ValueError:
        print("Invalid number. Exiting.")
        exit(1)

output_format = input("\nOutput format [epub/txt/html] (default: epub): ").strip().lower()
if output_format not in ["epub", "txt", "html"]:
    output_format = "epub"

print(f"\nDownloading work {work_id}...")
download(work_id, "./", episodes=episodes, episode_range=episode_range, recent=recent, output_format=output_format)
print("Done!")
