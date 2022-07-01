"""
This is to be used alongside the UNIT3D auto uploader.
You can specify how the "files" are sent to the tracker.
This means you can change the title, categories, etc...

You must implement the "process" function.

Implementing the "__str__" function is recremended as well.
   This is used to print before  uploading so you can see
   what is being uploaded.
The rest can stay the same, add more as needed,
   the script will create the object and then call "get_files".
   It will add the torrent file, under "torrent".
"""

import constants
import torf
import requests
import re


class Tracker:
    # Set the name of the tracker this is for.
    tracker = "UNIT3D Nex-Gen Torrent Tracker"
    headers = {"User-Agent": "UNIT3D API Uploader v{constants.VERSION}"}

    def __init__(self, data={}, torrent_file={"path": "", "file": None}, debug=False):
        self.data = data  # Backup of data
        # Variables you can use, for determining the files.
        self.files = {}
        self.torrent = torrent_file
        self.screenshots = data.get("screenshots", [])
        self.size = data.get("size", 0)
        # Some tracker specific flags
        self.api_token = data.get("api", "")
        self.internal = data.get("internal", False)
        self.personal = data.get("personal", False)
        self.anon = data.get("anon", False)
        self.featured = data.get("featured", False)
        self.free = data.get("free", False)
        self.doubleup = data.get("doubleup", False)
        self.sticky = data.get("sticky", False)
        # Database identifiers
        self.imdb = data.get("imdb", None)  # the IMDb object
        self.tmdb = data.get(
            "tmdb", None
        )  # The TMDb object, most use cases you will need to call the .info()
        self.tvdb = data.get(
            "tvdb", {"id": None}
        )  # Currently just a dictionary with the id.
        self.mal = data.get(
            "mal", {"id": None, "romaji": "", "english": "", "native": ""}
        )
        self.igdb = data.get("igdb", None)
        # Name also has tv info, 'season': #, 'episode': #, 'episode_title': title
        # They are only there when applicable
        self.name = data.get(
            "name", {"name": "", "aka": "", "romanized": "", "romanized_aka": ""}
        )
        # Info about the file being uploaded
        self.extension = data.get("extension", None)
        self.video = data.get(
            "video", {"codec": "", "resolution": "1080p", "dynamic": "SDR"}
        )
        self.audio = data.get("audio", {"codec": "", "channels": 0, "atmos": False})
        self.mediainfo = data.get(
            "mediainfo", {"text": "", "object": None}
        )  # Text and Object so if you want to parse it again
        self.bdinfo = data.get(
            "bdinfo", []
        )  # List of the BDinfo, bdinfo[0] has 'full', 'main', and 'summary'.
        self.source = data.get("source", "")  # HDTV/Blu-ray/UHD Blu-ray
        self.region = data.get("region", "")
        self.streaming_service = data.get("streaming_service", "")
        self.type = data.get("type", "Encode")  # Default is encode.
        # Info about the upload
        self.keywords = data.get(
            "keywords", ""
        )  # Will include keywords from TMDb.  Comma separated.
        self.description = data.get(
            "description", ""
        )  # Will be bbcode, so you can transform the bbcode if needed.
        self.description_arg = data.get(
            "description_arg", ""
        )  # The argument passed, so you can use that.
        self.category = data.get(
            "category", "Movie"
        )  # Default is movie just to be safe.
        self.group = data.get("group", None)  # Release group.
        self.title = data.get("title", "")  # The default name determined by the script.
        self.title_override = data.get(
            "title_override", False
        )  # True when --name is passed.
        self.repack_count = data.get("repack_count", 0)
        self.proper_count = data.get("proper_count", 0)
        self.debug = debug
        self.set_default_files()  # Here to set defaults

    def __repr__(self):
        # Currently this will return everything and just remove the mediainfo.
        mediainfo_removed = self.files
        mediainfo_removed.pop("mediainfo")
        return str(mediainfo_removed)

    def __str__(self):
        repr_string = ""
        repr_string += f"Name: \"{self.files.get('name')[1]}\"\n\n"
        repr_string += (
            f"IMDb: {self.files.get('imdb')[1]}\tTMDb: {self.files.get('tmdb')[1]}\t"
        )
        repr_string += (
            f"TVDb: {self.files.get('tvdb')[1]}\tMalID: {self.files.get('mal')[1]}\n"
        )
        repr_string += f"Personal: {self.files.get('personal_release')[1]}\tInternal: {self.files.get('internal')[1]}\n"
        repr_string += f"Keywords: {self.files.get('keywords')[1]}\n\n"
        repr_string += (
            f"Category: {constants.CATEGORIES[self.files.get('category_id')[1]]}\t"
        )
        repr_string += (
            f"Type: {constants.RESOLUTIONS[self.files.get('resolution_id')[1]]} "
        )
        repr_string += f"{constants.TYPES[self.files.get('type_id')[1]]}\n"
        repr_string += f"Free:{self.files.get('free')[1]}\t"
        repr_string += f"Anon: {self.files.get('anonymous')[1]}\t"
        repr_string += f"Stream: {self.files.get('stream')[1]}\n"
        repr_string += f"Featured: {self.files.get('featured')[1]}\tDouble: {self.files.get('doubleup')[1]}\t"
        repr_string += f"Sticky: {self.files.get('sticky')[1]}\n\n"
        repr_string += f"Description: {self.files.get('description')[1]}"
        return str(repr_string)

    def get_files(self):
        return self.files

    def set_default_files(self):
        stream = "0"
        sd = "1" if int(self.video.get("resolution")[:-1]) < 720 else "0"

        resolution_id = {
            "8640p": "10",
            "4320p": "11",
            "2160p": "1",
            "1080p": "2",
            "1080i": "3",
            "720p": "5",
            "576p": "6",
            "576i": "7",
            "480p": "8",
            "480i": "9",
        }.get(self.video.get("resolution"), "10")
        type_id = {
            "Full Disc": "1",
            "Remux": "3",
            "WEB-DL": "4",
            "WEBRip": "5",
            "HDTV": "6",
            "Encode": "12",
        }.get(self.type, "0")
        category_id = {"Movie": "1", "TV": "2", "Fanres": "3"}.get(self.category, "0")

        imdb_id = "0" if self.imdb is None else self.imdb.getID()
        tmdb_id = "0" if self.tmdb is None else self.tmdb.id
        tvdb_id = "0" if self.tvdb.get("id") is None else self.tvdb.get("id")
        mal_id = "0" if self.mal.get("id") is None else self.mal.get("id")
        igdb_id = "0" if self.igdb is None else self.igdb

        internal = "1" if self.internal else "0"
        personal = "1" if self.personal else "0"
        featured = "1" if self.featured else "0"
        anonymous = "1" if self.anon else "0"
        sticky = "1" if self.sticky else "0"
        free = "1" if self.free else "0"
        doubleup = "1" if self.doubleup else "0"
        keywords = self.keywords.replace(",", ", ").replace("  ", " ")

        self.files = {
            "api_token": (None, self.api_token),
            "torrent": (self.torrent.get("path"), self.torrent.get("file")),
            "name": (None, self.title),
            "description": (None, self.description),
            "keywords": (None, keywords),
            "category_id": (None, category_id),
            "type_id": (None, type_id),
            "resolution_id": (None, resolution_id),
            "tmdb": (None, tmdb_id),
            "imdb": (None, imdb_id),
            "tvdb": (None, tvdb_id),
            "mal": (None, mal_id),
            "igdb": (None, igdb_id),
            "anonymous": (None, anonymous),
            "stream": (None, stream),
            "featured": (None, featured),
            "free": (None, free),
            "doubleup": (None, doubleup),
            "internal": (None, internal),
            "sticky": (None, sticky),
            "sd": (None, sd),
            "personal_release": (None, personal),
        }
        if self.bdinfo not in ("", []):
            self.files["mediainfo"] = (None, "")
            self.files["bdinfo"] = (None, self.bdinfo[0]["summary"])
        else:
            self.files["mediainfo"] = (None, self.mediainfo.get("text"))
            self.files["bdinfo"] = (None, "")

    def clear_default_files(self):
        # This removes everything, use if the default is not how you need it at all.
        # Otherwise it is suggested to just remove/edit what you need.
        self.files = {}

    def fix_internal(self):
        if self.group in self.INTERNALS:
            self.files["internal"] = (None, "1")

    def get_endpoint(self, base_endpoint):
        return f"{base_endpoint}/torrents/upload"

    def process(self):
        print(f"\nProcessing API files for {self.tracker}...\n")
        pass

    def upload(self):
        endpoint = self.get_endpoint(self.BASE_API_ENDPOINT)
        headers = {"User-Agent": "UNIT3D API Uploader v{constants.UNIT3D_VERSION}"}
        return requests.post(url=endpoint, headers=headers, files=self.files)

    def set_comment(self, results=None, torrent_path=None):
        if results and torrent_path:
            t = torf.Torrent.read(torrent_path)
            torrent_regex = re.search(
                "(.*)(/download/)(\d*)(\..*)", results.get("data")
            )
            torrent_url = f"{torrent_regex.group(1)}s/{torrent_regex.group(3)}"
            t.comment = torrent_url
            t.write(torrent_path, overwrite=True)
