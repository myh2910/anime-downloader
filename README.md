# anime-downloader

Download animes with Korean subtitles.

## Requirements

- Install [Python](https://www.python.org/) with version ≥ 3.10.
- `pip install -r requirements.txt`
- Install [ChromeDriver](https://chromedriver.chromium.org/).

## Usage

Always execute `freeze_support` function before doing anything.

```python
from multiprocessing import freeze_support

from anime_downloader import ...

if __name__ == "__main__":
    freeze_support()
    ...
```

Here is an example.

```python
from multiprocessing import freeze_support

from anime_downloader import download_chapter

if __name__ == "__main__":
    freeze_support()

    download_chapter("체인소 맨 1화", quality="fast")
```

## To-do

- [x] Extract some data of video fragments before downloading them.
- [x] Use `selenium` to extract data of anime chapters before downloading them.
- [x] Extract anime data with headless WebDriver.
- [x] Implement a search function for animes.
