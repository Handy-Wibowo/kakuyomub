import sys
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")

from .epub_maker import Epub_maker

from .works import Works, chapter

import argparse

parser = argparse.ArgumentParser(description='カクヨム => Epub')
parser.add_argument('work_id', help='the id of the work')
parser.add_argument('--path', default="./", help='the target path')
parser.add_argument('--episodes', default=None, help='comma-separated episode IDs to download (e.g., id1,id2,id3)')
parser.add_argument('--list-episodes', action='store_true', help='list all episode IDs and titles without downloading')

def main(id, path="./", episodes=None) -> None:
    """download work to epub with id, and move the file to the path

    Args:
        id (str|int): the work id
        path (str, optional): the target path. Defaults to "./".
        episodes (list[str], optional): specific episode IDs to download. Defaults to None (download all).
    """
    w = Works(id, download=(episodes is None))

    title = w.title
    maker = Epub_maker('test_epub1', title, w.author)

    if episodes is not None:
        # Download only selected episodes
        selected_eps = w.download_specific_episodes(episodes)
        toc = [maker.add_chapter('', ep.title, ep.html_file, id=ep.episode_id) for ep in selected_eps]
    else:
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


if __name__ == "__main__":
    args = parser.parse_args()

    if args.list_episodes:
        w = Works(args.work_id, download=False)
        print(f"Episodes for: {w.title}\n")
        for idx, (ep_id, title) in enumerate(w.list_episodes(), 1):
            print(f"[{idx:03d}] {ep_id} - {title}")
        sys.exit(0)

    episode_ids = None
    if args.episodes:
        episode_ids = [eid.strip() for eid in args.episodes.split(',') if eid.strip()]

    main(args.work_id, args.path, episodes=episode_ids)
