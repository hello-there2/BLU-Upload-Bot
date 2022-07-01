#!/usr/bin/python3.8

# Imports and requirements
import pkg_resources

pkg_resources.require("IMDbPY>=2021.4.18")
import argparse
import re
import shutil
import sys, datetime
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from sys import platform
from glob import glob
import ffmpeg
import requests
import tmdbsimple as tmdb
from imdb import IMDb
import torf
from guessit import guessit
from pymediainfo import MediaInfo as pymediainfo
import os
import time
import editdistance
import pybase64
import configparser
from unidecode import unidecode
import pykakasi
from shutil import copy
import imp
import qbittorrentapi
import constants, helpers
from classes import ProgressBar, SmartFormatter
import html

# Currently the easiest way of saving this.
is_hddvd = False

# Config specific variables
# Default
imghost, TMDB_API_KEY, image_width, image_height, num_screens = (
    None,
    None,
    None,
    None,
    None,
)
# Paths
ffmpeg_bin, chtor_bin, rtxmlrpc_bin, BDINFO_PATH, WATCH_FOLDER = (
    None,
    None,
    None,
    None,
    None,
)
# PTP info
ptpApiUser, ptpApiKey = None, None
# BLU info
BASE_API_ENDPOINT, API_TOKEN, torrent_source, torrent_announce = None, None, None, None
# Image Hosts
UNIT3D_IMAGE = None

# PTP
ptpApiUser, ptpApiKey = None, None
# HDB
hdbUsername, hdbPasskey, hdbPassword = None, None, None
# Client specific
qbtClient, torrent_binary = None, None

# Initiate the argument parser

parser = argparse.ArgumentParser(
    description="Upload torrents to UNIT3D based trackers through its API",
    formatter_class=SmartFormatter,
)
parser.add_argument("-V", "--version", help="show program version", action="store_true")

parser.add_argument(
    "file_list",
    type=str,
    metavar="release-path",
    nargs="+",
    help="file or directory containing the release",
)

parser.add_argument(
    "--anonymous",
    dest="anonymous",
    default=False,
    action="store_true",
    help="Upload as anonymous",
)

parser.add_argument(
    "--sd", dest="sd", default=False, action="store_true", help="Upload is SD"
)

parser.add_argument(
    "--internal",
    dest="internal",
    default=False,
    action="store_true",
    help="Upload is Internal",
)

parser.add_argument(
    "--streamop",
    dest="stream",
    default="AUTO-DETECT",
    action="store_const",
    const="1",
    help="Upload is Stream Optimized",
)

parser.add_argument(
    "--description",
    dest="description",
    default="",
    type=str,
    help="Torrent description",
)

parser.add_argument("--name", dest="name", default=None, type=str, help="Torrent name")

parser.add_argument(
    "--category",
    dest="category_id",
    default="AUTO-DETECT",
    type=str,
    help="R|Upload category, name or ID work.\n" "Movie\t|TV\t|Fanres\n" "1\t|2\t|3",
)

parser.add_argument(
    "--type",
    dest="type_id",
    default="AUTO-DETECT",
    type=str,
    help="R|Upload type, name or ID work.\n"
    "Disc\t|Remux\t|Encode\t|WEB-DL\t|WEBRip\t|HDTV\n"
    "1\t|3\t|12\t|4\t|5\t|6\n",
)

parser.add_argument(
    "--tmdb", dest="tmdb", default="AUTO-DETECT", type=str, help="TheMovieDb ID"
)

parser.add_argument(
    "--tvdb", dest="tvdb", default="AUTO-DETECT", type=str, help="TVDb ID"
)

parser.add_argument(
    "--imdb", dest="imdb", default="AUTO-DETECT", type=str, help="IMDb ID"
)

parser.add_argument("--mal", dest="mal", default="0", type=str, help="MAL ID")

parser.add_argument("--igdb", dest="igdb", default="0", type=str, help="IGDB ID")

parser.add_argument(
    "--overwrite-existing-torrent",
    dest="overwrite",
    default=False,
    action="store_true",
    help="overwrite-existing-torrent",
)

parser.add_argument(
    "--use-torrent",
    dest="use_torrent",
    default=None,
    type=str,
    help="Specify a torrent file to use instead of creating a new one.",
)

parser.add_argument(
    "--featured",
    dest="featured",
    default=False,
    action="store_true",
    help="Upload is Featured",
)

parser.add_argument(
    "--free",
    dest="free",
    default=False,
    action="store_true",
    help="Upload is Freeleech",
)

parser.add_argument(
    "--doubleup",
    dest="doubleup",
    default=False,
    action="store_true",
    help="Upload is Double Upload",
)

parser.add_argument(
    "--sticky",
    dest="sticky",
    default=False,
    action="store_true",
    help="Upload is Stickied",
)

parser.add_argument(
    "--group", dest="group", default=None, type=str, help="Override group detection"
)

parser.add_argument(
    "--nogroup",
    dest="nogroup",
    default=False,
    action="store_true",
    help="Remove Detected group",
)

parser.add_argument(
    "--audio",
    dest="audio",
    default=None,
    type=str,
    help='Audio base codec, e.x. "TrueHD", "Atmos" defaults to "TrueHD Atmos".  Requires the use of --channels',
)

parser.add_argument(
    "--channels",
    dest="channels",
    default=None,
    type=str,
    help='Audio channels, e.x. "5.1".  Can be used without --audio, but is suggested to be used with',
)

parser.add_argument("--video", dest="video", default=None, type=str, help="Video codec")

parser.add_argument(
    "--dynamic-range",
    dest="dynamic_range",
    default=None,
    type=str,
    help='Dynamic range, "DV HDR", "HDR10+", "HDR", "SDR", or others.',
)

parser.add_argument(
    "--resolution",
    dest="resolution",
    default=None,
    type=str,
    help="Resolution, needs to be one of the following: 8640p, 4320p, 2160p, 1080p, 1080i, 720p, 576p, 576i, 480p, 480i, or Other",
)

parser.add_argument(
    "--cut",
    dest="cut",
    default=None,
    type=str,
    help='The cut of the movie/show, e.x. "Director\'s Cut", passing an empty string "" will remove any cut detected',
)

parser.add_argument(
    "--edition",
    dest="edition",
    default=None,
    type=str,
    help='The edition, e.x. "Remastered"',
)

parser.add_argument(
    "--web-source",
    dest="web",
    default=None,
    type=str,
    help="The source of the WEB release.  i.e. AMZN, Amazon, etc.",
)

parser.add_argument(
    "--region",
    dest="region",
    default=None,
    type=str,
    help='The region (only applicable for full discs), e.x. "GBR"',
)

parser.add_argument(
    "--repack",
    dest="repack",
    default=None,
    type=int,
    help="Repack number, 0 is none (removes it if detected), 1 is REPACK, 2 is REPACK2, etc.",
)

parser.add_argument(
    "--proper",
    dest="proper",
    default=None,
    type=int,
    help="Proper number, 0 is none, 1 is PROPER, 2 is PROPER2, etc.",
)

parser.add_argument(
    "--rerip",
    dest="rerip",
    default=None,
    type=int,
    help="RERIP number, 0 is none, 1 is RERIP, 2 is RERIP2, etc.",
)

parser.add_argument(
    "--hybrid",
    dest="hybrid",
    default=False,
    action="store_true",
    help="When passed it is considered a Hybrid",
)

parser.add_argument(
    "--episode-title",
    dest="episode_title",
    default=None,
    type=str,
    help="When passed on a TV show it adds the Episode title, 1 is to add the one the parser found, anything else will used what is passed.",
)

parser.add_argument(
    "--ptp",
    dest="ptp",
    default=None,
    type=str,
    help="""Requires your PTP ApiUser and ApiKey to be set.  Pass the PTP torrent ID to grab their bbcode.  *** (Not yet implemented)
pass "auto" for automatic detection, which can be set in the config file too.  Pass a torrent ID to match that one directly.""",
)

parser.add_argument(
    "--hdb",
    dest="hdb",
    default=None,
    type=str,
    help="""Requires your HDB credentials to be set.  Passkey is suggested, as you can use 2fa with it, if both are set passkey is used.
pass "auto" for automatic detection, which can be set in the config file too.  Pass a torrent ID to match that one directly.""",
)

parser.add_argument(
    "--allow-no-imdb",
    dest="allow_no_imdb",
    default=False,
    action="store_true",
    help="When passed it will auto upload with IMDb 0 instead of erroring out in auto mode.",
)

parser.add_argument(
    "--allow-no-tmdb",
    dest="allow_no_tmdb",
    default=False,
    action="store_true",
    help="When passed it will auto upload with TMDb 0 instead of erroring out in auto mode.",
)

parser.add_argument(
    "--skip-dupe-check",
    dest="skip_dupe_check",
    default=False,
    action="store_true",
    help=f"When passed it will skip dupe checking abort.\nThe check is still done, just not aborted.",
)

parser.add_argument(
    "--config",
    dest="config_path",
    default=constants.CONFIG_PATH,
    type=str,
    help=f"Config file path, used for when not in default location {constants.CONFIG_PATH}",
)

parser.add_argument(
    "--debug",
    dest="debug",
    default=False,
    action="store_true",
    help="When passed it will run like normally, but not fully upload.",
)

parser.add_argument(
    "--keywords",
    dest="keywords",
    default=None,
    type=str,
    help="Comma separated list of keywords.",
)

parser.add_argument(
    "--append-keywords",
    dest="append_keywords",
    default=False,
    action="store_true",
    help="When passed it will append thhe keywords given to the list from TMDb, default is overrite them.",
)

parser.add_argument(
    "--tracker",
    dest="tracker",
    default="BLU",
    type=str,
    help="Change which tracker to upload to.",
)

parser.add_argument(
    "--client",
    dest="client",
    default="DEFAULT",
    type=str,
    help="Specify which client you are using, default is rTorrent for Linux and Watch Folder for Windows.",
)

parser.add_argument(
    "--nfo",
    dest="nfo",
    default=None,
    type=str,
    help="The path to the nfo file.  If not passed it will search for one.",
)

parser.add_argument(
    "--personal",
    dest="personal",
    default=False,
    action="store_true",
    help='When passed it will mark this release as a "Personal Release"',
)

parser.add_argument(
    "--screens",
    dest="screens",
    default=None,
    type=int,
    help="Specify how many screens to take.  Overrides the screens number in the config.",
)

parser.add_argument(
    "--screen-kill",
    dest="MAX_WAIT",
    default=-1,
    type=int,
    help=f"Number used for the max to wait on ffmpeg to take a screen, in seconds.  Default {constants.MAX_WAIT} seconds.",
)

parser.add_argument(
    "--season",
    dest="season",
    default=None,
    type=int,
    help="Season number, values less than 0 mean remove it.",
)

parser.add_argument(
    "--episode",
    dest="episode",
    default=None,
    type=int,
    help="Episode number, values less than 0 mean remove it.",
)

# read arguments from the command line
args = parser.parse_args()
# read config file
config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
assert Path(args.config_path).exists()
config.read(args.config_path)

# Used for uploading to other trackers mostly
api_files_data = {}


# Define functions


def uprint(x):
    try:
        __builtins__.print(x)
    except:
        __builtins__.print(str(x).encode("ascii", "xmlcharrefreplace").decode("ascii"))


# Override the oritinal print function.
# Some had issues with unicode.  Will encode non-ascii as xml format.
print = uprint


def ascii_check(string):
    try:
        return string.isascii()
    except:
        pass
    try:
        string.encode("ascii")
        return True
    except:
        return False


def read_defaults():
    global imghost, TMDB_API_KEY, num_screens, image_width, image_height, BDINFO_PATH, WATCH_FOLDER
    global ffmpeg_bin, chtor_bin, rtxmlrpc_bin
    global BASE_API_ENDPOINT, API_TOKEN, torrent_source, torrent_announce
    global ptpApiUser, ptpApiKey
    global hdbUsername, hdbPasskey, hdbPassword
    global qbtClient, qBitArguments
    # Defaults
    imghost = config["DEFAULT"].get("image host").lower()
    TMDB_API_KEY = config["DEFAULT"].get("tmdb api")
    if args.screens is not None and args.screens >= 0:
        num_screens = args.screens
    else:
        num_screens = config["DEFAULT"].get("num screens", "8")
    num_screens = int(num_screens)
    if num_screens < 0:
        num_screens = 0
    if args.MAX_WAIT == -1:
        args.MAX_WAIT = config["DEFAULT"].getint("screen kill", constants.MAX_WAIT)
    image_width = config["DEFAULT"].getint("image width", constants.IMAGE_WIDTH)
    image_height = config["DEFAULT"].getint("image height", image_width)
    if not args.allow_no_imdb:
        args.allow_no_imdb = config["DEFAULT"].getboolean(
            "allow no imdb", fallback=False
        )
    if not args.allow_no_tmdb:
        args.allow_no_tmdb = config["DEFAULT"].getboolean(
            "allow no tmdb", fallback=False
        )

    # Paths
    ffmpeg_bin = config["Paths"].get("ffmpeg")
    chtor_bin = config["Paths"].get("chtor", None)
    rtxmlrpc_bin = config["Paths"].get("rtxmlrpc", None)
    BDINFO_PATH = config["Paths"].get("bdinfo", None)
    WATCH_FOLDER = config["Paths"].get("watch", None)

    # Clients
    if args.client == "DEFAULT":
        args.client = config["DEFAULT"].get("client", args.client)
        if args.client == "DEFAULT":
            # Client was still default
            # Set default client for configs without one and no argument was passed.
            args.client = "watch" if helpers.is_windows() else "rtorrent"

    if "rtorrent" in args.client.lower() or "rutorrent" in args.client.lower():
        args.client = "rtorrent"
        WATCH_FOLDER = None
        if helpers.is_windows() or chtor_bin is None or rtxmlrpc_bin is None:
            if args.debug:
                print(
                    "rTorrent client specified, no valid setup detected or is Windows..."
                )
                print(f"Debug mode enabled... Continuing...\n")
            else:
                raise RuntimeError(
                    "rTorrent client specified, no valid setup detected or is Windows..."
                )
    elif "qbit" in args.client.lower():
        # Default values set are the qBit defaults, this way default setups don't need to specify anything or only changed ones.
        args.client = "qbit"
        if "qBittorrent" in config.sections():
            qBitHost = config["qBittorrent"].get("url", "localhost")
            qBitPort = config["qBittorrent"].get("port", "8080")
            qbitUsername = config["qBittorrent"].get("username", "admin")
            qBitPassword = config["qBittorrent"].get("password", "adminadmin")
            # Arguments follow as described in official documentation
            # https://github.com/qbittorrent/qBittorrent/wiki
            # https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#add-new-torrent
            qBitArguments = {
                "category": config["qBittorrent"].get("category", ""),
                "tags": config["qBittorrent"].get("tags", ""),
                "skip_checking": config["qBittorrent"].getboolean(
                    "skip_checking", True
                ),
                "paused": config["qBittorrent"].getboolean("paused", False),
                "upLimit": config["qBittorrent"].getint("upLimit", -1),
                "dlLimit": config["qBittorrent"].getint("dlLimit", -1),
                "ratioLimit": config["qBittorrent"].getfloat("ratioLimit", -1),
                "seedingTimeLimit": config["qBittorrent"].getint(
                    "seedingTimeLimit", -1
                ),
            }
        else:
            qBitHost, qBitPort, qbitUsername, qBitPassword = (
                "localhost",
                "8080",
                "admin",
                "adminadmin",
            )
        qbtClient = qbittorrentapi.Client(
            host=qBitHost, port=qBitPort, username=qbitUsername, password=qBitPassword
        )
        try:
            qbtClient.auth_log_in()
        except qbittorrentapi.LoginFailed:
            error_string = "Invalid login credientials provided to qBittorrent..."
            error_string = f"{error_string}\n{qBitHost}:{qBitPort}\t\tUsername:{qbitUsername}\tPassword{qBitPassword}"
            if args.debug:
                print(f"{error_string}\nDebug mode enabled... Continuing...\n")
            else:
                raise RuntimeError(error_string)
    elif "watch" in args.client.lower():
        args.client = "watch"
        chtor_bin = None
        rtxmlrpc_bin = None
        if not WATCH_FOLDER:
            if args.debug:
                print(
                    f"No watch folder provided... Debug mode enabled... Continuing...\n"
                )
            else:
                raise RuntimeError("No watch folder provided...")

    # Tracker Specific
    use_tracker = str(args.tracker).upper().strip()
    if use_tracker not in config.sections():
        sys.exit(
            f"The tracker secion was not included... check for the [{use_tracker}] section in the config file."
        )
    BASE_API_ENDPOINT = config[use_tracker].get("api endpoint", None)
    API_TOKEN = config[use_tracker].get("api key", "0")
    torrent_source = config[use_tracker].get("torrent source", "BLU")
    torrent_announce = [config[use_tracker].get("announce", "")]

    # PTP API Credentials
    if "PTP" in config.sections():
        ptpApiUser = config["PTP"].get("api user", None)
        ptpApiKey = config["PTP"].get("api key", None)
        try:
            if config["PTP"].getboolean("auto", fallback=False) and args.ptp == None:
                args.ptp = "auto"
        except:
            pass
    # HDB API Credentials
    if "HDB" in config.sections():
        hdbUsername = config["HDB"].get("Username", None)
        hdbPasskey = config["HDB"].get(
            "Passkey", None
        )  # Better method.  2fa avail here.
        hdbPassword = config["HDB"].get(
            "Password", None
        )  # Works, but should use passkey.  2fa not avail here.
        try:
            if config["HDB"].getboolean("auto", fallback=False) and args.hdb == None:
                args.hdb = "auto"
        except:
            pass


def qbittorrent(path, torrent):
    global qbtClient, qBitArguments
    response = qbtClient.torrents_add(
        torrent_files=torrent,
        save_path=path,
        use_auto_torrent_management=False,
        is_skip_checking=qBitArguments["skip_checking"],
        is_paused=qBitArguments["paused"],
        category=qBitArguments["category"],
        tags=qBitArguments["tags"],
        seeding_time_limit=qBitArguments["seedingTimeLimit"],
        ratio_limit=qBitArguments["ratioLimit"],
        upload_limit=qBitArguments["upLimit"],
        download_limit=qBitArguments["dlLimit"],
    )
    print(f'\nSending torrent to qBit returned: "{response}"')


