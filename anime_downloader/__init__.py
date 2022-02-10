"""
anime-downloader
================
Download animes with subtitles from https://ohli24.net/ and
https://pigplayer.com.

"""
from timeit import default_timer

from .config import CONFIG
from . import write

__version__ = "2.0.0"
__author__ = "Yohan Min"

def download(param, prop="name", title=None, start=0, **kwargs):
	"""
	Download video and show the elapsed time.

	Parameters
	----------
	param : str
		Parameter value.
	prop : str, optional
		Parameter type, between "name", "id" and "source".
	title : str or None, optional
		Video title.
	start : int, optional
		Initial fragment index.
	"""
	for key, value in kwargs.items():
		CONFIG[key] = value

	elapsed_time = -default_timer()
	source, title = write.__init__(param, prop, title)
	status, quality = write.write_fragments(source, start)
	if status:
		write.merge_fragments(start, quality)
	write.write_subtitle(source, title)
	elapsed_time += default_timer()

	print(f":: Elapsed time: {elapsed_time:0.2f}")
