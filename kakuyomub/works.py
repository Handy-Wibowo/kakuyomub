from loguru import logger
from .downloader import Downloader
from .episode import Episodes
from requests import Session
from bs4 import BeautifulSoup
from PrettyPrint import PrettyPrintTree

import json
import re



class chapter():
    def __init__(self,title, id, json = None, level = 0, work_id = None, toc_key = None, download = True) -> None:
        self.title = title
        self.id = id
        self.level = level
        self.children: list = list()
        self.episodes: list[Episodes] = list()
        self.downloader = Downloader(self.episodes)
        self.work_id = work_id
        self.toc_key = toc_key
        self._downloaded = False
        
        if json and download:
            self.json = json
            self.match_episode(self.json)
        elif json:
            self.json = json
            self._build_episodes(json)

    def _build_episodes(self, json):
        """Build episode objects without downloading."""
        key = self.toc_key or f"TableOfContentsChapter:{self.id}"
        episode_data = json[key].get('episodeUnions', [])
            
        for item in episode_data:
            episode_id = item['__ref'].split(':')[-1]
            episode_data = json[f"Episode:{episode_id}"]
            episode_title = episode_data['title']
            self.episodes.append(Episodes(self.work_id, episode_id, episode_title))

    def match_episode(self, json):
        if self._downloaded:
            return
        
        # Ensure episodes are built
        if not self.episodes:
            self._build_episodes(json)
        
        logger.info(f"Downloading: {self.title}")   
        self.downloader.download()
        self._downloaded = True
        

    def download(self):
        """Download episodes for this chapter."""
        if hasattr(self, 'json') and self.json:
            self.match_episode(self.json)
        elif self.episodes:
            logger.info(f"Downloading: {self.title}")   
            self.downloader.download()
            self._downloaded = True

    def add_child(self, child):
        self.children.append(child)
    
    def get_episodes(self):
        return self.episodes
    
    def collect_episodes(self):
        """Collect all episodes recursively without downloading."""
        eps = list(self.episodes)
        for child in self.children:
            eps.extend(child.collect_episodes())
        return eps
    
    def get_child_info(self):
        res = []
        
        for child in self.children:
            res += [child.title]
            if child.children:
                res += [child.get_child_info()]
        return res
    
    def __str__(self) -> str:
        return f"{self.title} + {self.get_child_info()}"
    
def parse_meta_json(_json: json, download: bool = True) -> dict:
    res = {}
    # allocate the data attribute of the json file
    # see bench.json to see more details on this json file
    data = _json['props']['pageProps']['__APOLLO_STATE__']
    
    # extract work id with regex 
    text = ''.join(data['ROOT_QUERY'].keys())
    x = re.findall(r'(?<=\()(.+?)(?=\))', text)
    meta_data = {}
    for x_text in x:
        k = dict(json.loads(x_text))
        meta_data.update(k)
    
    work_id = meta_data["id"]
    word_data = data[f'Work:{meta_data["id"]}']
    res['title'] = word_data['title']
    res['catchphrase'] = word_data['catchphrase']
    res['introduction'] = word_data['introduction']
    res['tagLabels'] = word_data['tagLabels']
    author_ref = word_data.get('author', {}).get('__ref')
    res['author'] = data.get(author_ref, {}).get('activityName', '') if author_ref else ''

    # generate the chapter tree structure
    chap_list = _get_table_of_contents(word_data)
    logger.debug(f"chap_list: {chap_list}")
    
    # if there is no chapter tree structure, hint the flat structure, which is no chapter segmentation
    if chap_list == ['TableOfContentsChapter:']: 
        logger.debug('flat structure')
        root = chapter(res['title'], work_id, data, 0, work_id, chap_list[0], download=download)
        return res, root
    else:
        root = chapter(res['title'],res['title'])
        stack = [root]
        
        # rare case for first chapter is flat, following chapters are tree structure, e.g. https://kakuyomu.jp/works/16817139554696751535
        if chap_list[0] == 'TableOfContentsChapter:':
            logger.debug('first chapter is flat, following chapters are tree structure')
            root = chapter(res['title'], work_id, data, 0, work_id, chap_list[0], download=download)
            stack = [root]
            chap_list = chap_list[1:]
        
        
        # Build the content tree
        for idx, chap_id in enumerate(chap_list):
            toc_j = data[chap_id]
            chapter_ref = toc_j.get('chapter', {}).get('__ref')
            chap_j = data.get(chapter_ref, toc_j)
            level, title =  chap_j['level'], chap_j['title']
            _id = chap_j['id']
            new = chapter(title, _id, data, level, work_id, chap_id, download=download)
            if stack[-1].level < level:  
                stack[-1].add_child(new)
                stack.append(new)
            elif stack[-1].level == level:
                stack.pop(-1)
                stack[-1].add_child(new)
                stack.append(new)
            elif stack[-1].level > level:
                stack[level-1].add_child(new)
                stack.append(new)

        # use PrettyPrintTree to visualize the content tree
        pt = PrettyPrintTree(lambda x: x.children, lambda x: x.title,orientation=PrettyPrintTree.Horizontal)
        pt(root)
    
        
        
        return res, root