def get_ptp_bbcode():
    base_url = "https://passthepopcorn.me/torrents.php"
    bbcode = None
    ptp_id = str(args.ptp)

    if args.ptp == None:
        return None

    if ptpApiUser == "" or ptpApiUser == "ApiUser":
        print(
            "No PTP ApiUser set, verify both the ApiUser and ApiKey are set correctly... No bbcode is returned..."
        )
        return None
    if ptpApiKey == "" or ptpApiKey == "ApiKey":
        print(
            "No PTP ApiKey set, verify both the ApiUser and ApiKey are set correctly... No bbcode is returned..."
        )
        return None

    headers = {
        "ApiUser": ptpApiUser,
        "ApiKey": ptpApiKey,
        "User-Agent": "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11",
    }

    if "AUTO" in str(args.ptp).upper():
        base_auto_url = "https://passthepopcorn.me/torrents.php"
        auto_params = {
            "json": "noredirect",
            "grouping": "0",
            "filelist": Path(args.file_list[0]).name,
        }
        r = requests.get(url=base_auto_url, headers=headers, params=auto_params)
        try:
            results = r.json()
        except:
            print("Checking ptp failed... No bbcode is being returned...")
            return None
        if results.get("TotalResults") == "0":
            print("Auto PTP match failed, no bbcode from there will be copied...")
            return None
        elif results.get("TotalResults") == "1":
            movies = results.get("Movies")
            movie_torrent = movies[0].get("Torrents")
            ptp_id = movie_torrent[0]
            ptp_id = str(ptp_id.get("Id"))
        else:
            print("Auto PTP match failed, no bbcode from there will be copied...")
            print("Reason: More than one result returned from auto matching.")
            return None

    ptp_params = {"action": "get_description", "id": ptp_id}
    r = requests.get(url=base_url, headers=headers, params=ptp_params)
    bbcode = r.text
    if bbcode == "Unauthorized.":
        raise RuntimeError("Invalid PTP Api Credentials...")
    if bbcode == "" or bbcode == None:
        print("PTP Torrent ID not found... No bbcode is being used.")
        bbcode = None
    return bbcode


def get_ptp_imdb():
    ptp_id = -1
    base_url = "https://passthepopcorn.me/torrents.php"
    if ptpApiUser == "" or ptpApiUser == "ApiUser":
        print("ApiUser not set for PTP... Not auto detecting IMDb from PTP...")
        return None, None
    if ptpApiKey == "" or ptpApiKey == "ApiKey":
        print("ApiKey not set for PTP... Not auto detecting IMDb from PTP...")
        return None, None

    headers = {
        "ApiUser": ptpApiUser,
        "ApiKey": ptpApiKey,
        "User-Agent": "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11",
    }
    auto_params = {
        "json": "noredirect",
        "grouping": "0",
        "filelist": Path(args.file_list[0]).name,
    }
    r = requests.get(url=base_url, headers=headers, params=auto_params)
    try:
        results = r.json()
    except:
        print("Failed to parse ptp response... No IMDb will be used...")
        return None, None
    if results.get("TotalResults") == "0":
        print("Auto PTP match failed, no IMDb from there will be copied...")
        ptp_imdb = None
    elif results.get("TotalResults") == "1":
        movies = results.get("Movies")[0]
        ptp_imdb = "tt" + movies["ImdbId"]
        print(f"Using IMDb '{ptp_imdb}' from PTP")
        ptp_imdb = ptp_imdb
        ptp_id = movies.get("Torrents", [{"Id": -1}])[0]["Id"]
    else:
        print("Auto PTP match failed, no bbcode from there will be copied...")
        print("Reason: More than one result returned from auto matching.")
        ptp_imdb = None
    return ptp_imdb, ptp_id


def get_hdb_info(path, search="file", title=None, tryNext=True):
    url = "https://hdbits.org/api/torrents"
    header = {"Content-Type": "application/json"}
    params = {"username": hdbUsername, "include_dead": "true", "limit": 100, "page": 0}
    if not hdbPasskey:
        params["password"] = hdbPassword
    else:
        params["passkey"] = hdbPasskey
    # Returns IMDb, TVDb, Type, Region, English Title, Year
    # IMDb may return it with missing 0's.
    # Region is for full discs, type will be the type as defined below, but WEB Encode is WEBRip
    filename = path  # Have this here so I can
    is_bluray = False
    hdb_imdb, hdb_tvdb, hdb_type, hdb_region, hdb_title, hdb_category = (
        None,
        None,
        None,
        None,
        None,
        None,
    )
    hdb_data = None

    if hdbUsername is None or (hdbPasskey is None and hdbPassword is None):
        print(
            f"\nHDB Username is required to search HDB...\nAdditionally you must set the Passkey or Password..."
        )
        print(
            "Passkey is recommended, as 2fa can be enabled.  Using the password requires 2fa be disabled...\n"
        )
        return None

    hdb_status_codes = {
        0: "Success",
        1: "Failure (something bad happened)",
        2: "SSL Required - You should be on https://",
        3: "JSON malformed",
        4: "Auth data missing",
        5: "Auth failed (incorrect username / password)",
        6: "Missing required parameters",
        7: "Invalid parameter",
        8: "IMDb - Import fail",
        9: "IMDb - TV not allowed",
    }
    hdb_type_medium = {
        1: "Blu-ray/HD DVD",
        3: "Encode",  # Also used for WEB-DLs
        4: "Capture",  # (U)HDTV Capture
        5: "Remux",
        6: "WEB-DL",
    }
    hdb_type_category = {
        1: "Movie",
        2: "TV",
        3: "Documentary",
        4: "Music",
        5: "Sport",
        6: "Audio",
        7: "XXX",
        8: "Misc/Demo",
    }

    if search.lower() == "file":
        if Path(path).is_file():
            filename = path
        else:
            # Folder was given
            bdinfo_files, dvd_file, HDDVD_files = disc_info(path)
            is_bluray = bdinfo_files != []

            if is_bluray:
                # Full Blu-ray
                meta_folder = os.path.join(bdinfo_files[0], "META", "DL")
                try:
                    filename = next(iter(Path(meta_folder).glob("*.jpg")))
                except:
                    print(
                        f'Blu-ray does not have a jpg in the "META/DL" folder or is missing the "META/DL" folder.'
                    )
                    print("HDB searching not possible...")
                    return hdb_data
            else:
                # Use first file
                filename = next(iter(sorted(Path(path).glob("*/")))).as_posix()
        # Here for when searching it doesn't send '', a folder sends the folder name,
        # which currently gets no results, but is a valid API call.
        if path.endswith("/"):
            path = path[:-1]
        print(f'Checking HDB for "{os.path.basename(filename)}"')
        params["file_in_torrent"] = os.path.basename(filename)
    elif search.lower() == "imdb":
        print("Attempting to search HDB via IMDb ID...")
        try:
            imdb_id = int(args.imdb.replace("tt", ""))
            params["imdb"] = {"id": imdb_id}
        except:
            if tryNext:
                print(
                    f"Invalid IMDb ID for HDB search: '{args.imdb}'... Checking with guessit info..."
                )
                return get_hdb_info(
                    path, search="search", title=guessit_info.get("title")
                )
            else:
                print("Invalid IMDb ID: '{args.imdb}'... ")
                return hdb_data
    elif search.lower() == "search":
        print("Attempting to search HDB via title search...")
        if title is not None and title != "":
            if tryNext:
                print("No title found for HDB search, using file method...")
                return get_hdb_info(
                    path, search="file", title=guessit_info.get("title")
                )
            else:
                print("No title found, using file method...")
                return hdb_data
        params["search"] = title
    else:
        print(
            f"Invalid search type for HDB... Expected 'file', 'guessit', or, 'imdb'... Got: {search}"
        )
        return None
    r = requests.post(url=url, headers=header, json=params)
    try:
        response = r.json()
    except:
        print("Failed to parse response from HDB, no data is being used...")
        return None
    previous_name = ""
    last_on_page_name = ""
    if response["status"] == 0:
        print("HDB API Call was Successful, checking for match...")
        response_data = response["data"]
        get_next_page = True
        print(f"Getting page: {params['page']}")
        while get_next_page:

            # Successful api search
            for d in response_data:
                d_size = d["size"]
                d_numfiles = d["numfiles"]
                d_name = d["name"]
                last_on_page_name = d_name
                d_type_category = hdb_type_category.get(d["type_category"])
                d_type = hdb_type_medium.get(d["type_medium"])
                # Get stuff from their IMDb
                try:
                    d_imdb = d["imdb"]
                except:
                    d_imdb = None
                # Get their TVDb if it exists
                try:
                    d_tvdb = d["tvdb"]
                except:
                    d_tvdb = None
                # Allow for 1 MiB and 1 file difference, just in case something like an nfo is missing.
                if (
                    abs(release_size - d_size) < 1049000
                    and abs(num_files - d_numfiles) < 2
                ):
                    # Found match
                    print(f'Matched: "{d_name}" ({sizeof_fmt(d_size)})\n')
                    hdb_imdb, hdb_tvdb = d_imdb, d_tvdb
                    hdb_type, hdb_region = d_type, None
                    hdb_title, hdb_category = d_name, d_type_category
                    get_next_page = False
                if d_name == previous_name:
                    get_next_page = False

            if get_next_page and len(response["data"]) == 100:
                params["page"] = params["page"] + 1
                print(f"Getting page: {params['page']}")
                r = requests.post(url=url, headers=header, json=params)
                response = r.json()
                if response["status"] == 0:
                    response_data = response["data"]
                else:
                    get_next_page = False
            else:
                get_next_page = False
            previous_name = last_on_page_name
    else:
        # Something went wrong with the API Call.
        # Print error, only for the invalid credentials using password is checked, done because 2fa needs passkey.
        print(
            f"HDB API failed... Status was \"{hdb_status_codes.get(response['status'])}\""
        )
        if response.get("message") is not None and response.get("message") != "":
            print(f"Message: \"{response.get('message')}\"")
        print(f"HDB data cannot be used...\n")
    if hdb_type == "Blu-ray/HD DVD":
        try:
            hdb_region = re.search(
                "([A-Z]{3})( Blu-ray)", hdb_title, flags=re.IGNORECASE
            ).group(1)
            if hdb_region == "UHD":
                hdb_region = re.search(
                    "([A-Z]{3})( UHD Blu-ray)", hdb_title, flags=re.IGNORECASE
                ).group(1)
            hdb_region = hdb_region.upper()
        except:
            # Try Except just for ones without a region.
            hdb_region = None
    # Change Encode type for WEBRips to report WEBRip
    if hdb_title is not None and hdb_type == "Encode" and "WEBRip" in hdb_title:
        hdb_type = "WEBRip"
    hdb_data = {
        "IMDb": hdb_imdb,
        "TVDb": hdb_tvdb,
        "type": hdb_type,
        "region": hdb_region,
        "title": hdb_title,
        "category": hdb_category,
    }
    if not hdb_data.get("title", None):
        print(
            f'HDB match failed using method: "{search}"... File: "{os.path.basename(filename)}"\n'
        )
        hdb_data = None
    # If the result is blank try the next method.
    if hdb_data == None and search == "imdb" and tryNext:
        hdb_data = get_hdb_info(path, search="search", title=guessit_info.get("title"))
    elif hdb_data == None and search == "guessit" and tryNext:
        hdb_data = get_hdb_info(path, search="file", title=guessit_info.get("title"))
    return hdb_data


def autodetect_streamop(info):
    global container, isstreamable
    args.stream = "0"
    # Full discs aren't streamable
    if args.type_id == constants.TYPES["Full Disc"]:
        return "0"
    vtrack = get_mediainfo_video(info)[0]
    atrack = get_mediainfo_audio(info)[0]
    for track in info.tracks:
        if track.track_type == "General":
            container = track.format
            isstreamable = track.isstreamable
        if (
            container == "MPEG-4"
            and (
                vtrack == "H.264"
                or vtrack == "H.265"
                or vtrack == "x264"
                or vtrack == "x265"
            )
            and atrack == "AAC"
            and isstreamable == "Yes"
        ):
            return "1"
        else:
            return "0"


def get_extension(info):
    if args.type_id == constants.TYPES["Full Disc"] and type(info) == list:
        return "m2ts"
    for track in info.tracks:
        if track.track_type == "General":
            return track.file_extension
    return ""


def autodetect_resolution_bdinfo(bdinfo):
    quick_summary = bdinfo[0]["summary"]
    bdinfo_lines = quick_summary.splitlines()

    for bdinfo_line in bdinfo_lines:
        scan_type = "progressive"
        if "Video:" in bdinfo_line:
            res = re.search("(.*)( \d{3,4}[ip])(.*)", bdinfo_line).group(2)
            res = res.strip()
            if res in ["2160p", "1080p", "1080i", "720p"]:
                args.sd = "0"
            else:
                args.sd = "1"
            if "i" in res:
                scan_type = "interlaced"
            res_category = res.replace(scan_type[0], "")

            if args.resolution is not None:
                res = args.resolution.lower()
                resolution_groups = re.match("(\d+)([ip])", res)
                res_category = int(resolution_groups.group(1))
                if resolution_groups.group(2) == "p":
                    scan_type = "progressive"
                else:
                    scan_type = "interlaced"
            return [res_category, scan_type, constants.RESOLUTIONS[res]]


def autodetect_resolution(info):
    global track, scan_type, height, width
    if args.type_id == constants.TYPES["Full Disc"] and type(info) == list:
        return autodetect_resolution_bdinfo(info)
    for track in info.tracks:
        if track.track_type == "Video":
            width = track.width
            height = track.height
            scan_type = track.scan_type
            # Exit out of finding track info when the first video track is found.
            break

    total_pixels = width * height
    if total_pixels < 600000:
        # SD
        args.sd = "1"
        if height == 480:
            res_category = 480
        elif height == 576:
            res_category = 576
        elif total_pixels > 430000:
            res_category = 576
        else:
            res_category = 480
    else:
        # HD
        args.sd = "0"
        if total_pixels > 70000000:
            res_category = 8640
        elif total_pixels > 13500000:
            res_category = 4320
        elif total_pixels > 3000000:
            res_category = 2160
        elif total_pixels > 960000:
            res_category = 1080
        else:
            res_category = 720

    # Detect interlaced content
    try:
        if "MBAFF" in scan_type or "Interlaced" in scan_type:
            scan_type = "interlaced"
        else:
            scan_type = "progressive"
    except:
        scan_type = "progressive"
    if scan_type == "interlaced" and res_category >= 720 and "25.0" in track.frame_rate:
        scan_type = "progressive"
    res = f"{res_category}{scan_type[0].lower()}"
    if args.resolution is not None:
        res = args.resolution.lower()
        resolution_groups = re.match("(\d+)([ip])", res)
        res_category = int(resolution_groups.group(1))
        if resolution_groups.group(2) == "p":
            scan_type = "progressive"
        else:
            scan_type = "interlaced"
    return [res_category, scan_type, constants.RESOLUTIONS[res]]


def get_mediainfo_audio_bdinfo(bdinfo):
    quick_summary = bdinfo[0]["summary"]
    bdinfo_lines = quick_summary.splitlines()

    for bdinfo_line in bdinfo_lines:
        scan_type = "p"
        if "Audio:" in bdinfo_line:
            # Only uses first audio channel
            if "Dolby Digital" in bdinfo_line:
                audio_format = "DD"
            elif "TrueHD" in bdinfo_line:
                audio_format = "TrueHD"
            elif "DTS:X" in bdinfo_line:
                audio_format = "DTS:X"
            elif "DTS-HD Master Audio" in bdinfo_line:
                audio_format = "DTS-HD MA"
            elif "DTS" in bdinfo_line and "High" in bdinfo_line:
                audio_format = "DTS-HD HRA"
            elif "DTS" in bdinfo_line and "EX" in bdinfo_line:
                audio_format = "DTS-EX"
            elif "DTS" in bdinfo_line:
                audio_format = "DTS"
            elif "LPCM" in bdinfo_line:
                audio_format = "LPCM"
            elif "PCM" in bdinfo_line:
                audio_format = "PCM"
            if "Atmos" in bdinfo_line:
                audio_format = f"{audio_format} Atmos"
            audio_channels = re.search(
                "(.*/)( \d\.\d-?E?X?S?)( )(.*)", bdinfo_line
            ).group(2)
            audio_channels = audio_channels.strip()

            if args.audio is not None and args.channels is not None:
                # Setting audio codec requires also setting the channels
                audio_format = args.audio
                if audio_format == "Atmos":
                    audio_format = "TrueHD Atmos"
            if args.channels is not None:
                # Setting the channels can be done by itself, but suggested to do both.
                audio_channels = args.channels
            return [audio_format, audio_channels]


def get_mediainfo_audio(info):
    if args.type_id == constants.TYPES["Full Disc"] and type(info) == list:
        return get_mediainfo_audio_bdinfo(info)
    for track in info.tracks:
        if track.track_type == "Audio":
            if track.other_format is not None:
                audio_format = track.other_format[0]  # Better format name
            else:
                audio_format = track.format  # fallback if other_format is missing.
            audio_channels = track.channel_s
            if track.channel_s__original is not None and "Object" not in str(
                track.channel_s__original
            ):
                audio_channels = track.channel_s__original
            audio_layout = track.channel_layout
            if track.channelpositions_original is not None:
                # Get layout, DTS-ES uses channelpositions_original instead of channel_layout
                # others might too.
                audio_layout = track.channelpositions_original
            elif track.channel_positions is not None and track.channel_layout is None:
                # Get layout, Opus uses channel_positions instead of channel_layout
                # others might too.
                audio_layout = track.channel_positions
            audio_compression = track.compression_mode
            if track.other_commercial_name is not None:
                audio_commercial_name = (
                    track.other_commercial_name
                )  # Better commercial name
            else:
                audio_commercial_name = (
                    track.commercial_name
                )  # Fallback commercial name

            if audio_commercial_name is not None:
                # Not all codecs will have a commercial name
                audio_commercial_name = audio_commercial_name[0]
            # Format detection
            if "MLP" in audio_format:
                audio_format = "TrueHD"
            elif "DTS" in audio_format and audio_format.endswith(" X"):
                audio_format = "DTS:X"
            elif "DTS" in audio_format and "Lossless" in audio_compression:
                audio_format = "DTS-HD MA"
            elif "DTS" in audio_format and "High" in audio_commercial_name:
                audio_format = "DTS-HD HRA"
            elif "DTS" in audio_format and "ES" in audio_commercial_name:
                audio_format = "DTS-ES"
            elif "E-AC-3" in audio_format:
                audio_format = "DD+"
            elif "AC-3" in audio_format:
                audio_format = "DD"
            elif "MPEG" in audio_format:  # MPEG can be 1-3
                if "3" in track.format_profile:
                    audio_format = "MP3"  # Likely the only one we will see
                elif "2" in track.format_profile:  # Others are just in case.
                    audio_format = "MP2"
                else:
                    audio_format = "MP1"
            elif "AAC" in audio_format:
                audio_format = "AAC"

            # Atmos detection
            if audio_commercial_name is not None and "Atmos" in audio_commercial_name:
                audio_format = audio_format + " Atmos"

            # Channel detection
            if (
                audio_layout is None
                and "DTS:X" in audio_format
                or "Atmos" in audio_format
            ):
                if audio_channels is not None and audio_channels == 6:
                    audio_channels = "5.1"
                else:
                    audio_channels = "7.1"
                # DTS:X and Atmos might not have a layout, default to 7.1/5.1
            elif audio_layout is not None and "Object" in audio_layout:
                if audio_channels is not None and audio_channels == 6:
                    audio_channels = "5.1"
                else:
                    audio_channels = "7.1"
                # Object based codecs might have "Object Based" as their layout
            elif audio_layout is not None and "LFE" in audio_layout:
                audio_channels = str(audio_channels - 1) + ".1"
            else:
                audio_channels = str(audio_channels) + ".0"
            # Override arguments, not putting it above just so if new bugs are found.
            if args.audio is not None and args.channels is not None:
                # Setting audio codec requires also setting the channels
                audio_format = args.audio
                if audio_format == "Atmos":
                    audio_format = "TrueHD Atmos"
            if args.channels is not None:
                # Setting the channels can be done by itself, but suggested to do both.
                audio_channels = args.channels
            if "DD" in audio_format:
                if track.format_settings and "EX" in track.format_settings:
                    audio_channels = re.sub(r"(\d\.\d)", r"\g<1>-EX", audio_channels)
            return [audio_format, audio_channels]


