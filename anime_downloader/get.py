"""
Extract and write video fragments and subtitles.

"""
import os
import requests

from .config import CONFIG
from .utils import DOMAINS

def write_subtitle(subtitle):
	"""
	Write subtitle file.

	Parameters
	==========
	subtitle : str
		Subtitle path.
	"""
	ext = os.path.splitext(subtitle)[1]
	filename = os.path.join(CONFIG['dirname'], f"{CONFIG['filename']}{ext}")

	print(":: Extracting subtitle file...")
	if os.path.exists(filename):
		print(f" File {filename} already exists.")
		return

	subtitle_url = f"https://pigplayer.com/{subtitle}"
	print(f" Connecting to {subtitle_url}...")
	res = requests.get(subtitle_url)

	if res.status_code == 200:
		with open(filename, "wb") as file:
			file.write(res.content)
	elif res.status_code == 404:
		print(" [Error] 404 Not Found.")
	else:
		print(f" [Error] Unknown status code: {res.status_code}")

def write_fragments(code, num_domain, start):
	"""
	Download video fragments.

	Parameters
	==========
	code : str
		Pigplayer video code.
	num_domain : int
	start : int
		Initial fragment index.

	Returns
	=======
	success : bool
		Indicates whether the download process was succesful or not.
	"""
	outfile = os.path.join(
		CONFIG['dirname'],
		f"{CONFIG['filename']}.{CONFIG['exts'][1]}"
	)

	print(":: Extracting video fragments...")
	if os.path.exists(outfile):
		print(f" File {outfile} already exists.")
		return False

	if CONFIG['quality'] == "best":
		CONFIG['quality'] = "1080p"
		url = f"/cdn/down/{code}/{CONFIG['quality']}/{CONFIG['quality']}"
		fragment_url = DOMAINS[num_domain][start % 10] \
			+ f"{url}{start}.{CONFIG['exts'][0]}"
		res = requests.get(fragment_url)
		if res.status_code != 200:
			CONFIG['quality'] = "720p"

	dirname = os.path.join(CONFIG['dirname'], CONFIG['quality'])
	if not os.path.exists(dirname):
		os.makedirs(dirname)

	url = f"/cdn/down/{code}/{CONFIG['quality']}/{CONFIG['quality']}"
	num_fragment = start
	success = True

	while True:
		fragment = os.path.join(dirname, f"{num_fragment}.{CONFIG['exts'][0]}")
		if os.path.exists(fragment):
			print(f" File {fragment} already exists.")
			num_fragment += 1
			continue

		fragment_url = DOMAINS[num_domain][num_fragment % 10] \
			+ f"{url}{num_fragment}.{CONFIG['exts'][0]}"
		print(f" Connecting to {fragment_url}...")
		res = requests.get(fragment_url)

		if res.status_code == 200:
			with open(fragment, "wb") as fragment_file:
				fragment_file.write(res.content)
			num_fragment += 1
			continue

		if res.status_code != 404:
			print(f" [Error] Unknown status code: {res.status_code}")
			return False

		print(" [Error] 404 Not Found.")
		if num_fragment == start:
			return False
		break

	return success

def remove_fragments(fragments, dirname):
	"""
	Remove fragment files.

	Parameters
	==========
	fragments : list of str
		Fragment file paths.
	dirname : str
		Folder name.
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

def merge_fragments(start):
	"""
	Merge video fragments in a single video file.

	Parameters
	==========
	start : int
		Initial fragment index.
	"""
	outfile = os.path.join(
		CONFIG['dirname'],
		f"{CONFIG['filename']}.{CONFIG['exts'][1]}"
	)

	if os.path.exists(outfile):
		if CONFIG['auto']:
			merge = "y"
			print(f":: Replacing existing file {outfile}...")
		else:
			merge = input(f":: Replace the existing file {outfile}? [y/N] ")
			if merge.strip() not in ["y", "Y", "n", "N"]:
				merge = "n"
	else:
		merge = "y"
		print(":: Merging video fragments in a single file...")

	if merge in "yY":
		with open(outfile, "wb") as file:
			dirname = os.path.join(CONFIG['dirname'], CONFIG['quality'])
			fragment_num = start
			fragments = []

			while True:
				fragment = os.path.join(dirname, f"{fragment_num}.{CONFIG['exts'][0]}")
				if not os.path.exists(fragment):
					break

				print(f" Merging file {fragment}...")
				fragments.append(fragment)
				with open(fragment, "rb") as fragment_file:
					file.write(fragment_file.read())
				fragment_num += 1

	remove_fragments(fragments, dirname)
