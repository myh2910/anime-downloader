import platform
import re

import requests
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from .config import CONFIG


def get_subtitle_url(source):
    """Get link of the subtitle file from the given URL.

    Args:
        source (str): Link of the video player.

    Returns:
        str or False: Link of the subtitle file. False if fails.
    """
    headers = CONFIG["headers"]
    headers["Referer"] = source

    res = requests.get(source, headers=headers)
    res.raise_for_status()

    content = res.content.decode("utf8")

    js_decoder = "function(p,a,c,k,e,d){e=function(c){return(c<a?'':e(parseInt(c/a)))+((c=c%a)>35?String.fromCharCode(c+29):c.toString(36))};if(!''.replace(/^/,String)){while(c--){d[e(c)]=k[c]||e(c)}k=[function(e){return d[e]}];e=function(){return'\\\\w+'};c=1};while(c--){if(k[c]){p=p.replace(new RegExp('\\\\b'+e(c)+'\\\\b','g'),k[c])}}return p}"
    py_decoder = "def decode(p,a,c,k,e,d):\n\tdef base36(n):\n\t\tr=[]\n\t\twhile n:r.append('0123456789abcdefghijklmnopqrstuvwxyz'[n%36]);n//=36\n\t\treturn''.join(reversed(r or'0'))\n\te=lambda n:(''if n<a else e(int(n/a)))+(chr(n+29)if(n:=n%a)>35 else base36(n))\n\td={e(n):k[n]or e(n)for n in range(c)}\n\treturn re.sub('[a-zA-Z0-9_]+',lambda m:d[m.group()],p).replace('\\\\/','/')"

    try:
        if (start := content.find(js_decoder)) != -1:
            end = content.find(")</script>", start)
            exec(py_decoder)
            content = eval("decode" + content[start + len(js_decoder) : end])
            if match := re.search('"kind":"captions","file":"(.*?)"', content):
                return match.group(1)
        raise
    except:
        try:
            if match := re.search("var videoCaption = '(.*?)';", content):
                return match.group(1)
            raise
        except:
            return False


def get_video_source(source):
    """Get link of the playlist file from the given URL.

    Args:
        source (str): Link of the video player.

    Returns:
        str: Link of the playlist file.
    """
    headers = CONFIG["headers"]
    headers["Referer"] = source

    res = requests.post(f"{source}&do=getVideo", headers=headers)
    res.raise_for_status()

    return res.json()["videoSource"]


def get_fragments_url(source, video_source):
    """Get links of the video fragments.

    Args:
        source (str): Link of the video player.
        video_source (str): Link of the playlist file.

    Returns:
        tuple of str and list: Tuple consisting of the video quality and the
        links of the video fragments.
    """
    headers = CONFIG["headers"]
    headers["Referer"] = source

    res = requests.get(video_source, headers=headers)
    res.raise_for_status()

    content = res.content.decode("utf8") + "\n"
    resolutions, heights = {}, []

    for _, height, url in re.findall("RESOLUTION=(.*?)x(.*?)\n(.*?)\n", content):
        if (idx := height.find(",")) >= 0:
            height = height[:idx]
        resolutions[f"{height}p"] = url
        heights.append(int(height))

    match CONFIG["quality"]:
        case "best":
            quality = f"{max(heights)}p"
        case "fast":
            quality = f"{min(heights)}p"
        case _:
            quality = CONFIG["quality"]

    res = requests.get(resolutions[quality], headers=headers)
    res.raise_for_status()

    content = res.content.decode("utf8")
    return quality, re.findall("&url=(.*?)\n", content)


def get_fragment_file(url, path):
    """Download a fragment file from the given URL.

    Args:
        url (str): Link of the video fragment.
        path (str): Path in which the fragment file will be stored.
    """
    print(f" Connecting to {url}...")

    try:
        res = requests.get(url)
        res.raise_for_status()
    except requests.exceptions.ConnectionError:
        res = requests.get(url)
        res.raise_for_status()

    with open(path, "wb") as file:
        file.write(res.content)


def get_webdriver():
    """Get ChromeDriver.

    Returns:
        Chrome: A ChromeDriver instance.
    """
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")

    if platform.system() == "Linux":
        options.binary_location = "/bin/google-chrome-stable"

    return uc.Chrome(options, use_subprocess=True)


def get_anime_data(*args, driver=None):
    """Get data of the given anime chapters.

    We use `undetected-chromedriver` package to bypass Cloudflare protections.

    Args:
        *args (str): Links of pages containing the video players.
        driver (Chrome or None): A ChromeDriver instance.

    Returns:
        list of tuple of str: Tuples consisting of the link of the video player
        and the title of each corresponding video.
    """
    if not args:
        return []

    if not driver:
        driver = get_webdriver()

    data = []
    print(":: Extracting player sources...")

    for url in args:
        driver.get(url)

        xpath = "//div[@class='view-padding']//iframe"
        source = (
            WebDriverWait(driver, CONFIG["wait"])
            .until(EC.presence_of_element_located((By.XPATH, xpath)))
            .get_attribute("src")
        )
        print(f" {source}")

        title = driver.find_element(By.XPATH, "//div[@class='view-title']//h1")
        data.append((source, title.text))

    driver.close()

    return data


def get_chapters_data(param, prop):
    """Get data of the chapters of an anime by its name or search function.

    Args:
        param (str): Parameter value.
        prop (str): "name" if it is the exact name of an anime, "search" if the
        search function should be used.

    Returns:
        list of tuple or None: Tuples consisting of the link of the video player
        and the title of each chapter of the anime. None if data is unavailable.
    """
    driver = get_webdriver()

    match prop:
        case "name":
            driver.get(f"{CONFIG['server']}/c/{param}")
        case "search":
            print(":: Extracting list of animes...")
            driver.get(
                "%s/bbs/search.php?srows=%d&sfl=wr_subject&stx=%s"
                % (CONFIG["server"], CONFIG["match"], param)
            )
            content = WebDriverWait(driver, CONFIG["wait"]).until(
                EC.presence_of_element_located((By.CLASS_NAME, "at-content"))
            )

            try:
                search_none = content.find_element(By.CLASS_NAME, "search-none")
                print(f" [Error] {search_none.text}")
                driver.close()
                return None
            except NoSuchElementException:
                xpath = "//div[@class='list-desc']//a"
                list_desc = content.find_elements(By.XPATH, xpath)
                width = len(str(len(list_desc) - 1))

                for idx, board in enumerate(list_desc):
                    title = board.find_element(By.CLASS_NAME, "post-title").text
                    print(" [" + str(idx).rjust(width) + "]", title)

                idx = input(":: Select anime index [default: 0] ").strip()
                if idx:
                    idx = int(idx)
                else:
                    idx = 0

                list_desc[idx].click()

    print(":: Extracting list of chapters available...")
    list_body = WebDriverWait(driver, CONFIG["wait"]).until(
        EC.presence_of_element_located((By.CLASS_NAME, "list-body"))
    )
    item_subject = list_body.find_elements(By.CLASS_NAME, "item-subject")[::-1]
    for idx, chapter in enumerate(item_subject):
        print(f" {chapter.text}")

    chapters = (chapter.get_attribute("href") for chapter in item_subject)
    return get_anime_data(*chapters, driver=driver)