def get_mediainfo_text(path, info):
    if args.type_id == constants.TYPES["Full Disc"] and type(info) == list:
        return ""
    if Path(path).is_dir():
        _, first_media_file = single_file_folder(path)
        path = first_media_file
    return pymediainfo.parse(path, output="", full=False).replace(
        str(Path(path).parent) + "/", ""
    )


def get_3d_bdinfo(bdinfo):
    quick_summary = bdinfo[0]["summary"]
    bdinfo_lines = quick_summary.splitlines()
    check_next = True
    video_track = 0
    left_eye, right_eye = False, False

    for bdinfo_line in bdinfo_lines:
        if "Video:" in bdinfo_line:
            video_track += 1
            if "Multiview" in bdinfo_line:
                return "3D"
            elif "Left Eye" in bdinfo_line:
                left_eye = True
            elif "Right Eye" in bdinfo_line:
                right_eye = True
        elif video_track != 0:
            # Require left and right due to PiP will both use left.
            if left_eye and right_eye:
                return "3D"
            else:
                break
    return None


def get_3d_filename(filename):
    type_3d = None
    if re.search("Half.?OU", filename, flags=re.IGNORECASE):
        type_3d = "Half OU"
    elif re.search("3D.?SBS", filename, flags=re.IGNORECASE):
        type_3d = "Half OU"
    elif re.search(".HOU.", filename, flags=re.IGNORECASE):
        type_3d = "Half OU"
    elif re.search("Half.?SBS", filename, flags=re.IGNORECASE):
        type_3d = "Half SBS"
    elif re.search("3D.?SBS", filename, flags=re.IGNORECASE):
        type_3d = "Half SBS"
    elif re.search(".HSBS.", filename, flags=re.IGNORECASE):
        type_3d = "Half SBS"
    return type_3d


def get_3d_mediainfo(info, filename="", other_3d=False):
    if args.type_id == constants.TYPES["Full Disc"] and type(info) == list:
        has_ssif = False
        for bdinfo in media_info:
            if has_ssif:
                break
            has_ssif = bdinfo_contains_ssif(bdinfo["main"])
        return get_3d_bdinfo(info) or has_ssif
    type_3d = None
    is_3d = False
    for track in info.tracks:
        if track.track_type == "Video":
            if track.multiview_count:
                is_3d = True
                break
    type_3d_filename = get_3d_filename(filename)
    if is_3d and other_3d and type_3d_filename:
        # Case mediainfo says 3D, but better option found in filename.
        type_3d = type_3d_filename
    elif is_3d:
        type_3d = "3D"
    elif other_3d and type_3d_filename:
        type_3d = type_3d_filename
    return type_3d


def get_bdinfo_video(bdinfo):
    quick_summary = bdinfo[0]["summary"]
    bdinfo_lines = quick_summary.splitlines()
    dynamic_range = None
    check_next = True
    video_track = 0
    for bdinfo_line in bdinfo_lines:
        if not check_next:
            break
        if "Video:" in bdinfo_line:
            video_track += 1
            if "HDR10+" in bdinfo_line:
                dynamic_range = "HDR10+"
            elif "HDR10" in bdinfo_line:
                dynamic_range = "HDR"
            elif "BT.2020" in bdinfo_line and dynamic_range is None:
                # "Standard" HDR, no HDR10 metadata.  Cannot have Dolby Vision.
                dynamic_range = "PQ10"
                check_next = False
            if "Dolby Vision" in bdinfo_line:
                dynamic_range = "DV " + dynamic_range if dynamic_range else "DV HDR"
                check_next = False
            if video_track == 1:
                # Only check first video stream
                if "AVC" in bdinfo_line:
                    format = "AVC"
                elif "HEVC" in bdinfo_line:
                    format = "HEVC"
                elif "VC-1" in bdinfo_line:
                    format = "VC-1"
                elif "MPEG-2" in bdinfo_line:
                    format = "MPEG-2"
                else:
                    # Just in case those fail above, catch remaining.
                    format = re.search("(.*Video: )(.*)( Video.*)", bdinfo_line).group(
                        2
                    )
                    format = format.strip()
            else:
                # Don't check next video track, doby vision check already done.
                # Here so ones with a PiP won't
                check_next = False

    if args.video is not None:
        format = args.video
    if args.dynamic_range is not None:
        dynamic_range = ""
        if "hdr" in args.dynamic_range.lower():
            dynamic_range = "HDR"
        if "dovi" in args.dynamic_range.lower():
            dynamic_range += "DV"
        if dynamic_range == "":
            dynamic_range = args.dynamic_range
    if dynamic_range == "SDR":
        dynamic_range = None
    return format, dynamic_range


def get_mediainfo_video(info):
    global dynamic_range, format
    # Default is assume SDR
    v_sdr, v_hdr10, v_hdr10p, v_dv, v_pq10, v_hlg, v_wcg = (
        True,
        False,
        False,
        False,
        False,
        False,
        False,
    )

    if args.type_id == constants.TYPES["Full Disc"] and type(info) == list:
        return get_bdinfo_video(info)
    video_tracks = info.video_tracks
    main_video_track = video_tracks[0]
    if main_video_track.format is not None:
        if "AVC" in main_video_track.format:
            format = "H.264"
        elif "HEVC" in main_video_track.format:
            format = "H.265"
        elif "VP9" in main_video_track.format:
            format = "VP9"
        elif "MPEG" in main_video_track.format:
            try:
                if "2" in main_video_track.codec_id:
                    format = "MPEG-2"
                else:
                    format = "MPEG-1"
            except:
                format = "MPEG-2"
        else:
            format = main_video_track.format
    if main_video_track.encoded_library_name is not None:
        if "x265" in main_video_track.encoded_library_name:
            format = "x265"
        elif "x264" in main_video_track.encoded_library_name:
            format = "x264"
    if format in ["x264", "AVC"] and main_video_track.bit_depth == 10:
        format = f"Hi10P {format}"
    for vtrack in video_tracks:
        if vtrack.other_hdr_format is not None:
            if any("HDR10" in hdr_format for hdr_format in vtrack.other_hdr_format):
                v_hdr10 = True or v_hdr10
                v_sdr = False
            if any("HDR10+" in hdr_format for hdr_format in vtrack.other_hdr_format):
                v_hdr10p = True or v_hdr10p
                v_hdr10 = True or v_hdr10
                v_sdr = False
            # Dolby Vision
            if any("dvhe.04" in hdr_format for hdr_format in vtrack.other_hdr_format):
                # Profile 4 is SDR
                v_dv = True
                v_sdr = True
            elif any("dvhe.05" in hdr_format for hdr_format in vtrack.other_hdr_format):
                # Profile 5 is legacy WEB
                v_dv = True or v_dv
                v_sdr = False
            elif any("dvhe.07" in hdr_format for hdr_format in vtrack.other_hdr_format):
                # Profile 7 is Blu-ray, must be on some HDR base
                v_dv = True or v_dv
                v_sdr = False
                v_hdr10 = True or v_hdr10
            elif any("dvhe.08" in hdr_format for hdr_format in vtrack.other_hdr_format):
                # Profile 8 is Blu-ray encodes or new WEB, can be SDR
                v_dv = True or v_dv
            elif any("dvav.09" in hdr_format for hdr_format in vtrack.other_hdr_format):
                # Profile 9 is AVC, likely never going to be used, can be SDR
                v_dv = True or v_dv
                v_sdr = False
        # HLG/WCG detection.  These are only found in transfer charactistics.
        if vtrack.transfer_characteristics is not None:
            if "HLG" in vtrack.transfer_characteristics:
                v_hlg = True or v_hlg
            if "BT.2020 (10-bit)" in vtrack.transfer_characteristics:
                v_wcg = True or v_wcg
                v_sdr = False
            if "PQ" in vtrack.transfer_characteristics:
                v_pq10 = True
                v_sdr = False
        if vtrack.transfer_characteristics_original is not None:
            if "HLG" in vtrack.transfer_characteristics_original:
                v_hlg = True or v_hlg
                v_sdr = False
            if "BT.2020 (10-bit)" in vtrack.transfer_characteristics_original:
                v_wcg = True or v_wcg
                v_sdr = False
            if "PQ" in vtrack.transfer_characteristics_original:
                v_pq10 = True
                v_sdr = False
    dynamic_range = "SDR" if v_sdr else ""
    dynamic_range = "HLG" if v_hlg else dynamic_range
    dynamic_range = "HDR10+" if v_hdr10p else dynamic_range
    dynamic_range = "HDR" if v_hdr10 and not v_hdr10p else dynamic_range
    dynamic_range = "PQ10" if v_pq10 and not any([v_hdr10p, v_hdr10]) else dynamic_range
    dynamic_range = (
        "WCG"
        if v_wcg and not any([v_hlg, v_hdr10p, v_hdr10, v_pq10])
        else dynamic_range
    )
    dynamic_range = f"DV {dynamic_range}".strip() if v_dv else dynamic_range
    if args.video is not None:
        format = args.video
    if args.dynamic_range is not None:
        dynamic_range = ""
        if "hdr" in args.dynamic_range.lower():
            dynamic_range = "HDR"
        if "dovi" in args.dynamic_range.lower():
            dynamic_range += "DV"
        if dynamic_range == "":
            dynamic_range = args.dynamic_range
    if dynamic_range == "SDR":
        dynamic_range = None
    return format, dynamic_range


def get_mediainfo_duration(info):
    global total_sec
    if type(info) == list:
        return sum(
            get_mediainfo_duration(pymediainfo.parse(m2ts)) for m2ts in m2ts_files
        )
    # Do try except, use the video duration if it has it, otherwise use general.
    try:
        for track in info.tracks:
            if track.track_type == "Video":
                ms = track.duration  # Track time in millisecondes
                total_sec = round(float(ms)) / 1000  # Convert to seconds
                break
    except:
        for track in info.tracks:
            if track.track_type == "General":
                ms = track.duration  # Track time in millisecondes
                total_sec = round(float(ms)) / 1000  # Convert to seconds
                break
    return float(total_sec)


def get_m2ts_files(bdinfo):
    bdinfo_lines = bdinfo.splitlines()
    m2ts_files = []
    for bdinfo_line in bdinfo_lines:
        m2ts_regex = re.match(
            "^(\d+.M2TS)(\s+\d:\d{2}:\d{2}.\d{3}\s+)(\d:\d{2}:\d{2}.\d{3})",
            bdinfo_line,
            flags=re.IGNORECASE,
        )
        if m2ts_regex:
            m2ts_file = m2ts_regex.group(1)
            m2ts_dur = m2ts_regex.group(3)
            m2ts_files += [{"m2ts": m2ts_file, "duration": m2ts_dur}]
    return m2ts_files


def bdinfo_contains_ssif(bdinfo):
    bdinfo_lines = bdinfo.splitlines()
    for bdinfo_line in bdinfo_lines:
        ssif_regex = re.match(
            "^(\d+.SSIF)(\s+\d:\d{2}:\d{2}.\d{3}\s+)(\d:\d{2}:\d{2}.\d{3})",
            bdinfo_line,
            flags=re.IGNORECASE,
        )
        if ssif_regex:
            return True
    return False


def get_bdinfo_name(bdinfo):
    title_regex, label_regex = None, None
    bdinfo_lines = bdinfo.splitlines()
    for bdinfo_line in bdinfo_lines:
        if not title_regex:
            title_regex = re.match(
                "^(Disc Title: )(.*)", bdinfo_line, flags=re.IGNORECASE
            )
        if not label_regex:
            label_regex = re.match(
                "^(Disc Label: )(.*)", bdinfo_line, flags=re.IGNORECASE
            )
        if label_regex:
            break
    bdinfo_name = (
        label_regex.group(2)
        if label_regex
        else title_regex.group(2)
        if title_regex
        else None
    )
    return bdinfo_name


def get_bdinfo_type(bdinfo):
    size_regex, bdinfo_resolution, bdinfo_size, bdinfo_type = None, None, None, None
    bdinfo_lines = bdinfo.splitlines()
    for bdinfo_line in bdinfo_lines:
        if not size_regex:
            size_regex = re.match(
                "^(Size: )(.*)( bytes)", bdinfo_line, flags=re.IGNORECASE
            )
        if size_regex:
            bdinfo_size = size_regex.group(2)
            break
    bdinfo_size = int(bdinfo_size.replace(",", "").replace(".", ""))
    if bdinfo_size <= 24996709663:
        bdinfo_type = "BD25"
    elif bdinfo_size <= 50004156744:
        bdinfo_type = "BD50"
    elif bdinfo_size <= 66002909922:
        bdinfo_type = "BD66"
    elif bdinfo_size <= 99997576070:
        bdinfo_type = "BD100"
    else:
        bdinfo_type = "BD000"
    return bdinfo_type


def time_to_sec(time):
    split_duration = time.split(":")
    # Convert to seconds
    if len(split_duration) == 3:
        hours = int(split_duration[0]) * 3600
        minutes = int(split_duration[1]) * 60
        seconds = float(split_duration[2])
    elif len(split_duration) == 2:
        # No Hours, just in case
        hours = 0
        minutes = int(split_duration[0]) * 60
        seconds = float(split_duration[1])
    duration = hours + minutes + seconds
    return duration


def cumilative_sum(lst):
    total, result = 0, []
    for ele in lst:
        total += ele
        result.append(total)
    return result


def get_mediainfo_ids(info):
    media_tmdb, media_imdb, media_tvdb = None, None, None

    if args.type_id == constants.TYPES["Full Disc"] and type(info) is list:
        return media_tmdb, media_imdb, media_tvdb

    for track in info.tracks:
        if track.track_type == "General":
            try:
                media_tmdb = track.tmdb.split("/")[1]
                if (
                    "AUTO-DETECT" in args.category_id
                    and track.tmdb.split("/")[0] == "movie"
                ):
                    args.category_id = constants.CATEGORIES["Movie"]
                else:
                    args.category_id = constants.CATEGORIES["TV"]
            except:
                pass
            try:
                media_imdb = track.imdb
            except:
                pass
            try:
                pass
            except:
                media_tvdb = track.tvdb
            return media_tmdb, media_imdb, media_tvdb


def correct_dar(info):
    for track in info.tracks:
        if track.track_type == "Video":
            if float(track.pixel_aspect_ratio) < 1:
                width = float(track.width)
                height = float(track.height)
                height = float(track.display_aspect_ratio) * height
                dar_correction = round(width / height, 3)
                return 1, dar_correction
            elif float(track.pixel_aspect_ratio) > 1:
                return track.pixel_aspect_ratio, 1
            else:
                return 1, 1


def take_screenshot(
    file, offset_secs, output_dir, frame_type=None, w_sar=None, h_sar=None
):
    global ffmpeg_bin
    # This is used to fix the DAR
    w_sar = "sar" if not w_sar else str(w_sar)
    h_sar = "1" if not h_sar else str(h_sar)
    # This noscale is needed for some files it gave black screen for instead.
    noscale = w_sar == "1" and h_sar == "1"
    pic_type = {"I": "PICT_TYPE_I", "P": "PICT_TYPE_P", "B": "PICT_TYPE_B"}
    screenshot_path = Path(output_dir) / (
        "{}_{}.png".format(Path(file).stem, offset_secs)
    )
    screenshot_path = Path(screenshot_path).as_posix()
    # Convert the offset secs to a human readable time, helpful for printing and in some cases taking screens
    offset = datetime.timedelta(seconds=offset_secs)
    if helpers.is_windows():
        # Windows seem to not like the ffmpeg library, using direct command instead.
        if ".exe" not in ffmpeg_bin:
            ffmpeg_bin = os.path.join(ffmpeg_bin, "ffmpeg.exe")
        ffmpeg_command = (
            f'{Path(ffmpeg_bin).as_posix()} -y -ss {offset} -i "{file}" -vframes 1'
        )
        if not noscale:
            ffmpeg_command = f"{ffmpeg_command} -vf scale=iw*{w_sar}:ih*{h_sar}"
        if frame_type:
            ffmpeg_command = (
                f'{ffmpeg_command} -vf "select=eq(pict_type\\,{pic_type[frame_type]})"'
            )
        ffmpeg_command = f'{ffmpeg_command} "{screenshot_path}"'
        ffmpeg_command_run = subprocess.Popen(
            ffmpeg_command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=False,
            shell=True,
        )
    else:
        ffmpeg_command = ffmpeg.input(str(file), ss=str(offset))
        if not noscale:
            ffmpeg_command = ffmpeg_command.filter(
                "scale", f"iw*{w_sar}", f"ih*{h_sar}"
            )
        if frame_type:
            ffmpeg_command = ffmpeg_command.filter(
                "select", f"eq(pict_type,{pic_type[frame_type]})"
            )
        ffmpeg_command = ffmpeg_command.output(str(screenshot_path), vframes=1)

        ffmpeg_command_run = ffmpeg_command.run_async(
            cmd=Path(ffmpeg_bin).as_posix(), quiet=True
        )

    print(f"{offset}\t{screenshot_path}")
    sleep_count = 0  # Here so we can wait for ffmpeg to make the file.
    MAX_WAIT = (
        args.MAX_WAIT * 10
    )  # Times 10 so we can sleep every 100ms instead of seconds.
    while not os.path.isfile(screenshot_path):
        # Check for file first, if it doesn't exist wait until it does or the timeout is reached
        if sleep_count == MAX_WAIT:
            print(
                f"\tFailed to take screenshot after {args.MAX_WAIT}s... killing ffmpeg command..."
            )
            print(
                f"\tThe above screenshot may not have been taken and might not upload...."
            )
            ffmpeg_command_run.terminate()
            outs, errs = ffmpeg_command_run.communicate()
            break
        else:
            sleep_count += 1
        time.sleep(0.1)
    try:
        ffmpeg_command_run.terminate()
        outs, errs = ffmpeg_command_run.communicate()
    except:
        pass
    return screenshot_path


def set_image_host(override=False):
    global UNIT3D_IMAGE, imghost, config
    if not UNIT3D_IMAGE or not override:
        image_module_dir = os.path.join(constants.SCRIPT_PATH, "UNIT3D_Image")
        import_file = None
        for entry in os.scandir(image_module_dir):
            if entry.path.lower() == f"{image_module_dir.lower()}/{imghost.lower()}.py":
                import_file = entry
                break
        module_name = Path(import_file.name).stem
        f, filename, module_description = imp.find_module(
            module_name, [image_module_dir]
        )
        module = imp.load_module(module_name, f, filename, module_description)
        section = ""
        for host in config.sections():
            if f"image_{imghost.lower()}" == host.lower():
                section = host
                break
        UNIT3D_IMAGE = module.ImageHost(
            config=config, section=section, debug=args.debug
        )


def upload_screenshots(path, num_screens, length_override=None):
    global UNIT3D_IMAGE
    if not UNIT3D_IMAGE:
        set_image_host()
    if Path(path).is_dir():
        path = next(iter(sorted(Path(path).glob("*/")))).as_posix()
    screenshot_files_pre = take_screenshots(
        path, num_screens, length_override=length_override
    )
    screenshot_files = []
    for screenshot_file in screenshot_files_pre:
        if os.path.isfile(screenshot_file):
            screenshot_files += [screenshot_file]
        else:
            print(f'Image not found... Removing file: "{screenshot_file}"')
    if screenshot_files == []:
        print(f"Failed taking screens for file: {os.path.basename(path)}")
    UNIT3D_IMAGE.upload_images(screenshot_files)


