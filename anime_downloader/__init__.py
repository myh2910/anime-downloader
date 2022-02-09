"""
anime-downloader
================
Download animes with subtitles from https://ohli24.net/ and
https://pigplayer.xyz.

"""
from timeit import default_timer

from .config import CONFIG
from . import get

__version__ = "1.2.0"
__author__ = "Yohan Min"

def download(
	code,
	title=None,
	subtitle=None,
	num_domain=0,
	start=0,
	**kwargs
):
	"""
	Download video and show the elapsed time.

	Parameters
	==========
	code : str
		Pigplayer video code.
	title : str or None, optional
		Video title.
	subtitle : str or None, optional
		Subtitle path.
	num_domain : int, optional
	start : int, optional
		Initial fragment index.
	"""
	for key, value in kwargs.items():
		CONFIG[key] = value

	elapsed_time = -default_timer()
	if get.write_fragments(code, num_domain, start):
		get.merge_fragments(code, title, start)
	if subtitle:
		get.write_subtitle(code, title, subtitle)
	elapsed_time += default_timer()

	print(f"Elapsed time: {elapsed_time:0.2f}")
