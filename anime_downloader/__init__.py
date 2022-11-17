"""
anime-downloader
================

Download animes with Korean subtitles from OHLI24.

WARNING: OHLI24 is an illegal anime streaming site from Korea. I am not
responsible for any legal issues or damages regarding to this.

"""
from timeit import default_timer

from . import write
from .config import CONFIG
from .get import get_anime_data, get_chapters_data

__author__ = "Yohan Min"
__version__ = "2.3.1"

class Timer:
	def start(self):
		self.elapsed_time = -default_timer()

	def end(self):
		self.elapsed_time += default_timer()
		print(f":: Elapsed time: {self.elapsed_time:0.2f} seconds")

def download_video(source, title):
	if write.write_fragments(source):
		write.merge_fragments()
	write.write_subtitle(source, title)

def download_chapter(param, prop="name", title=None, **kwargs):
	"""
	Download an anime chapter.

	Parameters
	----------
	param : str
		Parameter value.
	prop : str, optional
		Parameter type, between "name", "source" and "id".
	title : str or None, optional
		Video title.
	"""
	for key, value in kwargs.items():
		CONFIG[key] = value

	timer = Timer()
	timer.start()

	download_video(*write.__init__(param, prop, title))

	timer.end()

def download_chapters(*args, **kwargs):
	"""
	Download multiple anime chapters.

	Parameters
	----------
	args : tuple of str
		Names of anime chapters
	"""
	if not args:
		return

	for key, value in kwargs.items():
		CONFIG[key] = value

	timer = Timer()
	timer.start()

	for source, title in get_anime_data(*(
		f"https://ohli24.net/e/{name}" for name in args)):
		download_video(source, write.__init__(source, "source", title)[1])

	timer.end()

def download_anime(param, prop="name", **kwargs):
	"""
	Download all available chapters from an anime.

	Parameters
	----------
	param : str
		Parameter value.
	prop : str, optional
		Parameter type, between "name", "id" and "search".
	"""
	for key, value in kwargs.items():
		CONFIG[key] = value

	timer = Timer()
	timer.start()

	if data := get_chapters_data(param, prop):
		for source, title in data:
			download_video(source,
				write.__init__(source, "source", title)[1])

	timer.end()
