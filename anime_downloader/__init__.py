"""
anime-downloader
================
Download animes with subtitles from https://ohli24.net/ and
https://pigplayer.com.

"""
from timeit import default_timer

from . import write
from .config import CONFIG
from .get import get_anime_data, get_chapters_data

__version__ = "2.1.0"
__author__ = "Yohan Min"

def download_chapter(param, prop="name", title=None, start=0, **kwargs):
	"""
	Download anime chapter and show the elapsed time.

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
		write.merge_fragments(quality, start)
	write.write_subtitle(source, title)

	elapsed_time += default_timer()
	print(f":: Elapsed time: {elapsed_time:0.2f}")

def download_chapters(*args, **kwargs):
	"""
	Download anime chapters.

	Parameters
	----------
	args : tuple of str
		Names of anime chapters
	"""
	for key, value in kwargs.items():
		CONFIG[key] = value

	elapsed_time = -default_timer()

	data = get_anime_data(f"https://ohli24.net/e/{name}" for name in args)
	for source, title in data:
		new_title = write.__init__(source, "source", title)[1]
		status, quality = write.write_fragments(source)
		if status:
			write.merge_fragments(quality)
		write.write_subtitle(source, new_title)

	elapsed_time += default_timer()
	print(f":: Elapsed time: {elapsed_time:0.2f}")

def download_anime(param, prop="name", **kwargs):
	"""
	Download anime.

	Parameters
	----------
	param : str
		Parameter value.
	prop : str, optional
		Parameter type, between "name", "id" and "search".
	"""
	for key, value in kwargs.items():
		CONFIG[key] = value

	elapsed_time = -default_timer()

	if data := get_chapters_data(param, prop):
		for source, title in data:
			new_title = write.__init__(source, "source", title)[1]
			status, quality = write.write_fragments(source)
			if status:
				write.merge_fragments(quality)
			write.write_subtitle(source, new_title)

	elapsed_time += default_timer()
	print(f":: Elapsed time: {elapsed_time:0.2f}")