def take_screenshots(file, num_screens, frame_type=None, length_override=None):
    file_mediainfo = pymediainfo.parse(file)
    try:
        w_correction, h_correction = correct_dar(file_mediainfo)
    except:
        w_correction, h_correction = None, None
    if length_override:
        duration = length_override
    else:
        duration = float(int(get_mediainfo_duration(file_mediainfo)))
    output_dir = Path(tempfile.gettempdir()) / ("{}_screens".format(Path(file).name))
    if frame_type is None:
        v_codec, _ = get_mediainfo_video(file_mediainfo)
        if (
            v_codec == "VC-1" or v_codec in ["HEVC", "H.265", "x265"]
        ) and file.upper().endswith("M2TS"):
            # VC-1 m2ts files require I-Frames to be reliable for screens.
            frame_type = "I"
    if frame_type == "I":
        print("Warning... Taking screenshots of only I-Frames...")
    if output_dir.exists():
        shutil.rmtree(output_dir.resolve())
    Path.mkdir(output_dir)
    offsets = [
        int(1 / (int(num_screens) + 1) * o * duration)
        for o in range(1, int(num_screens) + 1)
    ]
    return [
        take_screenshot(
            file, offset, output_dir, frame_type, w_sar=w_correction, h_sar=h_correction
        )
        for offset in offsets
    ]


def get_external_ids(tmdb_data=None, imdb_data=None):
    if tmdb_data is None:
        raise RuntimeError("Getting the external IDs requires TMDb to be passed...")

    tmdb_id = tmdb_data.id
    imdb_id = tmdb_data.external_ids().get("imdb_id", "0")
    tvdb_id = tmdb_data.external_ids().get("tvdb_id", "0")

    if imdb_data is not None:
        # Use this IMDb over what TMDb had
        imdb_id = "tt{}".format(imdb_data.movieID)

    # Required in cases IMDb or TVDb is returned as nothing,
    # happens when no IMDb/TVDb isn't in the TMDb database, but should for that type.
    if imdb_id == "":
        imdb_id = "0"
    if tvdb_id == "":
        tvdb_id = "0"

    return tmdb_id, imdb_id, tvdb_id


def get_imdb_year(imdb_info):
    year = None
    try:
        year = int(imdb_info["year"])
    except:
        year = 9999
        # This way the year makes sort have ones with date first ascending order
    return year


def get_imdb_info(guessit_info=None, imdb_id=None):
    imdb_info = None
    if guessit_info is None and imdb_id is None:
        raise RuntimeError(
            "Gathering IMDb info requires either guessit or a valid IMDb ID..."
        )
    elif imdb_id is not None:
        # Using the IMDb ID passed
        if int(str(imdb_id).replace("tt", "")) != 0:
            # Check if tt000000 was passed, if so no IMDb exists.
            imdb_info = IMDb().get_movie(str(imdb_id).replace("tt", ""))
            if imdb_info.data == {}:
                imdb_info = None
    else:
        # Using guessit info
        search_results = IMDb().search_movie(guessit_info["title"])
        possible_imdb, edit_distances = [], []

        if len(search_results) == 0:
            raise RuntimeError(
                "Unable to identify IMDb ID, please specify one manually."
            )
        # Sort the results, ones without year are moved to the bottom.
        # This should help in the case two same names, but no year in filename.
        # You would grab the oldest one, which for TV wouldn't have the year
        search_results.sort(key=get_imdb_year)
        try:
            guesset_year = int(guessit_info.get("year"))
        except:
            guesset_year = None

        for result in search_results:
            try:
                if guessit_info.get("year") is not None:
                    guesset_year = int(guessit_info.get("year"))
                    if not (
                        guesset_year - 1 <= int(result["year"]) <= guesset_year + 1
                    ):
                        continue  # No need to look at anything not +/- one year
            except:
                pass  # Some may not have a year.
            if args.category_id == constants.CATEGORIES["Movie"]:
                # Needs to be 'movie' in... due to they type can be 'tv movie' too.
                if result["kind"] is not None and "movie" in result["kind"]:
                    possible_imdb = possible_imdb + [result]
            elif args.category_id == constants.CATEGORIES["TV"]:
                if result["kind"] is not None and result["kind"] == "tv series":
                    possible_imdb = possible_imdb + [result]

        for result in possible_imdb:
            edit_distance = editdistance.eval(
                result["title"].upper(), guessit_info.get("title").upper()
            )
            edit_distances = edit_distances + [edit_distance]
            if edit_distance == 0:
                imdb_info = result
                break
        if imdb_info is None and len(possible_imdb) > 0:
            distance = 1  # start at 1 because first pass handles the 0 case.
            while True:
                for i in range(len(edit_distances)):
                    if distance == edit_distances[i]:
                        imdb_info = possible_imdb[i]
                        break
                if imdb_info is not None:
                    break
                else:
                    distance = distance + 1
                if distance > 100:
                    # Here just in case it gets stuck in an infinte loop
                    raise RuntimeError(
                        "Unable to identify IMDb ID, please specify one manually."
                    )

    return imdb_info


def get_tmdb_info(guessit_info=None, tmdb_id=None, tmdb_category=None, imdb_id=None):
    tmdb_info = None
    tmdb.API_KEY = TMDB_API_KEY
    search = tmdb.Search()

    # Checking for required arguments
    if guessit_info is None and tmdb_id is None and imdb_id is None:
        raise RuntimeError(
            "Gathering TMDb info requires either guessit, TMDb ID, or an IMDb ID..."
        )
    if tmdb_category is None:
        raise RuntimeError("TMDb Category is required...")
    if tmdb_id is not None and int(tmdb_id) == 0:
        raise RuntimeError(
            "TMDb is required...  Please create one or upload via the site manually for this..."
        )
    if tmdb_category == constants.CATEGORIES["Fanres"]:
        print(
            "Fanres Category given...  get_tmdb_info() is using Movie Category, if TV upload manually..."
        )
        tmdb_category = constants.CATEGORIES["Movie"]

    if tmdb_id is not None:
        # Get TMDb info by TMDb ID
        if tmdb_category == constants.CATEGORIES["TV"]:
            tmdb_info = tmdb.TV(tmdb_id)
        elif tmdb_category == constants.CATEGORIES["Movie"]:
            tmdb_info = tmdb.Movies(tmdb_id)
        else:
            raise RuntimeError(
                "Gathering TMDb info with TMDb ID requires a valid category (movie/tv)..."
            )
    elif imdb_id is not None:
        # Get TMDb info by IMDb (if it fails will recursively run with just guessit info)
        imdb_id = "tt" + str(imdb_id).replace("tt", "")
        tmdb_api_url = f"https://api.themoviedb.org/3/find/{imdb_id}"
        headers = {"User-Agent": "BLU"}
        params = {"external_source": "imdb_id", "api_key": TMDB_API_KEY}
        r = requests.get(url=tmdb_api_url, headers=headers, params=params)
        results = r.json()
        if len(results.get("tv_season_results")) > 0:
            if tmdb_category != constants.CATEGORIES["TV"]:
                print(
                    f"\nIMDb links to a TMDb TV show but Movie Category was passed... Switching to TV Category..."
                )
                args.category_id = constants.CATEGORIES["TV"]
                tmdb_category = constants.CATEGORIES["TV"]
            result = results.get("tv_season_results")[0]
        elif len(results.get("tv_results")) > 0:
            if tmdb_category != constants.CATEGORIES["TV"]:
                print(
                    f"\nIMDb links to a TMDb TV show but Movie Category was passed... Switching to TV Category..."
                )
                args.category_id = constants.CATEGORIES["TV"]
                tmdb_category = constants.CATEGORIES["TV"]
            result = results.get("tv_results")[0]
        elif len(results.get("movie_results")) > 0:
            if tmdb_category != constants.CATEGORIES["Movie"]:
                print(
                    f"\nIMDb links to a TMDb Movie but TV Category was passed... Switching to Movie Category..."
                )
                args.category_id = constants.CATEGORIES["Movie"]
                tmdb_category = constants.CATEGORIES["Movie"]
            result = results.get("movie_results")[0]
        else:
            print(f"\nNo TMDb found using {imdb_id}, attempting with guessit info...")
            tmdb_info = get_tmdb_info(
                guessit_info=guessit_info, tmdb_category=tmdb_category
            )
        if tmdb_info is None:
            tmdb_id = result.get("id")
            tmdb_info = get_tmdb_info(tmdb_id=tmdb_id, tmdb_category=tmdb_category)
    else:
        guessit_title = guessit_info.get("title", "")
        guessit_year = guessit_info.get("year", "")
        possible_tmdb, edit_distances = [], []
        tmdb_result = None

        if tmdb_category == constants.CATEGORIES["TV"]:
            response = search.tv(query=guessit_title, first_air_date_year=guessit_year)
        elif tmdb_category == constants.CATEGORIES["Movie"]:
            response = search.movie(query=guessit_title, year=guessit_year)
        else:
            raise RuntimeError(
                "Gathering TMDb info with guessit info requires a valid category (movie/tv)..."
            )

        if response["total_results"] == 0:
            if (
                "AUTO" not in args.tvdb
                and args.tvdb != ""
                and tmdb_category == constants.CATEGORIES["Movie"]
            ):
                tmdb_api_url = f"https://api.themoviedb.org/3/find/{args.tvdb}"
                headers = {"User-Agent": "BLU"}
                params = {"external_source": "tvdb_id", "api_key": TMDB_API_KEY}
                r = requests.get(url=tmdb_api_url, headers=headers, params=params)
                results = r.json()
                if len(results.get("movie_results")):
                    print(
                        f'TMDb found using TVDb "{str(args.tvdb)}"... Using Movie Category...'
                    )
                    result = results.get("movie_results")[0]
                elif len(results.get("tv_results")):
                    print(
                        f'TMDb found using TVDb "{str(args.tvdb)}"...  Using TV Category...'
                    )
                    args.category_id = constants.CATEGORIES["TV"]
                    tmdb_category = constants.CATEGORIES["TV"]
                    result = results.get("tv_results")[0]
                elif len(results.get("tv_season_results")):
                    print(
                        f'TMDb found using TVDb "{str(args.tvdb)}"...  Using TV Category...'
                    )
                    args.category_id = constants.CATEGORIES["TV"]
                    tmdb_category = constants.CATEGORIES["TV"]
                    result = results.get("tv_season_results")[0]
                else:
                    raise RuntimeError(
                        "No TMDb found using guessit info... Please specify one..."
                    )
                tmdb_id = result.get("id")
                return get_tmdb_info(tmdb_id=tmdb_id, tmdb_category=tmdb_category)
            raise RuntimeError(
                "No TMDb found using guessit info... Please specify one..."
            )

        for result in search.results:
            title = ""
            year = ""

            if (
                result.get("first_air_date") is not None
                and result.get("first_air_date") != ""
            ):
                year = int(result.get("first_air_date")[:4])
            if result.get("name") is not None and result.get("name") != "":
                title = result.get("name")
            if (
                result.get("release_date") is not None
                and result.get("release_date") != ""
            ):
                year = int(result.get("release_date")[:4])
            if result.get("title") is not None and result.get("title") != "":
                title = result.get("title")

            if guessit_year != "" and year != "":
                if not (int(guessit_year) - 1 <= year <= int(guessit_year) + 1):
                    continue  # No need to look at anything not +/- one year

            edit_distance = editdistance.eval(title.upper(), guessit_title.upper())
            if edit_distance == 0:
                # This is the correct one.
                tmdb_id = result.get("id")
                tmdb_info = get_tmdb_info(tmdb_id=tmdb_id, tmdb_category=tmdb_category)
                break
            edit_distances = edit_distances + [edit_distance]
            possible_tmdb = possible_tmdb + [result]
        if tmdb_info is None:
            distance = 1
            while True:
                for i in range(len(edit_distances)):
                    if distance == edit_distances[i]:
                        tmdb_id = possible_tmdb[i].get("id")
                        tmdb_info = get_tmdb_info(
                            tmdb_id=tmdb_id, tmdb_category=tmdb_category
                        )
                        break
                if tmdb_info is not None:
                    break
                else:
                    distance = distance + 1
                if distance > 100:
                    # Here just in case it gets stuck in an infinte loop
                    raise RuntimeError(
                        "Unable to identify TMDb ID, please specify one manually."
                    )

    return tmdb_info


def get_best_identifiers(
    guessit_info=None, tmdb_data=None, imdb_data=None, tmdb_category=None
):
    if guessit is None or tmdb_data is None or tmdb_category is None:
        raise RuntimeError(
            "Guessit info, tmdb data, and tmdb category is required to get pick between IMDb/TMDb..."
        )
    if imdb_data is None:
        print(
            "No IMDb data found while checking better choice for database identifiers, using info from TMDb..."
        )
        return get_external_ids(tmdb_data=tmdb_data)

    tmdb_id, imdb_id, tvdb_id = get_external_ids(tmdb_data=tmdb_data)

    if imdb_id is None:
        print(
            "TMDb doesn't seem to have an IMDb for this, check the upload and verify correct IMDb."
        )
        print(f"\tIf the IMDb ID is correct consider updating TMDb.")
        return tmdb_id, imdb_data.movieID, tvdb_id
    if int(imdb_id.replace("tt", "")) == int(imdb_data.movieID):
        # They aready matched, return the results from TMDb
        return tmdb_id, imdb_id, tvdb_id

    # The IDs do not match, need to use edit distance to compare.
    tmdb_info = tmdb_data.info()
    tmdb_title = ""
    imdb_title = imdb_data.get("title")

    if tmdb_info.get("title") is not None and tmdb_info.get("title") != "":
        tmdb_title = tmdb_info.get("title")
    if tmdb_info.get("name") is not None and tmdb_info.get("name") != "":
        tmdb_title = tmdb_info.get("name")

    edit_distance_tmdb = abs(
        editdistance.eval(tmdb_title.upper(), guessit_info.get("title").upper())
    )
    edit_distance_imdb = abs(
        editdistance.eval(imdb_title.upper(), guessit_info.get("title").upper())
    )

    if edit_distance_tmdb < edit_distance_imdb:
        # Use TMDb
        return tmdb_id, imdb_id, tvdb_id
    if edit_distance_imdb < edit_distance_tmdb:
        # Use IMDb
        tmdb_data = get_tmdb_info(
            tmdb_category=tmdb_category,
            imdb_id=imdb_data.movieID,
            guessit_info=guessit_info,
        )
        return get_external_ids(tmdb_data=tmdb_data, imdb_data=imdb_data)
    if edit_distance_imdb == edit_distance_tmdb:
        # In the case of they matched, TMDb is being used.
        print(
            "Get best Identifiers found two shows with the same edit distance, but different IDs, using ones from TMDb..."
        )
        return tmdb_id, imdb_id, tvdb_id


def autodetect_category(g):
    if g.get("type") == "episode" or g.get("type") == "TV" or g.get("type") == "season":
        return constants.CATEGORIES["TV"]
    if g.get("type") == "movie":
        return constants.CATEGORIES["Movie"]


def autodetect_type(path, guessit_info):
    if Path(path).is_dir():
        for root, directories, filenames in os.walk(path):
            if "BDMV" in directories:
                return constants.TYPES["Full Disc"]
            for filename in filenames:
                if filename == "VTS_01_0.BUP":
                    return constants.TYPES["Full Disc"]
    if guessit_info.get("source") is not None:
        if "Web" in guessit_info.get("source") and "Rip" in guessit_info.get(
            "other", "Null"
        ):
            return constants.TYPES["WEBRip"]
        elif "Web" in guessit_info.get("source") and "Rip" not in guessit_info.get(
            "other", "Null"
        ):
            return constants.TYPES["WEB-DL"]
        elif "Blu-ray" in guessit_info.get("source") and "Remux" in guessit_info.get(
            "other", "Null"
        ):
            return constants.TYPES["Remux"]
        elif "HDTV" in guessit_info.get("source"):
            return constants.TYPES["HDTV"]
        else:
            return constants.TYPES["Encode"]


def get_file_list(path):
    if os.path.isfile(path):
        return [path]

    filelist = os.listdir(path)
    return_filelist = []
    for f in filelist:
        file = os.path.join(path, f)
        return_filelist += [file]
        if not os.path.isfile(file):
            return_filelist += get_file_list(file)
    return return_filelist


def get_dvd_info(path):
    _, dvd_size = num_file(path)
    dvd_type = "DVD5" if dvd_size < 4707319808 else "DVD9"
    vobs = list(
        set([x for x in get_file_list(path) if x.endswith(".VOB") and "VTS_" in x])
    )
    vobs.sort()  # sort them so we can loop through them.
    max_vob_number = 0
    max_set_size = 0
    current_vob_number = 0
    current_set_size = 0
    for vob in vobs:
        vob_number = re.match("(.*VTS_)(\d{2})(_\d.VOB)", vob).group(2)
        vob_size = num_file(vob)[1] # Will be required to be > 128KiB
        if vob_number == current_vob_number:
            current_set_size += vob_size
        else:
            if max_set_size < current_set_size:
                max_set_size = current_set_size
                max_vob_number = current_vob_number
            current_set_size = vob_size
            current_vob_number = vob_number
    if max_set_size < current_set_size:
        max_set_size = current_set_size
        max_vob_number = current_vob_number
    main_vobs = [
        vob for vob in vobs if re.match(rf"(.*VTS_)({max_vob_number})(_\d.VOB)", vob)
    ]
    main_vobs_scanable = []
    for vob in main_vobs:
        try:
            vob_mi = pymediainfo.parse(vob)
            a_info = get_mediainfo_audio(vob_mi)  # [audio_format, audio_channels]
            v_format, v_dynamic_range = get_mediainfo_video(vob_mi)
            main_vobs_scanable.append(vob)
        except:
            print(f"Unable to scan VOB... '{vob}'... VOB will be ignored...")
    main_vobs = main_vobs_scanable
    if args.debug:
        print(f"Found main vobs...")
        for vob in main_vobs:
            vob_size = num_file(vob)[1]
            print(f"\t{vob} ({sizeof_fmt(vob_size)})")
        print("")
    if len(main_vobs) > 1:
        main_vobs = main_vobs[1:]
    if len(main_vobs) > 2:
        main_vobs = main_vobs[:-1]
    ifo_file = os.path.join(path, f"VTS_{max_vob_number}_0.IFO")
    vob_file = main_vobs[0]
    vob_mediainfo = pymediainfo.parse(vob_file)
    ifo_mediainfo = pymediainfo.parse(ifo_file)
    return {
        "ifo_file": ifo_file,
        "vob_file": vob_file,
        "vob_mediainfo": vob_mediainfo,
        "ifo_mediainfo": ifo_mediainfo,
        "vob_list": main_vobs,
        "dvd_type": dvd_type,
    }


