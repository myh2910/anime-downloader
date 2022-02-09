"""
Extract and write video fragments and subtitles.

"""
import os
import requests

from .config import CONFIG
from .utils import DOMAINS, sanitize_filename

def write_subtitle(code, title, subtitle):
	"""
	Write subtitle file.

	Parameters
	==========
	code : str
		Pigplayer video code.
	title : str or None
		Video title.
	subtitle : str
		Subtitle path.
	"""
	ext = os.path.splitext(subtitle)[1]
	if title:
		title = sanitize_filename(title)
		filename = os.path.join(code, f"{title}{ext}")
	else:
		filename = os.path.join(code, f"{CONFIG['quality']}{ext}")

	if os.path.exists(filename):
		print(f"File {filename} already exists.")
		return

	subtitle_url = f"https://pigplayer.com/{subtitle}"
	print(f"Extracting {subtitle_url}...")
	res = requests.get(subtitle_url)

	if res.status_code == 200:
		with open(filename, "wb") as file:
			file.write(res.content)
	elif res.status_code == 404:
		print("[Error] 404 Not Found.")
	else:
		print(f"[Error] Unknown status code {res.status_code}.")

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
	if CONFIG['quality'] == "best":
		CONFIG['quality'] = "1080p"
		url = f"/cdn/down/{code}/{CONFIG['quality']}/{CONFIG['quality']}"
		fragment_url = DOMAINS[num_domain][start % 10] \
			+ f"{url}{start}.{CONFIG['exts'][0]}"
		res = requests.get(fragment_url)
		if res.status_code != 200:
			CONFIG['quality'] = "720p"

	dirname = os.path.join(code, CONFIG['quality'])
	if not os.path.exists(dirname):
		os.makedirs(dirname)

	url = f"/cdn/down/{code}/{CONFIG['quality']}/{CONFIG['quality']}"
	num_fragment = start
	success = True

	while True:
		filename = os.path.join(dirname, f"{num_fragment}.{CONFIG['exts'][0]}")
		if os.path.exists(filename):
			print(f"File {filename} already exists.")
			num_fragment += 1
			continue

		fragment_url = DOMAINS[num_domain][num_fragment % 10] \
			+ f"{url}{num_fragment}.{CONFIG['exts'][0]}"
		print(f"Extracting {fragment_url}...")
		res = requests.get(fragment_url)

		if res.status_code == 200:
			with open(filename, "wb") as file:
				file.write(res.content)
			num_fragment += 1
		elif res.status_code == 404:
			print("[Error] 404 Not Found.")
			if num_fragment == start:
				success = False
			break
		else:
			print(f"[Error] Unknown status code {res.status_code}.")
			success = False
			break

	return success

def merge_fragments(code, title, start):
	"""
	Merge video fragments in a single video file.

	Parameters
	==========
	code : str
		Pigplayer video code.
	title : str or None
		Video title.
	start : int
		Initial fragment index.
	"""
	if title:
		title = sanitize_filename(title)
		outfile = os.path.join(code, f"{title}.{CONFIG['exts'][1]}")
	else:
		outfile = os.path.join(code, f"{CONFIG['quality']}.{CONFIG['exts'][1]}")

	if os.path.exists(outfile):
		print(f"Replacing existing file {outfile}...")

	with open(outfile, "wb") as outdir:
		fragment_num = start
		fragments = []

		dirname = os.path.join(code, CONFIG['quality'])
		while True:
			filename = os.path.join(dirname, f"{fragment_num}.{CONFIG['exts'][0]}")
			if os.path.exists(filename):
				print(f"File {filename} found.")
				fragments.append(filename)
				with open(filename, "rb") as file:
					outdir.write(file.read())
				fragment_num += 1
			else:
				break

	if CONFIG['auto']:
		remove = "y"
	else:
		remove = input("Would you remove all the fragment files? [y/N] ")
		if remove.strip() not in ["y", "Y", "n", "N"]:
			remove = "n"

	if remove in "yY":
		for filename in fragments:
			os.remove(filename)
		os.rmdir(dirname)
