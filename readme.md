# Kakuyomub
<p align="center">
  <img src="icon.png" style="width:30%;" />
</p>

Convert Kakuyomu articles to Epub file | カクヨムの文章をEPUBに転写する | カクヨム文章转换为Epub

This fork adds selective episode downloading and multiple output formats on top of the original [XHLin-gamer/kakuyomub](https://github.com/XHLin-gamer/kakuyomub).

## Usage

Make sure python is available, then
```bash
git clone https://github.com/Handy-Wibowo/kakuyomub.git
cd kakuyomub
pip install -r requirement.txt
python -m kakuyomub.main WORK_ID 
```

or if you want to point the downloaded file to a folder:
```bash
python -m kakuyomub.main WORK_ID --path C:\Users\xhaug\OneDrive\Desktop
```

```bash
pip install kakuyomub
>>> kakuyomub.download(16817330650993330082, "./")
```

replace the `WORK_ID` with the カクヨム work id.

## Selective Episode Downloads

You can download only selected chapters instead of the entire novel.

### List all episodes first

```bash
python -m kakuyomub.main WORK_ID --list-episodes
```

Output example:
```
[001] 16817330668128757674 - 第1話
[002] 16817330668128757675 - 第2話
...
```

### Download specific episodes by ID

```bash
python -m kakuyomub.main WORK_ID --episodes 16817330668128757674,16817330668128757675
```

### Download a range of episodes by index

Download episodes 1 through 10:

```bash
python -m kakuyomub.main WORK_ID --range 1-10
```

### Download the most recent N episodes

Download the latest 5 episodes:

```bash
python -m kakuyomub.main WORK_ID --recent 5
```

## Output Formats

By default, the tool creates a single `.epub` file. You can also output as separate `.txt` or `.html` files (one file per episode).

```bash
python -m kakuyomub.main WORK_ID --format epub   # default
python -m kakuyomub.main WORK_ID --format txt
python -m kakuyomub.main WORK_ID --format html
```

You can combine format with any selection option:

```bash
python -m kakuyomub.main WORK_ID --recent 10 --format txt --path ./output
```

This will create a folder like `./output/<title>_TXT/` containing the 10 most recent episodes as `.txt` files.

## Interactive CLI

CLI is also available with `download_novel.py`

```bash
git clone https://github.com/Handy-Wibowo/kakuyomub.git
cd kakuyomub
pip install -r requirement.txt
python download_novel
```

and then paste the **url** of the novel you want to download. (yes, you can paste the link of page like https://kakuyomu.jp/works/16817139554696751535 to the shell directly.)

The interactive mode supports:
- Downloading all episodes
- Downloading specific episodes by ID
- Downloading a range of episodes by index
- Downloading the most recent N episodes
- Choosing the output format (epub / txt / html)

## EXAMPLE

the url of 「クーデレなセフレと小悪魔な後輩が義妹になったので距離を置きたい。」 is https://kakuyomu.jp/works/16817330668128729529

The id of the work is the last trunk of the url, which is 16817330668128729529

```bash
# use the id to download work
python -m kakuyomub.main 16817330668128729529
```

and the result is as:
![alt text](image.png)

## Changes from the original fork

- **Selective episode downloads**
  - `--episodes ID1,ID2,...` to download specific episodes
  - `--range START-END` to download a range by index
  - `--recent N` to download the N most recent episodes
  - `--list-episodes` to list all episode IDs without downloading
- **Multiple output formats**
  - `--format epub` (default)
  - `--format txt` exports one `.txt` file per episode
  - `--format html` exports one `.html` file per episode
- **Interactive script** `download_novel.py` updated to support all new options
- Internal refactor of `Works`/`chapter` to allow metadata fetching without auto-downloading all episodes
