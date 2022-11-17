"""
Write video and subtitle file.

"""
import os
from concurrent.futures import ThreadPoolExecutor

import requests

from . import get
from .config import CONFIG

tmp = {}

def __init__(param, prop, title=None):
	"""
	Initialize module.

	Parameters
	----------
	param : str
		Parameter value.
	prop : str
		Parameter type.
	title : str or None, optional
		Video title.

	Returns
	-------
	source : str
		Player source.
	"""
	match prop:
		case "name":
			source, title = get.get_anime_data(f"https://ohli24.net/e/{param}")[0]
		case "source":
			source = param
		case "id":
			source = get.get_source_from_id(param)

	if not title:
		print(":: Title not found.")
		return False

	title = "".join("_" if char in "\\/:*?\"<>|" else char for char in title)
	player_id = get.get_id_from_source(source)

	tmp['path'] = os.path.join(CONFIG['home'], f"{title}-{player_id}")
	tmp['output'] = os.path.join(tmp['path'], f"{title}.{CONFIG['ext']}")

	if not os.path.exists(tmp['output']):
		if not os.path.exists(tmp['path']):
			os.makedirs(tmp['path'])

	return source, title

def wget(url, path, session=requests, err_format="%s"):
	_err = ""
	max_repeat = CONFIG['repeat']

	while max_repeat > 0:
		try:
			res = session.get(url)
			res.raise_for_status()
			with open(path, "wb") as file:
				file.write(res.content)
			return True
		except Exception as err:
			_err = err
		max_repeat -= 1

	print(err_format % _err)
	tmp['status'] = False

	return False

def write_subtitle(source, title):
	"""
	Write subtitle file.

	Parameters
	----------
	source : str
		Player source.
	title : str
		Video title.
	"""
	print(":: Extracting subtitle file...")

	if url := get.get_subtitle_url(source):
		path = os.path.join(tmp['path'], f"{title}{os.path.splitext(url)[1]}")
		if os.path.exists(path):
			print(f" File {path} already exists.")
		else:
			print(f" Connecting to {url}...")
			wget(url, path)
	else:
		print(" Subtitle file does not exist.")

def get_fragment(task):
	fragment, path, session, idx = task
	print(f" [{idx}] Connecting to {fragment}...")
	return wget(fragment, path, session, f" [{idx}] %s")

def write_fragments(source):
	"""
	Download video fragments.

	Parameters
	----------
	source : str
		Player source.

	Returns
	-------
	bool
		Indicates whether the process was successful or not.
	"""
	print(f":: Extracting video fragments from {source}...")
	if os.path.exists(tmp['output']):
		print(f" File {tmp['output']} already exists.")
		return False

	video_source = get.get_video_source(source)
	quality, fragments_url = get.get_fragments_url(source, video_source)
	print(f" {len(fragments_url)} fragments found.")

	tmp['fragments_path'] = os.path.join(tmp['path'], quality)
	if not os.path.exists(tmp['fragments_path']):
		os.makedirs(tmp['fragments_path'])

	tmp['num_fragments'] = len(fragments_url)
	tmp['fragment_file'] = os.path.join(tmp['fragments_path'], "%d.ts")
	tmp['status'] = True

	with requests.Session() as session:
		tasks = []
		for i in range(tmp['num_fragments']):
			url = fragments_url[i]
			path = tmp['fragment_file'] % i

			if os.path.exists(path):
				print(f" File {path} already exists.")
			else:
				tasks.append((url, path, session, f"{i + 1}/{tmp['num_fragments']}"))

		with ThreadPoolExecutor(CONFIG['threads']) as pool:
			pool.map(get_fragment, tasks)

	return tmp['status']

def remove_fragments(fragments):
	"""
	Remove fragment files.

	Parameters
	----------
	fragments : list of str
		Fragment file paths.
	"""
	if CONFIG['auto']:
		remove = "y"
	else:
		remove = input(":: Remove all the fragment files? [y/N] ")
		if remove.strip() not in ["y", "Y", "n", "N"]:
			remove = "n"

	if remove in "yY":
		print(":: Removing fragment files...")
		for fragment in fragments:
			os.remove(fragment)
		os.rmdir(tmp['fragments_path'])

def merge_fragments():
	"""
	Merge video fragments in a single video file.

	"""
	if os.path.exists(tmp['output']):
		if CONFIG['auto']:
			merge = "y"
			print(f":: Replacing existing file {tmp['output']}...")
		else:
			merge = input(f":: Replace the existing file {tmp['output']}? [y/N] ")
			if merge.strip() not in ["y", "Y", "n", "N"]:
				merge = "n"
	else:
		merge = "y"
		print(":: Merging video fragments in a single file...")

	if merge in "yY":
		with open(tmp['output'], "wb") as video:
			fragments = []
			for i in range(tmp['num_fragments']):
				if not os.path.exists(tmp['fragment_file'] % i):
					print(f" File {tmp['fragment_file'] % i} doesn't exist")
					break

				print(" [%d/%d] Merging fragment %s..."
					% (i + 1, tmp['num_fragments'], tmp['fragment_file'] % i))
				fragments.append(tmp['fragment_file'] % i)
				with open(tmp['fragment_file'] % i, "rb") as file:
					video.write(file.read())

	remove_fragments(fragments)
