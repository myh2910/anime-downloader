"""
Write video and subtitle file.

"""
import os

from . import get
from .config import CONFIG

tmp = {}

def sanitize_filename(filename):
	"""
	Sanitize filename.

	Parameters
	----------
	filename : str
		Possibly invalid filename.

	Returns
	-------
	str
		Converted filename.
	"""
	return "".join("_" if char in "\\/:*?\"<>|" else char for char in filename)

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

	title = sanitize_filename(title)
	player_id = get.get_id_from_source(source)

	tmp['dir'] = os.path.join(CONFIG['home'], f"{title}-{player_id}")
	tmp['out'] = os.path.join(tmp['dir'], f"{title}{CONFIG['ext']}")

	if not os.path.exists(tmp['out']):
		if not os.path.exists(tmp['dir']):
			os.makedirs(tmp['dir'])

	return source, title

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
	url = get.get_subtitle_url(source)
	ext = os.path.splitext(url)[1]
	path = os.path.join(tmp['dir'], f"{title}{ext}")

	print(":: Extracting subtitle file...")
	if os.path.exists(path):
		print(f" File {path} already exists.")
	else:
		get.get_subtitle_file(url, path)

def write_fragments(source, start=0):
	"""
	Download video fragments.

	Parameters
	----------
	source : str
		Player source.
	start : int, optional
		Initial fragment index.

	Returns
	-------
	tuple of bool and None
		Indicates whether the process was successful or not.
	"""
	print(f":: Extracting video fragments from {source}...")
	if os.path.exists(tmp['out']):
		print(f" File {tmp['out']} already exists.")
		return False, None

	video_source = get.get_video_source(source)
	quality, fragments_url = get.get_fragments_url(source, video_source)
	print(f" {len(fragments_url)} fragments found.")

	dirname = os.path.join(tmp['dir'], quality)
	if not os.path.exists(dirname):
		os.makedirs(dirname)

	for idx in range(start, len(fragments_url)):
		url = fragments_url[idx]
		ext = os.path.splitext(url)[1]
		path = os.path.join(dirname, f"{idx}{ext}")

		if os.path.exists(path):
			print(f" File {path} already exists.")
		else:
			get.get_fragment_file(url, path)

	return True, quality

def remove_fragments(fragments, dirname):
	"""
	Remove fragment files.

	Parameters
	----------
	fragments : list of str
		Fragment file paths.
	dirname : str
		Folder name where the fragment files are saved.
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
		os.rmdir(dirname)

def merge_fragments(quality, start=0, ext="aaa"):
	"""
	Merge video fragments in a single video file.

	Parameters
	----------
	quality : str
		Fragment files resolution.
	start : int, optional
		Initial fragment index.
	ext : str, optional
		Fragment files extension.
	"""
	if os.path.exists(tmp['out']):
		if CONFIG['auto']:
			merge = "y"
			print(f":: Replacing existing file {tmp['out']}...")
		else:
			merge = input(f":: Replace the existing file {tmp['out']}? [y/N] ")
			if merge.strip() not in ["y", "Y", "n", "N"]:
				merge = "n"
	else:
		merge = "y"
		print(":: Merging video fragments in a single file...")

	if merge in "yY":
		with open(tmp['out'], "wb") as file:
			dirname = os.path.join(tmp['dir'], quality)
			idx = start
			fragments = []

			while True:
				fragment = os.path.join(dirname, f"{idx}.{ext}")
				if not os.path.exists(fragment):
					break

				print(f" Merging file {fragment}...")
				fragments.append(fragment)
				with open(fragment, "rb") as fragment_file:
					file.write(fragment_file.read())
				idx += 1

	remove_fragments(fragments, dirname)
