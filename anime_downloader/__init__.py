from timeit import default_timer

from .config import CONFIG
from .get import get_anime_data, get_chapters_data
from .write import write_video

__author__ = "Yohan Min"
__version__ = "2.3.2"


class Timer:
    def start(self):
        self.elapsed_time = -default_timer()

    def end(self):
        self.elapsed_time += default_timer()
        print(f":: Elapsed time: {self.elapsed_time:0.2f} seconds.")


def download_chapter(param, prop="name", title=None, **kwargs):
    """Download an anime chapter.

    Args:
        param (str): Parameter value.
        prop (str): "name" if it is the exact name of an anime chapter, "source"
        if it is the link of the video player.
        title (str or None): Title of the corresponding video.
    """
    for key, value in kwargs.items():
        CONFIG[key] = value

    timer = Timer()
    timer.start()

    write_video(param, prop, title)

    timer.end()


def download_chapters(*args, **kwargs):
    """Download multiple anime chapters.

    Args:
        *args (str): Names of the anime chapters.
        **kwargs: Additional arguments.
    """
    if not args:
        return

    for key, value in kwargs.items():
        CONFIG[key] = value

    timer = Timer()
    timer.start()

    for source, title in get_anime_data(
        *(f"{CONFIG['server']}/e/{name}" for name in args)
    ):
        write_video(source, "source", title)

    timer.end()


def download_anime(param, prop="name", **kwargs):
    """Download all available chapters from an anime.

    Args:
        param (str): Parameter value.
        prop (str): "name" if it is the exact name of an anime, "search" if the
        search function should be used.
        **kwargs: Additional arguments.
    """
    for key, value in kwargs.items():
        CONFIG[key] = value

    timer = Timer()
    timer.start()

    if data := get_chapters_data(param, prop):
        for source, title in data:
            write_video(source, "source", title)

    timer.end()