def disc_info(path):  # modified for better DVD
    BluRay, HDDVD = [], []  # Stores a list of disc base folders
    DVD_Info = []  # Stores info for all DVDs in the torrent.
    folders = [f for f in get_file_list(path) if not os.path.isfile(f)]
    files = [f for f in get_file_list(path) if os.path.isfile(f)]
    folders.sort()
    files.sort()
    for f in folders:
        if f.endswith("/BDMV") or f.endswith("\BDMV"):
            BluRay += [f]
        elif f.endswith("/HVDVD_TS") or f.endswith("\HVDVD_TS"):
            HDDVD += [f]
        elif f.endswith("/VIDEO_TS") or f.endswith("\VIDEO_TS"):
            DVD_Info += [get_dvd_info(f)]
    for f in files:
        if f.endswith(".iso") or f.endswith(".ISO"):
            BluRay += [f]
    return BluRay, DVD_Info, HDDVD


def scene_check(filename):
    guessit_info, old_scene = None, None
    if len(path) < 5:
        return None
    old_scene = re.fullmatch("[\da-z]+-[\da-z.]+(-[\da-z.]+)?", path[:-4])
    if old_scene is not None:
        try:
            sample_name = path[:-4] + ".sample" + path[-4:]
            srrdb_request = requests.get(
                "https://www.srrdb.com/api/search/store-real-filename:" + sample_name,
                timeout=1,
            )
            full_release = srrdb_request.json()["results"][0].get("release") + path[-4:]
            guessit_info = guessit(full_release)
        except:
            try:
                sample_name = path[:-4] + "-sample" + path[-4:]
                srrdb_request = requests.get(
                    "https://www.srrdb.com/api/search/store-real-filename:"
                    + sample_name,
                    timeout=1,
                )
                full_release = (
                    srrdb_request.json()["results"][0].get("release") + path[-4:]
                )
                guessit_info = guessit(full_release)
            except:
                guessit_info = None
    else:
        try:
            srrdb_request = requests.get(
                "https://www.srrdb.com/api/search/r:" + path[:-4], timeout=1
            )
            full_release = srrdb_request.json()["results"][0].get("release") + path[-4:]
            guessit_info = guessit(full_release)
        except:
            guessit_info = None

    return guessit_info


def fix_ep_season(guessit_info):
    if args.season:
        if args.season < 0:
            if guessit_info.get("season"):
                guessit_info.pop("season")
        else:
            guessit_info["season"] = args.season
    if args.episode:
        if args.episode < 0:
            if guessit_info.get("episode"):
                guessit_info.pop("episode")
        else:
            guessit_info["episode"] = args.episode
    return guessit_info


def generate_comp_bbcode(comp):
    compBetween = comp["between"]
    numComps = len(compBetween)
    compWidth = 1150 // numComps
    comp_bbcode = " | ".join(compBetween)
    comp_vs = " vs ".join(compBetween)
    comp_bbcode = f"[spoiler={comp_vs}][center]{comp_bbcode}\n"
    i = numComps
    for img in comp["images"]:
        if i == 0:
            comp_bbcode += f"\n"
            i = numComps
        i -= 1
        comp_bbcode += f"[url={img}][img={compWidth}]{img}[/img][/url]"
    comp_bbcode = f"{comp_bbcode}\n[/center][/spoiler]"
    return comp_bbcode


def bbcode_to_comp(bbcode):
    try:
        comparisons = re.findall(
            "\[comparison=.*\][\s\S]*?\[/comparison\]", bbcode, flags=re.I
        )
    except:
        return []
    comps = []
    for comp in comparisons:
        comparisonsBetween = re.findall("comparison=(.*?)\]", comp, flags=re.I)[
            0
        ].split(",")
        comparisonsBetween = [c.strip() for c in comparisonsBetween]
        images = [
            match[0].strip()
            for match in re.findall("(https?.*?\.(png|jpg))", comp, flags=re.I)
        ]
        comps += [{"between": comparisonsBetween, "images": images}]
    return comps


def ptp_bbcode_converter(bbcode):
    # Unescape the HTML
    bbcode = html.unescape(bbcode)
    # Remove the hr tag.
    bbcode = bbcode.replace("[hr]", "")
    # Convert crlf to lf (easier to use)
    bbcode = re.sub(r"\r\n", r"\n", bbcode)
    # Remove ptp links, replace ptp url with PTP.
    bbcode = re.sub("https?://passthepopcorn.me", "PTP", bbcode)
    mediainfos = re.findall("\[mediainfo][\s\S]*?\[/mediainfo\]", bbcode, flags=re.I)
    # Currently require mediainfo tag.  Easier, might make it work better later on.
    if mediainfos == []:
        return ""
    # remove some tags
    staff_notes = re.findall("\[staff.*?][\s\S]*?\[/staff\]", bbcode, flags=re.I)
    for staff_note in staff_notes:
        bbcode = bbcode.replace(staff_note, "")
    comparisons = re.findall(
        "\[comparison=.*\][\s\S]*?\[/comparison\]", bbcode, flags=re.I
    )
    comps = []
    for i in range(len(comparisons)):
        comp = comparisons[i]
        comps += bbcode_to_comp(comp)
        bbcode = bbcode.replace(comp, f"COMPARISONREPLACE{i}\n")
    # for comp in comparisons:
    #    bbcode = bbcode.replace(comp, "")
    for mediainfo in mediainfos:
        bbcode = bbcode.replace(mediainfo, "")
    bbcode = re.sub("\[/?img\]", "", bbcode, flags=re.I)
    bbcode = re.sub("\[size=\d+\]", "", bbcode, flags=re.I)
    bbcode = re.sub("\[/size\]", "", bbcode, flags=re.I)
    # Convert quote -> code
    bbcode = re.sub("\[/quote\]", "[/code]", bbcode, flags=re.I)
    bbcode = re.sub("\[quote\]", "[code]", bbcode, flags=re.I)
    quotes = re.findall("\[quote=.*?]", bbcode, flags=re.I)
    for quote in quotes:
        quoted = re.findall("quote=(.*?)\]", quote, flags=re.I)[0].strip()
        bbcode = bbcode.replace(quote, f"[code]{quoted}:\n")
    # convert the aligns
    aligns = re.findall("\[align=.*?\]", bbcode, flags=re.I)
    aligns_close = re.findall("\[/align\]", bbcode, flags=re.I)
    align_stack = []
    for align in aligns:
        align_type = re.findall("align=(.*?)\]", align, flags=re.I)[0].strip().lower()
        align_stack.append(align_type)
        bbcode = bbcode.replace(align, f"[{align_type}]", 1)
    for align_close in aligns_close:
        if align_stack != []:
            align_to_use = align_stack.pop(0)
            bbcode = bbcode.replace(align_close, f"[/{align_to_use}]", 1)
    while True:
        if align_stack == []:
            break
        bbcode += f"[/{align_stack.pop(0)}]"
    images = [
        match[0].strip()
        for match in re.findall("(https?.*?\.(png|jpg))", bbcode, flags=re.I)
    ]
    # Remove images, these are not part of the comps
    for image in images:
        bbcode = bbcode.replace(image, "")
    for i in range(len(comparisons)):
        comp_bbcode = generate_comp_bbcode(comps[i])
        bbcode = bbcode.replace(f"COMPARISONREPLACE{i}", f"{comp_bbcode}\n")
    # Convert hide -> spoiler
    bbcode = re.sub("\[hide=(.*?)\]", r"\n[spoiler=\g<1>]", bbcode, flags=re.I)
    bbcode = re.sub("\[hide\]", f"\n[spoiler]", bbcode, flags=re.I)
    bbcode = re.sub("\[/hide\]", f"[/spoiler]\n", bbcode, flags=re.I)
    # Fix possible new line issues with bullets.
    bbcode = re.sub("\[\*\]\n", "[*]", bbcode)
    blank_tags = re.findall("\[[a-z]+=?[^\W]*\]\n*\[/[a-z]+\]", bbcode, flags=re.I)
    for bt in blank_tags:
        tags = re.findall("\[(.*?)\]\n*\[/(.*?)\]", bt, flags=re.I)
        first_tag = tags[0][0].strip()
        second_tag = tags[0][1].strip()
        if first_tag.lower() == second_tag.lower():
            bbcode = bbcode.replace(bt, "")
    # Remove extra newlines within the lists.
    bbcode = bbcode = re.sub(r"\n+\[\*\]", "[*]", bbcode)
    # Temove excess newlines at end and any cases of multiple newlines in a row.
    # Allows for two in a row for formatting.
    bbcode = re.sub(r"\n+", "\n", bbcode)
    bbcode = re.sub(r"\n+$", "", bbcode)
    bbcode = re.sub(r"^\n+", "", bbcode)
    return bbcode


def preprocessing(path, guessit_info):
    global api_files_data
    assert Path(path).exists()
    tmdb_info, tmdb_data, tvdb_info, imdb_info, mal, hdb_data = (
        None,
        None,
        None,
        None,
        None,
        None,
    )
    tmdb_title, tmdb_year = "", ""
    tmdb_year = ""

    if (args.season or args.episode) and "AUTO" in args.category_id:
        args.category_id = constants.CATEGORIES["TV"]
    guessit_info = fix_ep_season(guessit_info)

    if args.ptp and args.imdb == "AUTO-DETECT":
        print("Attempting to get IMDb from PTP")
        args.imdb, ptp_id = get_ptp_imdb()
        if args.imdb == None or int(args.imdb.replace("tt", "")) == 0:
            args.imdb = "AUTO-DETECT"
        if ptp_id != -1:
            args.ptp = ptp_id
    comp_bbcode = ""
    ptp_bbcode = ""
    if args.ptp and "auto" not in str(args.ptp).lower() and int(args.ptp) > 0:
        ptp_bbcode = get_ptp_bbcode()
        comps = bbcode_to_comp(ptp_bbcode)
        ptp_bbcode = ptp_bbcode_converter(ptp_bbcode)
        for comp in comps:
            comp_bbcode = f"{comp_bbcode}{generate_comp_bbcode(comp)}\n"
        if args.description == "-1":
            ptp_bbcode = ""
        if ptp_bbcode != "":
            comp_bbcode = ""

    scene_guessit = scene_check(path)
    if scene_guessit:
        if scene_guessit.get("edition") == "Limited":
            scene_guessit.pop("edition")
        elif scene_guessit.get("edition"):
            new_edition = []
            for e in scene_guessit.get("edition"):
                if e == "Limited":
                    pass
                else:
                    new_edition += [e]
            scene_guessit["edition"] = new_edition
        guessit_info = scene_guessit

    # Search for full discs starting with IMDb when possible.
    # Pass the guessit title just in case the scene check changed it.
    if args.hdb is not None and "auto" in args.hdb.lower():
        print(f"\nAttempting to match the release to HDB...")
        if (
            args.imdb != "AUTO-DETECT"
            and int(args.imdb.replace("tt", "")) != 0
            and args.type_id == constants.TYPES["Full Disc"]
        ):
            hdb_data = get_hdb_info(
                path, search="imdb", title=guessit_info.get("title")
            )
        elif args.type_id == constants.TYPES["Full Disc"]:
            hdb_data = get_hdb_info(
                path, search="search", title=guessit_info.get("title")
            )
        else:
            hdb_data = get_hdb_info(
                path, search="file", title=guessit_info.get("title")
            )

    # Store old IMDb so we can try and search HDB later if it got updated...
    old_imdb = args.imdb
    if hdb_data is not None:
        if args.debug:
            print(f"HDB Data...\n{hdb_data}\n")
        if "AUTO" in args.type_id:
            if "WEB-DL" == hdb_data.get("type"):
                args.type_id = constants.TYPES["WEB-DL"]
            elif "Remux" == hdb_data.get("type"):
                args.type_id = constants.TYPES["Remux"]
            elif "Blu-ray/HD DVD" == hdb_data.get("type"):
                args.type_id = constants.TYPES["Full Disc"]
            elif "Encode" == hdb_data.get("type"):
                args.type_id = constants.TYPES["Encode"]
            elif "Capture" == hdb_data.get("type"):
                args.type_id = constants.TYPES["HDTV"]
        if "Remux" == hdb_data.get("type"):
            # Add the source to the title, hdb doesn't put it for a remux.  HDDVD would stay, as that one is in it.
            if "2160p" in hdb_data.get("title"):
                hdb_data["title"] = hdb_data.get("title").replace(
                    "Remux", "UHD BluRay REMUX"
                )
            elif "DVD" not in hdb_data.get("title"):
                hdb_data["title"] = hdb_data.get("title").replace(
                    "Remux", "BluRay REMUX"
                )
        if "AUTO" in args.imdb and hdb_data.get("IMDb") is not None:
            args.imdb = str(hdb_data.get("IMDb").get("id"))
        if "AUTO" in args.tvdb and hdb_data.get("TVDb") is not None:
            args.tvdb = str(hdb_data.get("TVDb").get("id"))
        if not args.region:
            args.region = hdb_data.get("region")
        if num_files > 1:
            new_guessit_info = guessit(hdb_data.get("title"))
        else:
            new_title = hdb_data.get("title") + ".mkv"
            new_guessit_info = guessit(new_title)
        if (
            guessit_info.get("episode_title", None) is not None
            and new_guessit_info.get("episode_title", None) is None
        ):
            # Add the episode title back to guessit if it was missing from HDB.
            # This is here so you can use to argument for adding the episode title to the upload title.
            new_guessit_info["episode_title"] = guessit_info.get("episode_title")
        if (
            guessit_info.get("streaming_service", None) is not None
            and new_guessit_info.get("streaming_service", None) is None
        ):
            # Add the streaming service back to guessit, as HDB doesn't put it in the title.
            new_guessit_info["streaming_service"] = guessit_info.get(
                "streaming_service"
            )
        if (
            hdb_data.get("release_group") != guessit_info.get("release_group")
            and hdb_data.get("release_group") is not None
        ):
            new_guessit_info["release_group"] = guessit_info.get("release_group")
        if hdb_data.get("category") in ["TV", "Documentary"]:
            new_guessit_info["type"] = "TV" if hdb_data.get("IMDb") is None else "Movie"
            if hdb_data.get("TVDb") is not None:
                if hdb_data.get("TVDb").get("season") is not None:
                    new_guessit_info["season"] = hdb_data.get("TVDb").get("season")
                else:
                    new_guessit_info["season"] = 1
                if hdb_data.get("TVDb", {"episode": 0}).get("episode", 0) != 0:
                    new_guessit_info["episode"] = hdb_data.get("TVDb").get("episode")
            else:
                new_guessit_info["season"] = 1
        guessit_info = new_guessit_info
    if args.debug:
        print(guessit_info)

    if args.category_id == "AUTO-DETECT":
        if "AUTO" not in args.tmdb and re.match(
            "movie/[0-9]+", args.tmdb, flags=re.IGNORECASE
        ):
            args.tmdb = args.tmdb[6:]
            print(f"\nUsing Movie Category detected by TMDb ID: {args.tmdb}")
            args.category_id = constants.CATEGORIES["Movie"]
        elif "AUTO" not in args.tmdb and re.match(
            "tv/[0-9]+", args.tmdb, flags=re.IGNORECASE
        ):
            args.tmdb = args.tmdb[3:]
            print(f"\nUsing TV Category detected by TMDb ID: {args.tmdb}")
            args.category_id = constants.CATEGORIES["TV"]
        else:
            args.category_id = autodetect_category(guessit_info)
        if args.category_id is None:
            args.category_id = constants.CATEGORIES["Movie"]

    else:
        if args.category_id not in [
            constants.CATEGORIES["Movie"],
            constants.CATEGORIES["TV"],
            constants.CATEGORIES["Fanres"],
        ]:
            category_id = args.category_id.upper()
            if "MOVIE" in category_id:
                args.category_id = constants.CATEGORIES["Movie"]
            elif "TV" in category_id:
                args.category_id = constants.CATEGORIES["TV"]
            elif "FAN" in category_id:
                args.category_id = constants.CATEGORIES["Fanres"]
            else:
                raise RuntimeError(
                    f"Invalid category given... Expected the ID or Movie/TV/Fan...  Recieved {args.category_id}"
                )
    if args.tmdb is not None:
        args.tmdb = str(args.tmdb)
    if "AUTO" not in args.tmdb and re.match(
        ".*/[0-9]+", args.tmdb, flags=re.IGNORECASE
    ):
        args.tmdb = re.search("(.*)(/)([0-9]+)", args.tmdb, flags=re.IGNORECASE).group(
            3
        )

    if args.tmdb == "AUTO-DETECT" and args.imdb == "AUTO-DETECT":
        # Most common case, no databse ID passed
        imdb_info = get_imdb_info(guessit_info=guessit_info)
        tmdb_data = get_tmdb_info(
            guessit_info=guessit_info, tmdb_category=args.category_id
        )
    elif args.tmdb == "AUTO-DETECT":
        # Only the IMDb ID was passed
        imdb_info = get_imdb_info(imdb_id=args.imdb, guessit_info=guessit_info)
        if imdb_info is not None:
            tmdb_data = get_tmdb_info(
                imdb_id=imdb_info.movieID,
                tmdb_category=args.category_id,
                guessit_info=guessit_info,
            )
        elif int(args.imdb.replace("tt", "")) != 0:
            raise RuntimeError(
                "IMDb ID passed is incorrect, check and re-run.  For ones without IMDb, use 0..."
            )
        else:
            tmdb_data = get_tmdb_info(
                guessit_info=guessit_info, tmdb_category=args.category_id
            )
    elif args.imdb == "AUTO-DETECT":
        # Only the TMDb ID was passed
        imdb_info = get_imdb_info(guessit_info=guessit_info)
        tmdb_data = get_tmdb_info(
            tmdb_id=args.tmdb, tmdb_category=args.category_id, guessit_info=guessit_info
        )
    else:
        # Both IDs were passed
        imdb_info = get_imdb_info(imdb_id=args.imdb, guessit_info=guessit_info)
        tmdb_data = get_tmdb_info(
            tmdb_id=args.tmdb, tmdb_category=args.category_id, guessit_info=guessit_info
        )

    tmdb_id, imdb_id, tvdb_id = get_best_identifiers(
        tmdb_data=tmdb_data,
        imdb_data=imdb_info,
        guessit_info=guessit_info,
        tmdb_category=args.category_id,
    )

    if tmdb_id != tmdb_data.id:
        tmdb_data = get_tmdb_info(
            tmdb_id=tmdb_id, tmdb_category=args.category_id, guessit_info=guessit_info
        )
    tmdb_info = tmdb_data.info()
    try:
        if imdb_id and imdb_id != "0":
            imdb_info = get_imdb_info(imdb_id=imdb_id.replace("tt", ""))
    except:
        pass
    # Setting final database IDs, done here so any checking can occur first
    args.imdb = imdb_id if args.imdb == "AUTO-DETECT" else args.imdb
    args.tmdb = tmdb_id if args.tmdb == "AUTO-DETECT" else args.tmdb
    args.tvdb = tvdb_id if args.tvdb == "AUTO-DETECT" else args.tvdb
    args.tvdb = "0" if args.tvdb == None or args.tvdb == "" else args.tvdb
    try:
        # Check if the IMDb ID is the same number as the obtained one.
        # If it is replace the ID.
        if int(str(args.imdb).replace("tt", "")) == int(
            str(imdb_id).replace("tt", "")
        ) and str(args.imdb).replace("tt", "") != str(imdb_id).replace("tt", ""):
            # Check if the IMDb needs updated, but was same number.
            # Can happen where the IMDb is missing a 0 from different API calls
            print(f"\nChanging IMDb from {args.imdb} to {imdb_id}\n")
            args.imdb = imdb_id
    except:
        pass

    if args.tmdb == None or args.tmdb == "":
        if args.allow_no_tmdb:
            args.tmdb = "0"
        else:
            raise RuntimeError("TMDb is required, create one if needed...")
    if args.imdb == None or args.imdb == "":
        if args.allow_no_imdb:
            args.imdb = "0"
        else:
            raise RuntimeError("IMDb is required, if none exist, pass '0'...")

    if args.type_id == "AUTO-DETECT":
        args.type_id = autodetect_type(path, guessit_info)
        if args.type_id is None:
            args.type_id = constants.TYPES["Encode"]
    else:
        type_id = args.type_id.upper()
        if "WEB" in type_id:
            if "RIP" in type_id:
                args.type_id = constants.TYPES["WEBRip"]
            else:
                args.type_id = constants.TYPES["WEB-DL"]
        elif "TV" in type_id:
            args.type_id = constants.TYPES["HDTV"]
        elif "REMUX" in type_id:
            args.type_id = constants.TYPES["Remux"]
        elif "FULL" in type_id or "DISC" in type_id or "BLU-RAY" in type_id:
            args.type_id = constants.TYPES["Full Disc"]
        elif "ENCODE" in type_id or "BLURAY" in type_id or "BDRIP" in type_id:
            args.type_id = constants.TYPES["Encode"]
        elif args.type_id not in constants.TYPES:
            raise RuntimeError(f"Invalid type passed... Recieved {args.type_id}")

    if args.group is not None and not args.nogroup:
        guessit_info["release_group"] = args.group

    if args.nogroup:
        guessit_info["release_group"] = None

    # Use config file for groups
    if guessit_info.get("release_group") is not None:
        if f"{guessit_info.get('release_group')}_Group" in config.sections():
            rg_config = config[f"{guessit_info.get('release_group')}_Group"]
            if args.description == "":
                description_fallback = config["DEFAULT"].get("description", "")
                args.description = rg_config.get("description", description_fallback)
            if not args.internal:
                args.internal = rg_config.getboolean("internal", fallback=False)
            if not args.anonymous:
                anon_fallback = config["DEFAULT"].getboolean(
                    "anonymous", fallback=False
                )
                args.anonymous = rg_config.getboolean(
                    "anonymous", fallback=anon_fallback
                )
            if not args.doubleup:
                args.doubleup = rg_config.getboolean("double up", fallback=False)
            if not args.free:
                args.free = rg_config.getboolean("freeleech", fallback=False)
            if not args.personal:
                args.personal = rg_config.getboolean("personal", fallback=False)
        else:
            if not args.anonymous:
                args.anonymous = config["DEFAULT"].getboolean(
                    "anonymous", fallback=False
                )
            if args.description == "":
                args.description = config["DEFAULT"].get("description", "")
    else:
        default_config = config["DEFAULT"]
        if not args.anonymous:
            args.anonymous = default_config.getboolean("anonymous", fallback=False)
        if args.description == "":
            args.description = default_config.get("description", "")

    args.anonymous = "1" if args.anonymous else "0"
    args.internal = "1" if args.internal else "0"
    args.free = "1" if args.free else "0"
    args.doubleup = "1" if args.doubleup else "0"
    args.sticky = "1" if args.sticky else "0"
    args.featured = "1" if args.featured else "0"
    args.stream = autodetect_streamop(media_info) if not args.stream else "0"

    tmdb_title, tmdb_title_aka, tmdb_title_roman, tmdb_title_aka_roman = get_tmdb_titles(
        tmdb_info
    )
    imdb_title, imdb_title_aka, imdb_title_roman, imdb_title_aka_roman = get_imdb_titles(
        imdb_info
    )

    # Make a stripped string (no special characters or spaces).  Used to not keep a title that is in another.
    imdb_roman_stripped = (
        re.sub("[^A-Za-z0-9]+", "", imdb_title_roman.lower().replace("&", "and"))
        if imdb_title
        else None
    )
    tmdb_roman_stripped = (
        re.sub("[^A-Za-z0-9]+", "", tmdb_title_roman.lower().replace("&", "and"))
        if tmdb_title
        else None
    )
    imdb_aka_roman_stripped = (
        re.sub("[^A-Za-z0-9]+", "", imdb_title_aka_roman.lower().replace("&", "and"))
        if imdb_title_aka
        else None
    )
    tmdb_aka_roman_stripped = (
        re.sub("[^A-Za-z0-9]+", "", tmdb_title_aka_roman.lower().replace("&", "and"))
        if tmdb_title_aka
        else None
    )

    if tmdb_title and imdb_title:
        if imdb_roman_stripped in tmdb_roman_stripped:
            api_name_roman = tmdb_title_roman
            api_name = tmdb_title
        elif tmdb_roman_stripped in imdb_roman_stripped:
            api_name_roman = imdb_title_roman
            api_name = imdb_title
        else:
            api_name_roman = tmdb_title_roman
            api_name = tmdb_title
    elif tmdb_title_roman:
        api_name_roman = tmdb_title_roman
        api_name = tmdb_title
    else:
        api_name_roman = imdb_title_roman
        api_name = imdb_title

    api_name_roman_stripped = re.sub(
        "[^A-Za-z0-9]+", "", api_name_roman.lower().replace("&", "and")
    )
    anime_info = get_anime_info(api_name, tmdb_info, args.mal)
    romaji_stripped = re.sub(
        "[^A-Za-z0-9]+", "", anime_info.get("romaji", "").lower().replace("&", "and")
    )

    if imdb_roman_stripped and imdb_roman_stripped not in api_name_roman_stripped:
        api_aka = imdb_title
        api_aka_roman = imdb_title_roman
    elif (
        imdb_aka_roman_stripped
        and imdb_aka_roman_stripped not in api_name_roman_stripped
    ):
        api_aka = imdb_title_aka
        api_aka_roman = imdb_title_aka_roman
    elif (
        tmdb_aka_roman_stripped
        and tmdb_aka_roman_stripped not in api_name_roman_stripped
    ):
        api_aka = tmdb_title_aka
        api_aka_roman = tmdb_title_aka_roman
    else:
        api_aka, api_aka_roman = (None, None)

    romaji_stripped = re.sub(
        "[^A-Za-z0-9]+", "", anime_info.get("romaji", "").lower().replace("&", "and")
    )
    if anime_info.get("romaji") and romaji_stripped not in api_name_roman:
        # For anime, make sure romaji isn't in the name already.
        tmdb_title = f"{api_name_roman} AKA {anime_info.get('romaji')}"
    elif api_aka:
        tmdb_title = f"{api_name_roman} AKA {api_aka_roman}"
    else:
        tmdb_title = api_name_roman

    if str(args.tmdb) != "0" and args.category_id == constants.CATEGORIES["Movie"]:
        if tmdb_info.get("release_date") is not None:
            tmdb_year = tmdb_info.get("release_date")[0:4]
    elif str(args.tmdb) != "0" and args.category_id == constants.CATEGORIES["TV"]:
        if tmdb_info.get("first_air_date") is not None:
            tmdb_year = tmdb_info.get("first_air_date")[0:4]

    if args.category_id == constants.CATEGORIES["TV"] and tmdb_year is not None:
        # Check for TV shows with year in filename and add the year to the name.
        if Path(path).is_dir() and path.endswith("/"):
            path = path[:-1]
        if tmdb_year in os.path.basename(path) and tmdb_year not in tmdb_title:
            tmdb_title = f"{tmdb_title} {tmdb_year}"
    if guessit_info.get("other") is not None:
        if "Proper" in guessit_info.get("other") and args.proper in [None, ""]:
            if (
                "REPACK" in str(os.path.basename(path)).upper()
                and "REPACK" not in (guessit_info.get("title", "") + tmdb_title).upper()
            ):
                guessit_info["proper_count"] = guessit_info["proper_count"] - 1
                if isinstance(guessit_info["other"], str):
                    guessit_info["other"] = [guessit_info["other"]] + ["Repack"]
                else:
                    guessit_info["other"] = guessit_info["other"] + ["Repack"]
                if guessit_info["proper_count"] == 0:
                    guessit_info["other"].remove("Proper")
    # Get the keywords from TMDb, default is overrite unless --append-keywords is passed
    tmdb_keywords = get_keywords(tmdb_data)
    if args.keywords is not None:
        if args.append_keywords and tmdb_keywords != "":
            args.keywords = args.keywords + "," + tmdb_keywords
        else:
            args.keywords = args.keywords
    else:
        args.keywords = tmdb_keywords
    print(f'Using keywords:\t"{args.keywords}"')

    if anime_info.get("id") and args.mal == "0":
        args.mal = str(anime_info.get("id"))

    # Check HDB with new IMDb, only update disc region.
    if (
        args.hdb is not None
        and hdb_data is None
        and old_imdb != args.imdb
        and args.type_id == constants.TYPES["Full Disc"]
        and "auto" in args.hdb.lower()
    ):
        print(
            f"Attempting to match the release to HDB the second time with updated IMDb info..."
        )
        hdb_data = get_hdb_info(
            path, search="imdb", title=guessit_info.get("title"), tryNext=False
        )
        if hdb_data:
            if not args.region:
                args.region = hdb_data.get("region")
            if guessit_info.get("release_group") is None and not args.nogroup:
                guessit_info["release_group"] = guessit(hdb_data.get("title")).get(
                    "release_group"
                )
    if guessit_info.get("release_group", None) and guessit_info.get(
        "release_group", ""
    ).lower() in ["nogrp", "nogroup"]:
        guessit_info["release_group"] = None
    guessit_info = fix_ep_season(guessit_info)

    if guessit_info.get("edition") == ["E", "x", "t", "e", "n", "d", "e", "d"]:
        guessit_info["edition"] = "Extended"

    if ptp_bbcode != "":
        if args.description != "":
            args.description = f"{args.description}\n\n{ptp_bbcode}\n"
        else:
            args.description = f"{ptp_bbcode}\n"
    if args.description == "-1":
        args.description = ""
    if comp_bbcode != "":
        if args.description != "":
            args.description = f"{args.description}\n\n{comp_bbcode}\n"
        else:
            args.description = f"{comp_bbcode}\n"

    api_files_data["imdb"] = imdb_info
    api_files_data["tmdb"] = tmdb_data
    api_files_data["tvdb"] = {"id": tvdb_id}
    api_files_data["name"] = {
        "name": api_name,
        "aka": api_aka,
        "romanized": api_name_roman,
        "romanized_aka": api_aka_roman,
    }
    api_files_data["mal"] = anime_info
    api_files_data["tmdb"] = tmdb_data
    api_files_data["keywords"] = args.keywords
    api_files_data["description_arg"] = args.description
    api_files_data["group"] = guessit_info.get("release_group", None)
    return tmdb_title, tmdb_year, guessit_info