def _get_table_of_contents(word_data: dict) -> list[str]:
    if 'tableOfContentsV2' in word_data:
        return [item['__ref'] for item in word_data['tableOfContentsV2']]

    chap_list = []
    for table_dict in word_data.get('tableOfContents', []):
        chap_list += [*table_dict.values()]
    return chap_list
    


class Works():
    def __init__(self, work_id, download: bool = True) -> None:
        self.work_id = work_id
        self._work_url = f'https://kakuyomu.jp/works/{self.work_id}'

        self.session = Session()
        
        self.json_raw : str = self.get_raw_json()
        parse_result = parse_meta_json(json.loads(self.json_raw), download=download)
        self.res : dict = parse_result[0]
        self.content : chapter = parse_result[1]
        # self.author = res['']
        self.title = self.res['title']
        self.catchphrase = self.res['catchphrase']
        self.introduction = self.res['introduction']
        self.tagLabels = self.res['tagLabels']
        self.author = self.res['author']

    def list_episodes(self) -> list[tuple[str, str]]:
        """Return list of (episode_id, title) without downloading."""
        eps = self.content.collect_episodes()
        return [(ep.episode_id, ep.title) for ep in eps]

    def download_specific_episodes(self, episode_ids: list[str]) -> list[Episodes]:
        """Download only the specified episode IDs."""
        all_eps = self.content.collect_episodes()
        id_set = set(episode_ids)
        selected = [ep for ep in all_eps if ep.episode_id in id_set]
        
        if not selected:
            logger.warning("No matching episodes found for the given IDs")
            return []
        
        downloader = Downloader(selected)
        logger.info(f"Downloading {len(selected)} selected episode(s)")
        downloader.download()
        return selected

    def download_episode_range(self, start: int, end: int) -> list[Episodes]:
        """Download episodes by their 1-based index range (inclusive)."""
        all_eps = self.content.collect_episodes()
        total = len(all_eps)
        
        if start < 1:
            start = 1
        if end > total:
            end = total
        if start > end:
            logger.warning("Invalid range: start > end")
            return []
        
        selected = all_eps[start - 1:end]
        if not selected:
            logger.warning("No episodes in the given range")
            return []
        
        downloader = Downloader(selected)
        logger.info(f"Downloading episodes {start} to {end} ({len(selected)} episode(s))")
        downloader.download()
        return selected

    def download_recent_episodes(self, count: int) -> list[Episodes]:
        """Download the most recent N episodes."""
        all_eps = self.content.collect_episodes()
        total = len(all_eps)
        
        if count < 1:
            logger.warning("Recent episode count must be at least 1")
            return []
        if count > total:
            count = total
        
        selected = all_eps[-count:]
        if not selected:
            logger.warning("No episodes found")
            return []
        
        downloader = Downloader(selected)
        logger.info(f"Downloading {len(selected)} most recent episode(s)")
        downloader.download()
        return selected

        
    def get_raw_json(self) -> str:
        
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        
        try:
            response = self.session.get(self._work_url)
            response.raise_for_status()
            # f = open('./test.html','w', encoding='utf8')
            # f.write(response.text)
            # f.close()
        except Exception as e:
            logger.error(f"{e}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        json_data = soup.find('script', id="__NEXT_DATA__")
        return json_data.text

    def get_content(self) -> chapter:
        return self.content
    
    def __str__(self) -> str:
        if not self.is_check():
            return f"[Unfinished] {self._work_url}"
        
if __name__ == "__main__":
    work = Works(16818093076629589128)
    print(*work.get_content().get_episodes())
    
    
    # flat:2912051598397383103
    
    # semi flat: https://kakuyomu.jp/works/16817139554696751535
    

    
    
