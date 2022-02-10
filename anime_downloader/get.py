"""
Extract video and subtitle data.

"""
import re

import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .config import CONFIG

def get_id_from_source(source):
	"""
	Get video ID from source.

	Parameters
	----------
	source : str
		Video data source.

	Returns
	-------
	str
		Video data ID.
	"""
	return re.search("data=(.*?)$", source).group(1)

def get_anime_data(*args):
	"""
	Get anime data from https://ohli24.net/.

	We use `undetected-chromedriver` package to bypass cloudflare protections.
	For technical reasons, headless ChromeDriver is not possible.

	Parameters
	----------
	args : tuple of str
		Anime chapter names that come after https://ohli24.net/e/.

	Returns
	-------
	list of tuple or tuple of str
		Data of animes.
	"""
	data = []

	options = uc.ChromeOptions()
	options.add_argument("--start-maximized")
	# options.add_argument("--headless")

	driver = uc.Chrome(options=options)
	for name in args:
		driver.get(f"https://ohli24.net/e/{name}")

		source = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
			(By.XPATH, "//div[@id='movie_player']//iframe")
		)).get_attribute("src")
		title = driver.find_element(
			By.XPATH, "//div[@class='view-title']//h1"
		).text
		data.append((source, title))

	driver.quit()

	if len(args) == 1:
		return data[0]
	return data

def get_subtitle_url(source):
	"""
	Get subtitle url.

	Parameters
	----------
	source : str
		Video data source.

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
		Video data source.

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
		Video data source.
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

	resolutions, heights = {}, []
	for _, height, url in re.findall(
		"RESOLUTION=(.*?)x(.*?)\n(.*?)\n", res.content.decode("utf8") + "\n"
	):
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

	return quality, re.findall("&url=(.*?)\n", res.content.decode("utf8"))

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

	res = requests.get(url)
	res.raise_for_status()

	with open(path, "wb") as file:
		file.write(res.content)
