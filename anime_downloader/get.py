"""
Extract video and subtitle data.

"""
import platform
import re

import requests
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import CONFIG


def get_subtitle_url(source):
	"""
	Get subtitle url.

	Parameters
	----------
	source : str
		Player source.

	Returns
	-------
	str
		Subtitle file link.
	"""
	headers = CONFIG['headers']
	headers['Referer'] = source

	res = requests.get(source, headers=headers)
	res.raise_for_status()

	decoded_content = res.content.decode("utf8")
	return re.search("var videoCaption = '(.*?)';", decoded_content).group(1)

def get_subtitle_file(url, path):
	"""
	Download subtitle file.

	Parameters
	----------
	url : str
		Subtitle file link.
	path : str
		Subtitle file path.
	"""
	print(f" Connecting to {url}...")
	res = requests.get(url)
	res.raise_for_status()

	with open(path, "wb") as file:
		file.write(res.content)

def get_video_source(source):
	"""
	Get code of the video source.

	Parameters
	----------
	source : str
		Player source.

	Returns
	-------
	str
		Video source.
	"""
	headers = CONFIG['headers']
	headers['Referer'] = source

	res = requests.post(f"{source}&do=getVideo", headers=headers)
	res.raise_for_status()

	return res.json()['videoSource']

def get_fragments_url(source, video_source):
	"""
	Get fragment links.

	Parameters
	----------
	source : str
		Player source.
	video_source : str
		Video source.

	Returns
	-------
	tuple of str and list
		Fragment links.
	"""
	headers = CONFIG['headers']
	headers['Referer'] = source

	res = requests.get(video_source, headers=headers)
	res.raise_for_status()

	content = res.content.decode("utf8") + "\n"
	resolutions, heights = {}, []

	for _, height, url in re.findall("RESOLUTION=(.*?)x(.*?)\n(.*?)\n", content):
		if (idx := height.find(",")) >= 0:
			height = height[:idx]
		resolutions[f'{height}p'] = url
		heights.append(int(height))

	match CONFIG['quality']:
		case "best":
			quality = f"{max(heights)}p"
		case "fast":
			quality = f"{min(heights)}p"
		case _:
			quality = CONFIG['quality']

	res = requests.get(resolutions[quality], headers=headers)
	res.raise_for_status()

	content = res.content.decode("utf8")
	return quality, re.findall("&url=(.*?)\n", content)

def get_fragment_file(url, path):
	"""
	Download fragment file.

	Parameters
	----------
	url : str
		Fragment file link.
	path : str
		Fragment file path.
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

def get_id_from_source(source):
	"""
	Get player ID from source.

	Parameters
	----------
	source : str
		Player source.

	Returns
	-------
	str or None
		Player ID.
	"""
	if search := re.search("data=(.*?)$", source):
		return f"{search.group(1)} [pigplayer]"
	if search := re.search("video/(.*?)$", source):
		return f"{search.group(1)} [ndoodle]"
	return None

def get_source_from_id(player_id):
	"""
	Get player source from ID.

	Parameters
	----------
	player_id : str
		Player ID.

	Returns
	-------
	str or None
		Player source.
	"""
	if search := re.search(r"(.*?) \[pigplayer\]", player_id):
		return f"https://pigplayer.com/player/index.php?data={search.group(1)}"
	if search := re.search(r"(.*?) \[ndoodle\]", player_id):
		return f"https://ndoodle.xyz/video/{search.group(1)}"
	return None

def get_chrome_driver():
	"""
	Get ChromeDriver.

	An error occurs with headless WebDriver:
	>>> options.add_argument("--headless")

	Returns
	-------
	Chrome
		ChromeDriver.
	"""
	options = uc.ChromeOptions()
	options.add_argument("--start-maximized")

	if platform.system() == "Linux":
		options.binary_location = "/bin/google-chrome-stable"

	driver = uc.Chrome(options=options)

	if CONFIG['minimize']:
		driver.minimize_window()

	return driver

def get_anime_data(*args, driver=None):
	"""
	Get anime data from https://ohli24.net/.

	We use `undetected-chromedriver` package to bypass Cloudflare protections.

	Parameters
	----------
	args : tuple of str
		Anime chapter links.
	driver : Chrome or None, optional
		ChromeDriver object.

	Returns
	-------
	list of tuple
		Data of animes.
	"""
	if not driver:
		driver = get_chrome_driver()

	data = []
	print(":: Extracting player source...")
	for url in args:
		driver.get(url)

		xpath = "//div[@id='movie_player']//iframe"
		source = WebDriverWait(driver, CONFIG['wait']).until(
			EC.presence_of_element_located((By.XPATH, xpath))
		).get_attribute("src")
		print(f" {source}")

		title = driver.find_element(By.XPATH, "//div[@class='view-title']//h1")
		data.append((source, title.text))

	driver.quit()
	return data

def get_chapters_data(param, prop):
	"""
	Get anime chapters data by anime name, board id or search function.

	Parameters
	----------
	param : str
		Parameter value.
	prop : str
		Parameter type.

	Returns
	-------
	list of tuple or None
		Anime chapters data available.
	"""
	driver = get_chrome_driver()

	match prop:
		case "name":
			driver.get(f"https://ohli24.net/c/{param}")
		case "id":
			driver.get(
				f"https://ohli24.net/bbs/board.php?bo_table=fin&wr_id={param}"
			)
		case "search":
			print(":: Extracting list of animes...")
			driver.get(
				f"https://ohli24.net/bbs/search.php?srows={CONFIG['show_rows']}\
&sfl=wr_subject&stx={param}"
			)
			content = WebDriverWait(driver, CONFIG['wait']).until(
				EC.presence_of_element_located((By.CLASS_NAME, "at-content"))
			)

			try:
				search_none = content.find_element(By.CLASS_NAME, "search-none")
				print(f" [Error] {search_none.text}")
				driver.quit()
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
	list_body = WebDriverWait(driver, CONFIG['wait']).until(
		EC.presence_of_element_located((By.CLASS_NAME, "list-body"))
	)
	item_subject = list_body.find_elements(By.CLASS_NAME, "item-subject")[::-1]
	for idx, chapter in enumerate(item_subject):
		print(f" {chapter.text}")

	chapters = (chapter.get_attribute("href") for chapter in item_subject)
	return get_anime_data(*chapters, driver=driver)
