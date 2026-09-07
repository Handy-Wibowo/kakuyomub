# Kakuyomub
<p align="center">
  <img src="icon.png" style="width:30%;" />
</p>

Convert Kakuyomu articles to Epub file | カクヨムの文章をEPUBに転写する | カクヨム文章转换为Epub

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

## Download specific episodes only

You can download only selected episodes by their episode IDs.

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

### Download selected episodes

```bash
python -m kakuyomub.main WORK_ID --episodes 16817330668128757674,16817330668128757675
```

You can also combine with `--path`:

```bash
python -m kakuyomub.main WORK_ID --episodes ID1,ID2,ID3 --path ./output
```

## Interactive CLI

CLI is also available with `download_novel.py`

```bash
git clone https://github.com/Handy-Wibowo/kakuyomub.git
cd kakuyomub
pip install -r requirement.txt
python download_novel
```

and then paste the **url** of the novel you want to download. (yes, you can paste the link of page like https://kakuyomu.jp/works/16817139554696751535 to the shell directly.)

The interactive mode now also supports choosing between downloading **all episodes** or **specific episodes**.

## EXAMPLE

the url of 「クーデレなセフレと小悪魔な後輩が義妹になったので距離を置きたい。」 is https://kakuyomu.jp/works/16817330668128729529

The id of the work is the last trunk of the url, which is 16817330668128729529

```bash
# use the id to download work
python -m kakuyomub.main 16817330668128729529
```

and the result is as:
![alt text](image.png)
