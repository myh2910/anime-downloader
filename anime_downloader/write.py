import os
from concurrent.futures import ThreadPoolExecutor

import requests

from . import get
from .config import CONFIG

tmp = {}


def write_video(param, prop, title=None):
    """Initialize module.

    Args:
        param (str): Parameter value.
        prop (str): "name" if it is the exact name of an anime chapter, "source"
        if it is the link of the video player.
        title (str or None): Title of the corresponding video.
    """
    match prop:
        case "name":
            source, title = get.get_anime_data(f"{CONFIG['server']}/e/{param}")[0]
        case "source":
            source = param
        case _:
            print(f":: Unknown value: {prop}.")
            return

    if not title:
        print(f":: Title not found for {source}.")
        return

    title = "".join("_" if char in '\\/:*?"<>|' else char for char in title)

    tmp["path"] = os.path.join(CONFIG["home"], title)
    tmp["output"] = os.path.join(tmp["path"], f"{title}.{CONFIG['ext']}")

    if not os.path.exists(tmp["output"]):
        if not os.path.exists(tmp["path"]):
            os.makedirs(tmp["path"])

    if write_fragments(source):
        merge_fragments()

    write_subtitle(source, title)


def write_file(url, path, session=requests, err_format="%s"):
    """Download file by the given URL.

    Args:
        url (str): Link of the file.
        path (str): Path in which the file will be downloaded.
        session (requests): A requests instance.
        err_format (str): Text format to be displayed in case of an error.

    Returns:
        bool: True in case of success. False otherwise.
    """
    _err = ""
    max_repeat = CONFIG["repeat"]

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
    tmp["status"] = False

    return False


def write_subtitle(source, title):
    """Download subtitle file by the given URL.

    Args:
        source (str): Link of the video player.
        title (str): Title of the corresponding video.
    """
    print(":: Extracting subtitle file...")

    if url := get.get_subtitle_url(source):
        path = os.path.join(tmp["path"], f"{title}{os.path.splitext(url)[1]}")
        if os.path.exists(path):
            print(f" File {path} already exists.")
        else:
            print(f" Connecting to {url}...")
            write_file(url, path)
    else:
        print(" Subtitle file does not exist.")


def write_fragment(task):
    fragment, path, session, idx = task
    print(f" [{idx}] Connecting to {fragment}...")
    return write_file(fragment, path, session, f" [{idx}] %s")


def write_fragments(source):
    """Download video fragments by the given URL.

    Args:
        source (str): Link of the video player.

    Returns:
        bool: True in case of success. False otherwise.
    """
    print(f":: Extracting video fragments from {source}...")
    if os.path.exists(tmp["output"]):
        print(f" File {tmp['output']} already exists.")
        return False

    video_source = get.get_video_source(source)
    quality, fragments_url = get.get_fragments_url(source, video_source)
    print(f" {len(fragments_url)} fragments found.")

    tmp["fragments_path"] = os.path.join(tmp["path"], quality)
    if not os.path.exists(tmp["fragments_path"]):
        os.makedirs(tmp["fragments_path"])

    tmp["num_fragments"] = len(fragments_url)
    tmp["fragment_file"] = os.path.join(tmp["fragments_path"], "%d.ts")
    tmp["status"] = True

    with requests.Session() as session:
        tasks = []
        for i in range(tmp["num_fragments"]):
            url = fragments_url[i]
            path = tmp["fragment_file"] % i

            if os.path.exists(path):
                print(f" File {path} already exists.")
            else:
                tasks.append((url, path, session, f"{i + 1}/{tmp['num_fragments']}"))

        with ThreadPoolExecutor(CONFIG["threads"]) as pool:
            pool.map(write_fragment, tasks)

    return tmp["status"]


def remove_fragments(fragments):
    """Remove the given fragment files.

    Args:
        fragments (list of str): Paths of the fragment files.
    """
    if CONFIG["auto"]:
        remove = "y"
    else:
        remove = input(":: Remove all the fragment files? [y/N] ")
        if remove.strip() not in ["y", "Y", "n", "N"]:
            remove = "n"

    if remove in "yY":
        print(":: Removing fragment files...")
        for fragment in fragments:
            os.remove(fragment)
        os.rmdir(tmp["fragments_path"])


def merge_fragments():
    if os.path.exists(tmp["output"]):
        if CONFIG["auto"]:
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
        with open(tmp["output"], "wb") as video:
            fragments = []
            for i in range(tmp["num_fragments"]):
                if not os.path.exists(tmp["fragment_file"] % i):
                    print(f" File {tmp['fragment_file'] % i} doesn't exist")
                    break

                print(
                    " [%d/%d] Merging fragment %s..."
                    % (i + 1, tmp["num_fragments"], tmp["fragment_file"] % i)
                )
                fragments.append(tmp["fragment_file"] % i)
                with open(tmp["fragment_file"] % i, "rb") as file:
                    video.write(file.read())

        remove_fragments(fragments)