def get_tmdb_titles(tmdb_info):
    title, title_aka = (None, None)
    title_roman, title_aka_roman = (None, None)

    if not tmdb_info:
        return (title, title_aka, title_roman, title_aka_roman)
    if type(tmdb_info) in (type(tmdb.Movies()), type(tmdb.TV())):
        tmdb_info = tmdb_info.info()

    if tmdb_info.get("title"):
        title = tmdb_info.get("title")
    elif tmdb_info.get("name"):
        title = tmdb_info.get("name")

    if tmdb_info.get("original_title"):
        title_aka = tmdb_info.get("original_title")
    elif tmdb_info.get("original_name"):
        title_aka = tmdb_info.get("original_name")
    if not title:
        title = ""
    if not title_aka:
        title_aka = ""
    if tmdb_info.get("original_language") == "ja":
        kks = pykakasi.kakasi()
        if not ascii_check(title):
            title_roman = kks.convert(title)[0]["hepburn"]
        else:
            title_roman = title
        if not ascii_check(title_aka):
            title_aka_roman = kks.convert(title_aka)[0]["hepburn"]
        else:
            title_aka_roman = title_aka
    if title != "" and title_roman in (None, ""):
        title_roman = unidecode(title)
    elif title_roman in (None, ""):
        title_roman = None
    if title_aka != "" and title_aka_roman in (None, ""):
        title_aka_roman = unidecode(title_aka)
    elif title_aka_roman in (None, ""):
        title_aka_roman = None
    return (title, title_aka, title_roman, title_aka_roman)


def get_imdb_titles(imdb_info):
    if not imdb_info:
        return (None, None, None, None)
    title, title_aka = (None, None)
    title_roman, title_aka_roman = (None, None)
    title = imdb_info.get("title")
    title_aka = imdb_info.get("original title")
    if not title_aka:
        country_list = imdb_info.get("countries")
        aka_list_country = []
        akas = imdb_info.get("akas")
        try:
            if akas and country_list:
                if args.debug:
                    print(f"List of AKAs from IMDb: {akas}")
                for aka in akas:
                    aka_match = re.match("(.*)( \()(.*)(\))", aka)
                    aka_list_country += [
                        {"title": aka_match.group(1), "country": aka_match.group(3)}
                    ]
                for aka in aka_list_country:
                    if aka.get("title") == imdb_info.get("localized title"):
                        if aka.get("country") in country_list:
                            title_aka = imdb_info.get("localized title")
                            break
        except:
            pass
    title_roman = unidecode(title) if title else None
    title_aka_roman = unidecode(title_aka) if title_aka else None

    return (title, title_aka, title_roman, title_aka_roman)


def from_japan(tmdb_info):
    return tmdb_info.get("original_language", "") == "ja" or "JP" in tmdb_info.get(
        "origin_country", [""]
    )


def is_animation(tmdb_info):
    genres = tmdb_info.get("genres", {})
    for genre in genres:
        if genre.get("id", 0) == 16:
            return True
    return False


def get_mal_data(name, mal="0"):
    anilist_data = {}
    # Special thanks to L4G for showing me the anilist api
    if mal != "0":
        # Use the MalID specified if given.
        query = "query ($idMal: Int) {  Media (idMal: $idMal, type: ANIME) { id idMal title { romaji english native }}}"
        variables = {"idMal": int(mal)}
    else:
        # Otherwise just use the TMDb name
        query = "query ($search: String) {  Media (search: $search, type: ANIME) { id idMal title { romaji english native }}}"
        variables = {"search": name}

    url = "https://graphql.anilist.co"
    r = requests.post(url, json={"query": query, "variables": variables})

    try:
        result = r.json()
        romaji = result["data"]["Media"]["title"]["romaji"]
        english = result["data"]["Media"]["title"]["english"]
        native = result["data"]["Media"]["title"]["native"]
        mal = result["data"]["Media"].get("idMal", None)
    except:
        romaji, mal = "", None
        english, native = "", ""
    anilist_data = {"id": mal, "romaji": romaji, "english": english, "native": native}
    return anilist_data


def get_anime_info(title, tmdb_info, mal="0"):
    anilist_data = {}
    if from_japan(tmdb_info) and is_animation(tmdb_info):
        anilist_data = get_mal_data(title, mal)
    return anilist_data


