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

from UNIT3D_Tackers.DEFAULT import Tracker as UNIT3D_T


class Tracker(UNIT3D_T):
    # Set the name of the tracker this is for.
    tracker = "LegacyHD - Home of LEGi0N"
    INTERNALS = ["LEGi0N"]

    def __init__(self, data={}, torrent_file={"path": "", "file": None}, debug=False):
        UNIT3D_T.__init__(self, data, torrent_file, debug)
        self.process()

    def __str__(self):
        repr_string = ""
        repr_string += f"Name: \"{self.files.get('name')[1]}\"\n\n"
        repr_string += (
            f"IMDb: {self.files.get('imdb')[1]}\tTMDb: {self.files.get('tmdb')[1]}\t"
        )
        repr_string += (
            f"TVDb: {self.files.get('tvdb')[1]}\tMalID: {self.files.get('mal')[1]}\n"
        )
        repr_string += f"Keywords: {self.files.get('keywords')[1]}\n\n"
        repr_string += f"Category: {self.files.get('category_id')}\tFree:{self.files.get('free')[1]}\t"
        repr_string += f"Anon: {self.files.get('anonymous')[1]}\tInternal: {self.files.get('internal')[1]}\n"
        repr_string += f"Type: {self.files.get('type')[1]}\t"
        repr_string += f"Stream: {self.files.get('stream')[1]}\n"
        repr_string += f"Featured: {self.files.get('featured')[1]}\tDouble: {self.files.get('doubleup')[1]}\t"
        repr_string += f"Sticky: {self.files.get('sticky')[1]}\n\n"
        repr_string += f"Description: {self.files.get('description')[1]}"
        return str(repr_string)

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

        if self.tmdb.external_ids().get("imdb_id", None):
            imdb_id = self.tmdb.external_ids().get("imdb_id").replace("tt", "")
        else:
            imdb_id = "0" if self.imdb is None else str(self.imdb.getID())
        tmdb_id = "0" if self.tmdb is None else str(self.tmdb.id)
        tvdb_id = "0" if self.tvdb.get("id") is None else str(self.tvdb.get("id"))
        mal_id = "0" if self.mal.get("id") is None else str(self.mal.get("id"))

        internal = "1" if self.internal else "0"
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
            "anonymous": (None, anonymous),
            "stream": (None, stream),
            "featured": (None, featured),
            "free": (None, free),
            "doubleup": (None, doubleup),
            "internal": (None, internal),
            "sticky": (None, sticky),
            "sd": (None, sd),
            "mediainfo": (None, self.mediainfo.get("text")),
            "igdb": (None, "0"),
        }

    def process(self):
        UNIT3D_T.process(self)
        self.files.pop("resolution_id", None)
        self.convert_type()
        self.convert_category()
        self.files.pop("type_id", None)
        self.files["type"] = (None, self.type)
        self.files["category_id"] = (None, self.category)
        self.fix_internal()
        if self.debug:
            pass

    def fix_internal(self):
        if self.group in self.INTERNALS:
            self.files["internal"] = (None, "1")
        else:
            self.files["internal"] = (None, "0")

    def is_documentary(self):
        for genre in self.tmdb.info().get("genres", []):
            if genre.get("name", "") == "Documentary":
                return True
        return False

    def convert_category(self):
        if self.category == "TV":
            if self.mal.get("id", None):
                self.category = "9"
            elif self.name.get("episode"):
                # Single episode
                self.category = "2"
            else:
                self.category = "5"
        elif self.category == "Movie":
            if self.is_documentary():
                self.category = "8"
            else:
                self.category = "1"
        elif self.category == "Fanres":
            self.category = "3"

    def convert_type(self):
        if "Blu" in self.source and self.type == "Full Disc":
            if "2160p" == self.video.get("resolution", ""):
                self.type = "UHD-BD"
            elif self.size > 26843545600:
                self.type = "BD-50"
            else:
                self.type = "BD-25"
        elif self.type == "Remux":
            if "2160p" == self.video.get("resolution", ""):
                if "DV" in self.video.get("dynamic", ""):
                    self.type = "UHD - Remux With Dolby Vision"
                else:
                    self.type = "UHD-Remux"
            elif "1080" in self.video.get("resolution", ""):
                self.type = "BD-Remux"
            elif "720" in self.video.get("resolution", ""):
                self.type = "BD-Remux"
            else:
                self.type = "SD FULL DVD or Remux"
                self.files["sd"] = (None, "1")
        elif "WEB-DL" == self.type:
            if "2160p" == self.video.get("resolution", ""):
                self.type = "WEB-DL 2160p"
            elif "1080" in self.video.get("resolution", ""):
                self.type = "WEB-DL 1080p"
            else:
                self.type = "WEB-DL 720p"
        elif self.extension == "mp4":
            self.files["stream"] = (None, "1")
            if "1080" in self.video.get("resolution", ""):
                self.type = "MP4 - 1080p"
            elif "720p" == self.video.get("resolution", ""):
                self.type = "MP4 - 720p"
        elif self.video.get("codec", "") in ["H.265", "HEVC", "x265"]:
            if "2160p" == self.video.get("resolution", ""):
                self.type = "2160p x265 Encode"
            elif "1080" in self.video.get("resolution", ""):
                self.type = "1080p x265 Encode"
            else:
                self.type = "720p x265 Encode"
        elif self.video.get("codec", "") in ["H.264", "AVC", "x264"]:
            if "2160p" == self.video.get("resolution", ""):
                self.type = "2160p x264 Encode"
            elif "1080" in self.video.get("resolution", ""):
                self.type = "1080p x264 Encode"
            else:
                self.type = "720p x264 Encode"
        elif "HDTV" == self.type:
            self.type = "HDTV"
        else:
            raise RuntimeError("Unable to detect type, upload manually and report...")
