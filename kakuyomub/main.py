import os
import re
import sys
from pathlib import Path
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")

from bs4 import BeautifulSoup

from .epub_maker import Epub_maker

from .works import Works, chapter

import argparse


def _sanitize_filename(name: str, max_len: int = 100) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > max_len:
        name = name[:max_len].strip()
    return name if name else "chapter"


def _html_to_text(html_str: str) -> str:
    soup = BeautifulSoup(html_str, "html.parser")
    for tag in soup(["script", "style", "nav"]):
        tag.decompose()

    paragraphs = []
    for elem in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li"]):
        text = elem.get_text(separator=" ", strip=True)
        text = " ".join(text.split())
        if text:
            paragraphs.append(text)

    if not paragraphs:
        text = soup.get_text(separator="\n", strip=True)
        paragraphs = [line for line in text.splitlines() if line.strip()]

    return "\n\n".join(paragraphs)


def _save_as_txt(episodes: list, output_dir: Path, title: str):
    folder = output_dir / f"{_sanitize_filename(title)}_TXT"
    folder.mkdir(parents=True, exist_ok=True)

    for idx, ep in enumerate(episodes, start=1):
        text = _html_to_text(ep.html_file)
        filename = f"{idx:03d}_{_sanitize_filename(ep.title)}.txt"
        (folder / filename).write_text(text, encoding="utf-8")

    logger.info(f"Saved {len(episodes)} .txt file(s) to {folder}")


def _save_as_html(episodes: list, output_dir: Path, title: str):
    folder = output_dir / f"{_sanitize_filename(title)}_HTML"
    folder.mkdir(parents=True, exist_ok=True)

    for idx, ep in enumerate(episodes, start=1):
        filename = f"{idx:03d}_{_sanitize_filename(ep.title)}.html"
        (folder / filename).write_text(ep.html_file, encoding="utf-8")

    logger.info(f"Saved {len(episodes)} .html file(s) to {folder}")


def _save_as_epub(episodes: list, output_dir: Path, title: str, author: str):
    maker = Epub_maker('test_epub1', title, author)
    toc = [maker.add_chapter('', ep.title, ep.html_file, id=ep.episode_id) for ep in episodes]
    maker.set_toc(toc)
    maker.set_spine()
    maker.add_navi()
    maker.write_epub(str(output_dir))


parser = argparse.ArgumentParser(description='カクヨム => Epub/TXT/HTML')
parser.add_argument('work_id', help='the id of the work')
parser.add_argument('--path', default="./", help='the target path')
parser.add_argument('--episodes', default=None, help='comma-separated episode IDs to download (e.g., id1,id2,id3)')
parser.add_argument('--range', default=None, help='download a range of episodes by 1-based index (e.g., 1-10)')
parser.add_argument('--recent', type=int, default=None, help='download the most recent N episodes')
parser.add_argument('--format', default="epub", choices=["epub", "txt", "html"], help='output format (default: epub)')
parser.add_argument('--list-episodes', action='store_true', help='list all episode IDs and titles without downloading')


def main(id, path="./", episodes=None, episode_range=None, recent=None, output_format="epub") -> None:
    """download work with id, and save the result to the path

    Args:
        id (str|int): the work id
        path (str, optional): the target path. Defaults to "./".
        episodes (list[str], optional): specific episode IDs to download. Defaults to None.
        episode_range (tuple[int, int], optional): 1-based inclusive range (start, end). Defaults to None.
        recent (int, optional): number of most recent episodes to download. Defaults to None.
        output_format (str, optional): output format - "epub", "txt", or "html". Defaults to "epub".
    """
    # Determine if we need metadata only (no auto-download)
    selective = episodes is not None or episode_range is not None or recent is not None
    w = Works(id, download=not selective)

    title = w.title
    author = w.author

    if episodes is not None:
        selected_eps = w.download_specific_episodes(episodes)
    elif episode_range is not None:
        start, end = episode_range
        selected_eps = w.download_episode_range(start, end)
    elif recent is not None:
        selected_eps = w.download_recent_episodes(recent)
    else:
        # Default: download all episodes and preserve chapter tree for EPUB
        selected_eps = w.content.collect_episodes()
        if output_format == "epub":
            maker = Epub_maker('test_epub1', title, author)

            def build_pages(node: chapter, toc: list):
                for episode in node.episodes:
                    chap = maker.add_chapter('', episode.title, episode.html_file, id=episode.episode_id)
                    toc.append(chap)
                for chapter_node in node.children:
                    toc.append([maker.section(chapter_node.title), build_pages(chapter_node, list())])
                return toc

            toc = build_pages(w.content, list())
            maker.set_toc(toc)
            maker.set_spine()
            maker.add_navi()
            maker.write_epub(path)
            return
        else:
            # For txt/html without selection, we need to download all first
            w.content.download()
            selected_eps = w.content.collect_episodes()

    if not selected_eps:
        logger.warning("No episodes were downloaded")
        return

    output_path = Path(path)
    output_path.mkdir(parents=True, exist_ok=True)

    if output_format == "txt":
        _save_as_txt(selected_eps, output_path, title)
    elif output_format == "html":
        _save_as_html(selected_eps, output_path, title)
    else:
        _save_as_epub(selected_eps, output_path, title, author)


if __name__ == "__main__":
    args = parser.parse_args()

    if args.list_episodes:
        w = Works(args.work_id, download=False)
        print(f"Episodes for: {w.title}\n")
        for idx, (ep_id, title) in enumerate(w.list_episodes(), 1):
            print(f"[{idx:03d}] {ep_id} - {title}")
        sys.exit(0)

    # Validate mutually exclusive selection options
    selection_options = [args.episodes, args.range, args.recent]
    selected_count = sum(1 for opt in selection_options if opt is not None)
    if selected_count > 1:
        parser.error("Only one of --episodes, --range, or --recent can be used at a time")

    episode_ids = None
    if args.episodes:
        episode_ids = [eid.strip() for eid in args.episodes.split(',') if eid.strip()]

    episode_range = None
    if args.range:
        match = re.fullmatch(r'(\d+)\s*-\s*(\d+)', args.range)
        if not match:
            parser.error("--range must be in the format START-END (e.g., 1-10)")
        episode_range = (int(match.group(1)), int(match.group(2)))

    main(
        args.work_id,
        args.path,
        episodes=episode_ids,
        episode_range=episode_range,
        recent=args.recent,
        output_format=args.format
    )