def get_torrent_name(g, info):
    global release_name, dvd_files, is_hddvd
    if g.get("streaming_service") is None and "Web" in g.get("source", ""):
        if "HMAX" in Path(path).name:
            g["streaming_service"] = "HBO Max"
            # Temporary fix until the guessit library is updated to support HMAX
        elif "SHO" in Path(path).name:
            g["streaming_service"] = "Showtime"
            # Temporary fix until the guessit library is updated to support SHO
        elif "ATVP" in Path(path).name or "ATV+" in Path(path).name:
            g["streaming_service"] = "AppleTV"
            # Temporary fix until the guessit library is updated to support ATVP
        elif (
            "DSNP" in Path(path).name
            or "DSN+" in Path(path).name
            or "DNSP" in Path(path).name
        ):
            g["streaming_service"] = "Disney Plus"
            # Temporary fix until the guessit library is updated to support DNSP
        elif "PMTP" in Path(path).name or "PMNP" in Path(path).name:
            g["streaming_service"] = "Paramount+"
            # Temporary fix until the guessit library is updated to support PMTP
    data = defaultdict(lambda: "")
    if g.get("title") is not None:
        data["title"] = g.get("title")
        release_name = f"{data.get('title')} "
    if g.get("year") is not None and args.category_id != constants.CATEGORIES["TV"]:
        data["year"] = g.get("year")
        release_name = f"{release_name} {data.get('year')}"
    if g.get("date") is not None and args.category_id != constants.CATEGORIES["TV"]:
        data["date"] = g.get("date")
        release_name = f"{release_name} {data.get('date')}"
    if (
        g.get("season") is None
        and g.get("episode") is None
        and args.category_id == constants.CATEGORIES["TV"]
        and "miniseries" in args.keywords.lower()
    ):
        data["season"] = str(1).zfill(2)
        release_name = f"{release_name} S{data.get('season')}"
    if g.get("season") is not None and args.category_id == constants.CATEGORIES["TV"]:
        data["season"] = str(g.get("season")).zfill(2)
        api_files_data["name"]["season"] = data["season"]
        release_name = f"{release_name} S{data.get('season')}"
    if g.get("episode") is not None and args.category_id == constants.CATEGORIES["TV"]:
        if isinstance(g.get("episode"), list):
            x = list(range(g.get("episode")[0], g.get("episode")[-1] + 1))
            if g.get("episode") == x:
                data["episode"] = [str(i).zfill(2) for i in g.get("episode")]
                if int(data.get("episode")[0]) + 1 == int(data.get("episode")[-1]):
                    release_name = f"{release_name}E{data.get('episode')[0]}E{data.get('episode')[-1]}"
                else:
                    release_name = f"{release_name}E{data.get('episode')[0]}-{data.get('episode')[-1]}"
            else:
                data["episode"] = defaultdict(lambda: "")
                i = 0
                while i < len(g.get("episode")) - 1:
                    data["episode"][i] = str(g.get("episode")[i]).zfill(2)
                    release_name = f"{release_name}E{data.get('episode')[i]}"
                    i += 1
        else:
            data["episode"] = str(g.get("episode")).zfill(2)
            release_name = f"{release_name}E{data.get('episode')}"
        api_files_data["name"]["episode_title"] = g.get("episode_title", "")
        api_files_data["name"]["episode"] = data["episode"]
    if (
        g.get("episode") is None
        and g.get("season") is None
        and g.get("date")
        and args.category_id == constants.CATEGORIES["TV"]
    ):
        release_name = f"{release_name} {g.get('date').isoformat()}"
    if args.hybrid:
        api_files_data["hybrid"] = True
        release_name = f"{release_name} Hybrid"
    if g.get("edition") is not None and args.cut is None:
        if isinstance(g.get("edition"), str):
            if "criterion" in g.get("edition").lower():
                g["edition"] = ""
            api_files_data["cut"] = g.get("edition")
            if g["edition"] == "Extended":
                g["edition"] = "Extended Cut"
            if g["edition"] == "Special":
                g["edition"] = "Special Edition"
            release_name = f"{release_name} {g.get('edition')}"
        else:
            new_edition = []
            for e in g.get("edition"):
                if "criterion" in e.lower():
                    pass
                else:
                    new_edition += [e]
            api_files_data["cut"] = new_edition
            release_name = f"{release_name} {' '.join(g.get('edition'))}"
    if args.cut is not None:
        release_name = f"{release_name} {args.cut}"
    if g.get("other") is not None:
        if (
            "Proper" in g.get("other")
            and args.rerip is None
            and (
                "RERIP" in Path(path).name.upper()
                or "RE-RIP" in Path(path).name.upper()
            )
        ):
            data["rerip"] = True
            data["rerip_count"] = g.get("proper_count")
            api_files_data["rerip_count"] = g.get("proper_count")
        if args.rerip and args.rerip != 0:
            data["rerip"] = True
            data["rerip_count"] = args.rerip
            api_files_data["rerip_count"] = args.rerip
        if data["rerip_count"] and "PROPER" in Path(path).name.upper():
            data["rerip_count"] = data["rerip_count"] - 1
            api_files_data["rerip_count"] = api_files_data["rerip_count"] - 1
        if g.get("proper_count", 0) > 0 and data.get("rerip") and not args.proper:
            args.proper = g.get("proper_count", 0) - data.get("rerip_count", 1)
        if "Proper" in g.get("other") and args.proper in [None, ""]:
            data["proper"] = True
            data["proper_count"] = g.get("proper_count")
            api_files_data["proper_count"] = g.get("proper_count")
            if data.get("proper_count") > 1:
                release_name = f"{release_name} PROPER{data.get('proper_count')}"
            elif data.get("proper_count") == 1:
                release_name = f"{release_name} PROPER"
        if args.proper:
            api_files_data["proper_count"] = args.proper
            if int(args.proper) > 1:
                release_name = f"{release_name} PROPER{args.proper}"
            elif int(args.proper) == 1:
                release_name = f"{release_name} PROPER"
        if data.get("rerip_count") and data.get("rerip_count", 0) > 1:
            release_name = f"{release_name} RERIP{data.get('rerip_count')}"
        elif data.get("rerip_count", 0) == 1:
            release_name = f"{release_name} RERIP"
        if "Repack" in g.get("other") and args.repack is None:
            api_files_data["repack_count"] = 1
            data["repack"] = True
            release_name = f"{release_name} REPACK"
        if args.repack is not None:
            api_files_data["repack_count"] = args.repack
            if int(args.repack) > 1:
                release_name = f"{release_name} REPACK{args.repack}"
            elif int(args.repack) == 1:
                release_name = f"{release_name} REPACK"
    else:
        if args.proper:
            api_files_data["proper_count"] = args.proper
            if int(args.proper) > 1:
                release_name = f"{release_name} PROPER{args.proper}"
            elif int(args.proper) == 1:
                release_name = f"{release_name} PROPER"
        if args.rerip:
            api_files_data["rerip_count"] = args.rerip
            if int(args.proper) > 1:
                release_name = f"{release_name} RE-RIP{args.rerip}"
            elif int(args.proper) == 1:
                release_name = f"{release_name} RE-RIP"
        if args.repack:
            api_files_data["repack_count"] = args.repack
            if int(args.repack) > 1:
                release_name = f"{release_name} REPACK{args.repack}"
            elif int(args.repack) == 1:
                release_name = f"{release_name} REPACK"

    if (
        args.episode_title is not None
        and args.category_id == constants.CATEGORIES["TV"]
    ):
        if args.episode_title == "1":
            release_name = f"{release_name} {g.get('episode_title','')}"
        else:
            release_name = f"{release_name} {args.episode_title}"
            api_files_data["name"]["episode_title"] = g.get(args.episode_title, "")

    data["resolution"], data["scanType"], data["resId"] = autodetect_resolution(info)
    release_name = (
        f"{release_name} {data.get('resolution')}{data.get('scanType')[0].lower()}"
    )
    data["video_codec"], data["dynamic_range"] = get_mediainfo_video(info)
    add_dynamic = data.get("dynamic_range") is not None
    try:
        other_3d = "3D" in g.get("other")
    except:
        other_3d = False
    mediainfo_3d = get_3d_mediainfo(info, Path(path).name, other_3d)
    if mediainfo_3d:
        data["3D"] = mediainfo_3d if mediainfo_3d else "3D"
        api_files_data["3D"] = data["3D"]
    if g.get("streaming_service") is not None and (
        "Web" in g.get("source", "")
        or args.type_id == constants.TYPES["WEB-DL"]
        or args.type_id == constants.TYPES["WEBRip"]
    ):
        if args.web:
            try:
                if args.web.lower() == "amazon":
                    args.web = "Amazon Prime"
                elif args.web.lower() == "netflix":
                    args.web = "Netflix"
                elif "apple" in args.web.lower():
                    args.web = "AppleTV"
                elif args.web.lower() == "hulu":
                    args.web = "Hulu"
                elif "iplayer" in args.web.lower():
                    args.web = "BBC iPlayer"
                data["streaming_service"] = constants.NETWORK[args.web]
            except:
                data["streaming_service"] = args.web.upper()
        else:
            data["streaming_service"] = constants.NETWORK[g.get("streaming_service")]
        release_name = f"{release_name} {data.get('streaming_service')}"
    else:
        data["streaming_service"] = None
        g["streaming_service"] = None
    check_type = g.get("source") is None
    if g.get("source") is not None:
        if "Web" in g.get("source") and "Rip" in g.get("other", "Null"):
            data["source"] = "WEBRip"
        elif "Web" in g.get("source") and "Rip" not in g.get("other", "Null"):
            data["source"] = "WEB-DL"
        elif "Blu-ray" in g.get("source") and "Remux" in g.get("other", "Null"):
            if "Ultra HD" in g.get("source"):
                data["source"] = "UHD BluRay REMUX"
            else:
                data["source"] = "BluRay REMUX"
        elif "Blu-ray" in g.get("source") and "Remux" not in g.get("other", "Null"):
            if "Ultra HD" in g.get("source"):
                data["source"] = "UHD BluRay"
            else:
                data["source"] = "BluRay"
        elif "HD-DVD" in g.get("source") and "Remux" in g.get("other", "Null"):
            data["source"] = "HDDVD REMUX"
            is_hddvd = True
        elif "HD-DVD" in g.get("source") and "Remux" not in g.get("other", "Null"):
            data["source"] = "HDDVD"
            is_hddvd = True
        elif "DVD" in g.get("source") and "Remux" in g.get("other", "Null"):
            data["source"] = "DVD REMUX"
        elif "DVD" in g.get("source") and "Remux" not in g.get("other", "Null"):
            data["source"] = "DVD"
        elif "Ultra HDTV" in g.get("source"):
            data["source"] = "UHDTV"
        elif "HDTV" in g.get("source"):
            data["source"] = "HDTV"
    # Compare source to type ID and verify match.
    if args.type_id is not None and g.get("source") is not None:
        if args.type_id == constants.FULL_DISC_TYPE_ID:
            check_type = not re.fullmatch(
                "UHD BluRay|BluRay|HDDVD|DVD", data.get("source", "")
            )
        elif args.type_id == constants.REMUX_TYPE_ID:
            check_type = not re.fullmatch(
                "UHD BluRay REMUX|BluRay REMUX|HDDVD REMUX|DVD REMUX",
                data.get("source", ""),
            )
        elif args.type_id == constants.ENCODE_TYPE_ID:
            check_type = not re.fullmatch(
                "UHD BluRay|BluRay|HDDVD|DVD", data.get("source", "")
            )
        elif args.type_id == constants.WEBDL_TYPE_ID:
            check_type = not re.fullmatch("WEB-DL", data.get("source", ""))
        elif args.type_id == constants.WEBRIP_TYPE_ID:
            check_type = not re.fullmatch("WEBRip", data.get("source", ""))
        elif args.type_id == constants.HDTV_TYPE_ID:
            check_type = not re.fullmatch("UHDTV|HDTV", data.get("source", ""))
    # A few cases when source is none, but type can still be found from args.
    if check_type:
        data["source"] = ""
        if args.type_id == constants.TYPES["WEB-DL"]:
            data["source"] = "WEB-DL"
        elif args.type_id == constants.TYPES["WEBRip"]:
            data["source"] = "WEBRip"
        elif args.type_id == constants.TYPES["HDTV"]:
            data["source"] = "HDTV"
        elif (
            args.type_id == constants.TYPES["Full Disc"]
            and get_extension(media_info) == "VOB"
        ):
            data["source"] = "DVD"
        elif args.type_id == constants.TYPES["Full Disc"] and is_hddvd:
            data["source"] = "HD DVD"
        elif (
            args.type_id == constants.TYPES["Full Disc"]
            and int(data.get("resolution")) >= 2160
        ):
            data["source"] = "UHD Blu-ray"
        elif args.type_id == constants.TYPES["Full Disc"]:
            data["source"] = "Blu-ray"
        elif (
            args.type_id == constants.TYPES["Encode"]
            and int(data.get("resolution")) >= 2160
        ):
            data["source"] = "UHD BluRay"
        elif (
            args.type_id == constants.TYPES["Encode"]
            and int(data.get("resolution")) >= 720
        ):
            if g.get("source") and "DVD" in g.get("source"):
                data["source"] = "HDDVD"
                is_hddvd = True
            else:
                data["source"] = "BluRay"
        elif "Remux" in g.get("other", "Null") and int(data.get("resolution")) >= 2160:
            data["source"] = "UHD BluRay REMUX"
        elif "Remux" in g.get("other", "Null") and int(data.get("resolution")) >= 720:
            data["source"] = "BluRay REMUX"
        elif "Remux" in g.get("other", "Null"):
            data["source"] = "DVD REMUX"
    if mediainfo_3d:
        data["source"] = f"3D {data['source']}"
    if args.region is not None and args.type_id == constants.TYPES["Full Disc"]:
        args.region = constants.DISC_REGIONS.get(
            args.region.upper(), args.region.upper()
        )
        api_files_data["region"] = args.region
        data["source"] = f"{args.region} {data['source']}"
    if args.edition is not None:
        data["source"] = f"{args.edition} {data['source']}"

    release_name = f"{release_name} {data.get('source')}"
    data["other"] = g.get("other", "")
    data["audio_codec"], data["audio_channels"] = get_mediainfo_audio(info)

    if "Atmos" in data["audio_codec"]:
        audio_codec = data["audio_codec"].split(" ", 1)
        audio_base_codec = audio_codec[0]
        audio_object = audio_codec[1]
        audio_with_channels = (
            f"{audio_base_codec} {data['audio_channels']} {audio_object}"
        )
    else:
        audio_with_channels = f"{data['audio_codec']} {data['audio_channels']}"

    # Fix codecs, so REMUX is AVC/HEVC and WEB-DL is H.264/H.265
    if "REMUX" in data["source"]:
        args.type_id = constants.TYPES["Remux"]

        if "264" in data["video_codec"]:
            data["video_codec"] = "AVC"
        if "265" in data["video_codec"]:
            data["video_codec"] = "HEVC"
    elif "WEB-DL" in data["source"]:
        if "264" in data["video_codec"] or "AVC" in data["video_codec"]:
            data["video_codec"] = "H.264"
        if "265" in data["video_codec"] or "HEVC" in data["video_codec"]:
            data["video_codec"] = "H.265"
    # Fix for HD DVD discs using H.264
    elif args.type_id == constants.TYPES["Full Disc"] and is_hddvd:
        if "264" in data["video_codec"]:
            data["video_codec"] = "AVC"

    # Adds SDR/HDR when needed
    if add_dynamic:
        video_data = f"{data.get('dynamic_range')} {data.get('video_codec')}"
    else:
        video_data = f"{data.get('video_codec')}"
    # Does naming correct, REMUX is "video audio" and all others are "audio video"
    if "REMUX" in data["source"] or args.type_id == constants.TYPES["Full Disc"]:
        release_name = f"{release_name} {video_data} {audio_with_channels}"
    else:
        release_name = f"{release_name} {audio_with_channels} {video_data}"
    if g.get("release_group"):
        if "MA" in data["audio_codec"] and g.get("release_group", "").startswith("MA"):
            g["release_group"] = g["release_group"][2:]
        elif "LPCM" in data["audio_codec"] and g.get("release_group", "").startswith(
            "LPCM"
        ):
            g["release_group"] = g["release_group"][4:]
        elif "PCM" in data["audio_codec"] and g.get("release_group", "").startswith(
            "PCM"
        ):
            g["release_group"] = g["release_group"][3:]
        if g.get("release_group", "") == "":
            g["release_group"] = None
    # Added a check for group being the cut/edition, just in case it is wrong.
    if g.get("release_group") in [args.cut, args.edition, g.get("edition")]:
        g["release_group"] = None
    if g.get("release_group"):
        data["release_group"] = g.get("release_group")
        if data["release_group"].startswith("-"):
            data["release_group"] = data["release_group"][1:]
        release_name = f"{release_name}-{data.get('release_group')}"
    release_name = " ".join(release_name.split())
    if args.type_id == constants.TYPES["Full Disc"]:
        release_name = release_name.replace("BluRay", "Blu-ray")
        release_name = release_name.replace("HDDVD", "HD DVD")
    # Fix DVD to be NTSC/PAL for DVDs.
    if "DVD" in data["source"] and not is_hddvd:
        dvd_replace = "DVD"
        if len(dvd_files) > 0:
            dvd_types = [dvd["dvd_type"] for dvd in dvd_files]
            number_dvd5s = dvd_types.count("DVD5")
            number_dvd9s = dvd_types.count("DVD9")
            dvd_replace = ""
            if number_dvd9s >= 1:
                dvd_replace = f"{number_dvd9s}xDVD9"
            if number_dvd5s >= 1:
                dvd_replace = f"{dvd_replace} {number_dvd5s}xDVD5".strip()
            data["source"] = dvd_replace
            # Set source to the number of DVDs, useful for api calls.
            dvd_replace = dvd_replace.replace("1x", "")
        release_name = re.sub(
            "(480[ip])(.* ?)( DVD )", f"\g<2> NTSC {dvd_replace} ", release_name
        )
        release_name = re.sub(
            "(576[ip])(.* ?)( DVD )", f"\g<2> PAL {dvd_replace} ", release_name
        )
        release_name = re.sub(data["video_codec"], "", release_name)

    release_name = " ".join(release_name.split())
    return release_name, data


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def create_torrent(path, overwrite=None):
    global torrent_binary
    torrent_name = Path(path).stem
    if Path(path).is_dir():
        torrent_name = Path(path).name
    torrent_path = Path(tempfile.gettempdir()) / ("{}.torrent".format(torrent_name))
    if args.use_torrent:
        try:
            t = torf.Torrent.read(args.use_torrent)
            t.private = True
            t.randomize_infohash = True
            t.randomize_infohash = False
            t.source = torrent_source
            t.trackers = torrent_announce
            t.write(torrent_path, overwrite=True)
            return torrent_path
        except:
            print("Failed to modify existing torrent... hashing new one...")
    if torrent_path.exists():
        if not overwrite:
            return torrent_path
        torrent_path.unlink()
    exclude = ["**.nfo", "**/*.nfo", "*.nfo"]
    try:
        torrent = torf.Torrent(
            path=path,
            trackers=torrent_announce,
            private=True,
            piece_size=None,
            created_by="torf/3.0.0",
            source=torrent_source,
            exclude_globs=exclude,
        )
    except torf.PathEmptyError:
        print("Empty file or directory or directory that contains only empty files")
    except torf.PathNotFoundError:
        print("Path does not exist")
    except torf.ReadError:
        print("Unreadable file or stream")
    torrent = torf.Torrent(
        path=path,
        trackers=torrent_announce,
        private=True,
        piece_size=None,
        created_by="torf/3.0.0",
        source=torrent_source,
        exclude_globs=exclude,
    )

    with ProgressBar(unit="Pieces", desc="Creating torrent") as bar:
        success = torrent.generate(callback=bar.update_to, interval=0)

    print(torrent.magnet(name=True, size=True, tracker=True))
    torrent_binary = torrent
    torrent.write(torrent_path)
    return torrent_path


def getbdinfo(bdinfo_file, prepend=""):
    bdinfo = {"full": "", "main": "", "summary": ""}
    mono = ["mono"] if not helpers.is_windows() else []
    bdinfow = ["-w"]
    bdinfo_save_path = os.path.join(os.getcwd(), "bdinfo")
    if not os.path.exists(bdinfo_save_path):
        os.mkdir(bdinfo_save_path)
    if prepend != "":
        bdinfo_save_path = os.path.join(bdinfo_save_path, prepend)
    if not os.path.exists(bdinfo_save_path):
        os.mkdir(bdinfo_save_path)
    if bdinfo_file.lower().endswith("bdmv"):
        bdinfo_path = os.path.basename(os.path.dirname(bdinfo_file))
    else:
        bdinfo_path = os.path.splitext(os.path.basename(bdinfo_file))
        if type(bdinfo_path) is not str:
            bdinfo_path = bdinfo_path[0]
    bdinfo_save_filename = "BDINFO." + bdinfo_path + ".txt"
    if os.path.exists(os.path.join(bdinfo_save_path, bdinfo_save_filename)):
        print(f"BDInfo file already found, using {bdinfo_path}")
        bdinfo_path = os.path.join(bdinfo_save_path, bdinfo_save_filename)
    else:
        if BDINFO_PATH is None:
            raise RuntimeError(
                f"BDInfo path must be defined int yout config file to be used..."
            )
        bdinfo_temp_dir = os.path.join(
            tempfile.gettempdir(), Path(bdinfo_file).name + ".UNIT3D.UPLOADER"
        )
        try:
            os.mkdir(bdinfo_temp_dir)
        except:
            pass
        subprocess.run(
            mono
            + [os.path.join(BDINFO_PATH, "BDInfo.exe")]
            + bdinfow
            + [bdinfo_file, bdinfo_temp_dir]
        )
        old_path = [
            os.path.join(bdinfo_temp_dir, f) for f in os.listdir(bdinfo_temp_dir)
        ][0]
        new_path = os.path.join(bdinfo_save_path, bdinfo_save_filename)
        copy(old_path, new_path)
        os.remove(old_path)
        os.rmdir(bdinfo_temp_dir)
        bdinfo_path = new_path
    with open(bdinfo_path, "r", encoding="utf-8") as f:
        bdinfo_report = f.read()
    bdinfo["full"] = bdinfo_report
    bdinfo["main"] = re.search(
        r"DISC INFO:\s+([\s\S]+?)\s+STREAM DIAGNOSTICS:", bdinfo_report
    ).group(1)
    bdinfo["summary"] = re.search(
        r"QUICK SUMMARY:\s+([\s\S]*?)\s+(\*\*\*\*\*\*\*\*\*\*\*\*\*|$)", bdinfo_report
    ).group(1)
    return bdinfo


def num_file(folder):
    # returns the number of files and the size, no need to go through them twice
    count, total_size = 0, 0
    if Path(folder).is_file():
        return 1, os.path.getsize(folder)
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        if Path(path).is_file():
            count += 1
            total_size += os.path.getsize(path)
        else:
            newCount, newSize = num_file(path)
            count += newCount
            total_size += newSize
    return count, total_size


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


def is_dupe(path, num_files):
    if Path(path).is_dir():
        file_name = Path(next(iter(sorted(Path(path).glob("*/")))).as_posix()).name
    else:
        file_name = Path(path).name
    url = f"{BASE_API_ENDPOINT}/torrents/filter?file_name={file_name}&api_token={API_TOKEN}"

    payload = {}
    headers = {"User-Agent": "UNIT3D API Uploader v{constants.UNIT3D_VERSION}"}

    response = requests.request("GET", url, headers=headers, data=payload)
    results = response.json()
    if results.get("data"):
        for release in results["data"]:
            try:
                if (
                    release["attributes"]["num_file"] == num_files
                    or release["attributes"]["num_file"] > num_files
                ):
                    return True
            except:
                if release["attributes"]["size"].replace(" ", "") == sizeof_fmt(
                    release_size
                ):
                    return True
    return False


def get_keywords(tmdb_info=None):
    keywords = []
    try:
        tmdb_keywords = tmdb_info.keywords()
        if tmdb_keywords.get("keywords") is not None:
            keywords = [
                f"{keyword['name'].replace(',','')}"
                for keyword in tmdb_keywords.get("keywords")
            ]
        elif tmdb_keywords.get("results") is not None:
            keywords = [
                f"{keyword['name'].replace(',','')}"
                for keyword in tmdb_keywords.get("results")
            ]
        return ",".join(keywords)
    except:
        return ""


def single_file_folder(path):
    file_list = sorted(Path(path).rglob("*"))
    files, first_media_file = [], None
    non_sample_files = []
    for file in file_list:
        if not file.is_dir():
            # We only care about non-directories
            extension = file.suffix.lower().strip()
            filename = file.as_posix()
            if extension == ".nfo" and args.nfo is None:
                args.nfo = filename
            if extension not in [
                ".nfo",
                ".srt",
                ".rar",
                ".txt",
                ".jpg",
                ".png",
                ".jpeg",
                ".sfv",
            ]:
                files += [file]
                if "sample" not in filename.lower():
                    non_sample_files += [file]
            elif extension in [".mkv", ".ts", ".m2ts", ".mp4", ".mov"]:
                first_media_file = file
    # if at least one file doesn't have sample in the name use that path list.
    if len(non_sample_files) != 0:
        files = non_sample_files
    # Verify the first media file wasn't removed from the file list, if it was fine new one.
    if first_media_file not in files:
        for file in files:
            extension = file.suffix.lower().strip()
            if extension in [".mkv", ".ts", ".m2ts", ".mp4", ".mov"]:
                first_media_file = file
                break
            if str(file.as_posix()).endswith("FEATURE_1.EVO"):
                first_media_file = file
                break
    return files, first_media_file.as_posix()


def cleanup():
    global UNIT3D_IMAGE, torrent_path
    for ss in UNIT3D_IMAGE.get_images():
        if os.path.isfile(ss["path"]):
            os.remove(ss["path"])
    if not args.debug and os.path.isfile(torrent_path):
        os.remove(torrent_path)


def get_hddvd_evo(path):
    first_evo = ".EVO"
    try:
        _, first_evo = single_file_folder(path)
    except:
        all_files = [
            os.path.join(os.path.abspath(path), rel)
            for rel in filter(lambda x: x.endswith(".EVO"), os.listdir(path))
        ]
        all_files.sort(key=lambda f: os.stat(f).st_size, reverse=True)
        first_evo = all_files[0]
    return first_evo


# Lets go
path_list = args.file_list
read_defaults()
bdinfo_files, dvd_files, hddvd_files = [], [], []
for path in path_list:
    num_files, release_size = num_file(path)
    if Path(path).is_dir() or re.search("\.iso", path, flags=re.IGNORECASE):
        bdinfo_files, dvd_files, hddvd_files = disc_info(path)
        if len(bdinfo_files) > 0:
            # Get unique, just because sometimes
            bdinfo_files = list(set(bdinfo_files))
            bdinfo_files.sort()
            prepend = "" if len(bdinfo_files) == 1 else Path(path).name
            media_info = [getbdinfo(bd, prepend) for bd in bdinfo_files]
            args.type_id = constants.TYPES["Full Disc"]
        elif len(dvd_files) > 0:
            media_info = dvd_files[0]["vob_mediainfo"]
            args.type_id = constants.TYPES["Full Disc"]
            args.sd = "1"
        elif len(hddvd_files) > 0:
            first_media_file = get_hddvd_evo(hddvd_files[0])
            if not os.path.exists(first_media_file):
                raise RuntimeError(
                    f"Couldn't find HD DVD FEATURE file... please report...\n{first_media_file}"
                )
            media_info = pymediainfo.parse(first_media_file)
            args.type_id = constants.TYPES["Full Disc"]
            is_hddvd = True
        else:
            # non-disc folder.
            allowed_files, first_media_file = single_file_folder(path)
            if len(allowed_files) == 1:
                # Only contained a single valid file.
                print(f'Folder given: "{path}" only had one non-sample media file...')
                if args.use_torrent:
                    print("Torrent file passed... Can't change directory...")
                else:
                    path = allowed_files[0].as_posix()
                    print(f'Switching path to "{path}"')
                media_info = pymediainfo.parse(path)
            else:
                media_info = pymediainfo.parse(first_media_file)
    else:
        media_info = pymediainfo.parse(path)
    media_tmdb, media_imdb, media_tvdb = get_mediainfo_ids(media_info)
    if media_tmdb is not None and "AUTO-DETECT" in str(args.tmdb):
        args.tmdb = media_tmdb
    if media_imdb is not None and "AUTO-DETECT" in str(args.imdb):
        args.imdb = media_imdb
    if media_tvdb is not None and "AUTO-DETECT" in str(args.tvdb):
        args.tvdb = media_tvdb

    if is_dupe(path, num_files):
        if args.debug:
            print(f"\n{Path(path).name} Is a Dupe, debug mode enabled, continuing...\n")
        elif args.skip_dupe_check:
            print(
                f"\n{Path(path).name} Is a Dupe,\n\t--skip-dupe-check passed, continuing...\n"
            )
        else:
            sys.exit(f"{Path(path).name} Is a Dupe, Aborting.")

    guessit_info = guessit(Path(path).name)

    if args.type_id == constants.TYPES["Remux"]:
        try:
            guessit_info["other"] = guessit_info["other"] + " Remux"
        except:
            guessit_info["other"] = "Remux"

    if args.type_id is None:
        args.type_id = constants.TYPES["Encode"]

    if args.name is None:
        tmdb_title, tmdb_year, guessit_info = preprocessing(path, guessit_info)
    else:
        # Try using user passed name for guessit first, if it fails try the filename.
        try:
            guessit_info_tmp = guessit(args.name.replace(" ", "."))
            tmdb_title, tmdb_year, guessit_info = preprocessing(path, guessit_info_tmp)
        except:
            tmdb_title, tmdb_year, guessit_info = preprocessing(path, guessit_info)
    try:
        guessit_info["release_group"] = re.sub(
            r"(FLAC\d\.\d|\d\.\d|Atmos|X|DoVi|DVSL)( *- *)(.*)",
            r"\3",
            guessit_info.get("release_group"),
        )
        if re.fullmatch(
            "(FLAC\d\.\d|\d\.\d|Atmos|X|DoVi|DVSL|\d*x?DVD\d*)",
            guessit_info.get("release_group"),
        ):
            guessit_info["release_group"] = None
        elif guessit_info.get("release_group") in constants.EXCLUDED_GROUPS:
            guessit_info["release_group"] = None
    except:
        guessit_info["release_group"] = None

    # Banned group check, uncommented it with more people using it
    if guessit_info.get("release_group") is not None and (
        guessit_info.get("release_group") in constants.BANNED_ALL
        or (
            guessit_info.get("release_group") in constants.BANNED_ALLOWED_RAW
            and args.type_id
            not in [constants.TYPES["Full Disc"], constants.TYPES["WEB-DL"]]
        )
    ):
        raise RuntimeError(
            f"{guessit_info.get('release_group')} is a banned group. Aborting."
        )

    if tmdb_title != "":
        guessit_info["title"] = tmdb_title
    if tmdb_year != "":
        guessit_info["year"] = tmdb_year

    torrent_name2, release_name_data = get_torrent_name(
        guessit_info, media_info
    )  # torrent_name needs more testing
    if args.name is None:
        args.name = torrent_name2
        api_files_data["title_override"] = False
    set_image_host()
    UNIT3D_IMAGE.set_gallery_name(args.name)
    api_files_data["title"] = args.name
    print(f'Using Release Name: "{args.name}"\n')

    if args.debug:
        print(f"Debug mode... Skipping creating torrent...\n")
        torrent_path = args.config_path
    else:
        torrent_path = str(create_torrent(path, args.overwrite))
        print(f"{torrent_path}\n")

    if args.type_id == constants.TYPES["Full Disc"] and type(media_info) == list:
        screenshot_bbcode = ""
        if num_screens > 0 and not api_files_data.get("3D"):
            mpls_total_duration = 0
            screens_taken, current_m2ts = 0, 0
            m2ts_files = get_m2ts_files(media_info[0]["main"])
            # Fix m2ts filenames/paths, fix duration, and add cumulative duration.
            for i in range(len(m2ts_files)):
                m2ts = f"{bdinfo_files[0]}/STREAM/{m2ts_files[i]['m2ts']}"
                m2ts_dur = m2ts_files[i]["duration"]
                if not Path(m2ts).exists():
                    m2ts_files[i]["m2ts"] = m2ts[:-4] + "m2ts"
                else:
                    m2ts_files[i]["m2ts"] = m2ts
                m2ts_duration_seconds = time_to_sec(m2ts_dur)
                mpls_total_duration += m2ts_duration_seconds
                m2ts_files[i]["cum_duration"] = mpls_total_duration
                m2ts_files[i]["duration"] = m2ts_duration_seconds
                m2ts_files[i]["num_screens"] = 0
            # Used to spread out the screenshots, the +2 is so it aims more towards front.
            # The current start is halfway into the spread.
            screen_spread = round(mpls_total_duration / (num_screens + 2))
            current_time = screen_spread / 2
            # See how many screens need taken in each m2ts.
            while screens_taken < num_screens:
                if current_time < m2ts_files[current_m2ts]["cum_duration"]:
                    m2ts_files[current_m2ts]["num_screens"] += 1
                    current_time += screen_spread
                    screens_taken += 1
                else:
                    current_m2ts += 1
            # Upload screens and generate bbcode.
            for m2ts in m2ts_files:
                if m2ts["num_screens"] != 0:
                    length_override = m2ts["duration"]
                    upload_screenshots(
                        m2ts["m2ts"],
                        str(m2ts["num_screens"]),
                        length_override=length_override,
                    )
        bdinfo_count, bbcode = 0, ""
        new_media_info = []
        for bd in media_info:
            bdinfo_count += 1
            main, full, quick_summary = bd["full"], bd["main"], bd["summary"]
            bdinfo_name = get_bdinfo_name(quick_summary)
            bdinfo_name = " / " + bdinfo_name if bdinfo_name else ""
            bdinfo_type = get_bdinfo_type(quick_summary)
            new_media_info += [
                {
                    "main": main,
                    "full": full,
                    "summary": quick_summary,
                    "type": bdinfo_type,
                }
            ]
            if bdinfo_count != 1:
                bbcode = f"{bbcode}<br>[spoiler=Disc {bdinfo_count}{bdinfo_name}]<br>[code]{quick_summary}<br>[/code]<br>[/spoiler]"
        bbcode = (
            f"{bbcode}<br>[center]<br>{UNIT3D_IMAGE.generate_bbcode()}<br>[/center]"
        )
        if new_media_info != []:
            media_info = new_media_info
    elif args.type_id == constants.TYPES["Full Disc"] and len(dvd_files) > 0:
        screen_bbcode, bbcode = "", ""
        if num_screens > 0:
            screen_vob = int(num_screens // len(dvd_files[0]["vob_list"]))
            # The screens missing from rounding
            missing_screens = num_screens - screen_vob * len(dvd_files[0]["vob_list"])
            for vob in dvd_files[0]["vob_list"]:
                take_screens_num = screen_vob
                if missing_screens > 0:
                    take_screens_num = screen_vob + 1
                    missing_screens -= 1
                try:
                    print(f"Taking {take_screens_num} in {vob}")
                    upload_screenshots(vob, take_screens_num)
                except:
                    pass
            screen_bbcode = f"[center]<br>{UNIT3D_IMAGE.generate_bbcode()}<br>[/center]"

        dvd_number = 0
        for dvd in dvd_files:
            dvd_number += 1
            ifo_mediainfo_text = get_mediainfo_text(dvd["ifo_file"], media_info)
            vob_mediainfo_text = get_mediainfo_text(dvd["vob_file"], media_info)
            try:
                folder_name = (
                    Path(os.path.abspath(dvd["vob_file"]))
                    .parent.parent.name.replace("'", "")
                    .replace('"', "")
                )
                folder_name = f"Disc {dvd_number} - {folder_name}"
                vob_name = "/ " + Path(dvd["vob_file"]).name.replace("'", "").replace(
                    '"', ""
                )
                ifo_name = "/ " + Path(dvd["ifo_file"]).name.replace("'", "").replace(
                    '"', ""
                )
            except:
                folder_name, vob_name, ifo_name = None, "VOB", "IFO"
            if dvd_number == 1:
                bbcode = f"[spoiler=VOB Mediainfo][code]<br>{vob_mediainfo_text}<br>[/code][/spoiler]"
            else:
                if folder_name:
                    bbcode = f"{bbcode}<br>{folder_name}:"
                bbcode = f"{bbcode}<br>[spoiler=Disc {dvd_number} {ifo_name}][code]<br>{ifo_mediainfo_text}[/code][/spoiler]"
                bbcode = f"{bbcode} [spoiler=Disc {dvd_number} {vob_name}][code]<br>{vob_mediainfo_text}[/code][/spoiler]"
        bbcode = f"{bbcode}<br><br>{screen_bbcode}"

    else:
        try:
            upload_screenshots(first_media_file, num_screens)
            bbcode = UNIT3D_IMAGE.generate_bbcode()
        except:
            upload_screenshots(path, num_screens)
            bbcode = UNIT3D_IMAGE.generate_bbcode()
        bbcode = f"[center]<br>{bbcode}<br>[/center]"

    try:
        bbcode
    except:
        description = f"{args.description}"
    else:
        if len(args.description) == 0:
            description = f"{bbcode}"
        else:
            description = f"{args.description}<br><br>{bbcode}"
    description = f"{description}<br><br>[center]<br>[img=35]https://blutopia.xyz/favicon.ico[/img] [b]Uploaded Using [url=https://github.com/HDInnovations/UNIT3D]UNIT3D[/url] Auto Uploader[/b] [img=35]https://blutopia.xyz/favicon.ico[/img]<br>[/center]"

    # Set more api_files_data
    api_files_data["video"] = {
        "codec": release_name_data.get("video_codec"),
        "resolution": f"{release_name_data.get('resolution')}{release_name_data.get('scanType','p')[0].lower()}",
        "dynamic": release_name_data.get("dynamic_range", "SDR"),
    }
    api_files_data["audio"] = {
        "codec": release_name_data.get("audio_codec"),
        "channels": release_name_data.get("audio_channels"),
    }
    api_files_data["source"] = release_name_data.get("source")
    api_files_data["streaming_service"] = release_name_data.get("streaming_service", "")
    mediainfo_text, bdinfo_text = "", ""
    if args.type_id != constants.TYPES["Full Disc"] or is_hddvd:
        api_files_data["extension"] = get_extension(media_info)
        try:
            mediainfo_text = get_mediainfo_text(first_media_file, media_info)
        except:
            mediainfo_text = get_mediainfo_text(path, media_info)
        api_files_data["mediainfo"] = {"object": media_info, "text": mediainfo_text}
    elif args.type_id == constants.TYPES["Full Disc"] and len(dvd_files) > 0:
        mediainfo_text = get_mediainfo_text(dvd_files[0]["ifo_file"], media_info)
        api_files_data["mediainfo"] = {
            "object": dvd_files[0]["ifo_mediainfo"],
            "text": mediainfo_text,
        }
    else:
        api_files_data["bdinfo"] = media_info
        bdinfo_text = api_files_data["bdinfo"][0]["summary"]
    api_files_data["type"] = constants.TYPES[args.type_id]
    api_files_data["category"] = constants.CATEGORIES[args.category_id]
    api_files_data["title_override"] = True
    api_files_data["internal"] = True if args.internal == "1" else False
    api_files_data["sticky"] = True if args.sticky == "1" else False
    api_files_data["free"] = True if args.free == "1" else False
    api_files_data["featured"] = True if args.featured == "1" else False
    api_files_data["doubleup"] = True if args.doubleup == "1" else False
    api_files_data["anon"] = True if args.anonymous == "1" else False
    api_files_data["api"] = API_TOKEN
    api_files_data["description"] = description
    api_files_data["screenshots"] = UNIT3D_IMAGE.get_images()
    api_files_data["size"] = release_size
    api_files_data["personal"] = args.personal
    personal = "1" if args.personal else "0"

    # data to be sent to api
    torrent_file = open(torrent_path, "rb")
    if args.nfo is not None and Path(args.nfo).exists():
        if os.path.getsize(args.nfo) > 12288:
            print(
                f'nfo: "{args.nfo}" ({sizeof_fmt(os.path.getsize(args.nfo))}) was bigger than 12KiB...'
            )
            print("No nfo is being used.")
            args.nfo, nfo_file = None, ""
        else:
            nfo_file = open(args.nfo, "rb")
    else:
        # Set path to None and file to the empty string
        args.nfo, nfo_file = None, ""

    import_file = os.path.join(constants.SCRIPT_PATH, "UNIT3D_Tackers")
    f, filename, module_description = imp.find_module(args.tracker, [import_file])
    UNIT3D = imp.load_module(args.tracker, f, filename, module_description)
    api_torrent_file = {"path": torrent_path, "file": torrent_file}
    api_nfo_file = {"path": args.nfo, "file": nfo_file}
    unit3d_tracker = UNIT3D.Tracker(api_files_data, api_torrent_file, args.debug)
    files = unit3d_tracker.get_files()
    unit3d_tracker.BASE_API_ENDPOINT = BASE_API_ENDPOINT
    # Print the object, shoule look similar to the BLU one.
    print(unit3d_tracker)

    if args.debug:
        # Exit instead of sending data
        cleanup()
        sys.exit("Debug Mode...  Aborting final upload...")

    r = unit3d_tracker.upload()
    try:
        results = r.json()
        print(results)
        unit3d_tracker.set_comment(results, torrent_path)
    except:
        print(r.status_code)
        print(r.text)

    download_dir = Path(os.path.abspath(path)).parent.as_posix()
    if args.client == "rtorrent":
        subprocess.call([chtor_bin, "-H", Path(path).as_posix(), torrent_path])
        subprocess.call(
            [
                rtxmlrpc_bin,
                "load.start",
                "",
                torrent_path,
                "d.priority.set=3",
                f"d.custom1.set={torrent_source}",
                f'd.directory.set="{download_dir}"',
            ]
        )
    elif args.client == "watch":
        watch_torrent_path = os.path.join(WATCH_FOLDER, Path(torrent_path).name)
        copy(torrent_path, watch_torrent_path)
    elif args.client == "qbit":
        torrent_file = open(torrent_path, "rb")  # open the file again for qbit.
        # We open again in case .torrent already existed.
        qbittorrent(download_dir, torrent_file)
    else:
        print(
            "No watch folder defined and chtor/rtxmlrpc aren't set, moving .torrent to working directory..."
        )
        new_torrent_path = os.path.join(os.getcwd(), Path(torrent_path).name)
        copy(torrent_path, new_torrent_path)

    try:
        torrent_file.close()
    except:
        pass  # Verify the file is closed
    cleanup()
