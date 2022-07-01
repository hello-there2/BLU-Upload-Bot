# Classes to be used with other files.

# Imports
from tqdm import tqdm as tqdm
import argparse
from pathlib import Path


class ProgressBar(tqdm):
    def __init__(self, pieces_total=None, **kwargs):
        super().__init__(**kwargs)
        self.total = pieces_total

    def update_to(self, torrent, filepath, pieces_done, pieces_total):
        if pieces_total is not None:
            pass
        if self.desc is not "Hashing: {}".format(Path(filepath).name):
            self.set_description(
                desc="Hashing: {}".format(Path(filepath).name), refresh=True
            )
        self.update(n=1)


class SmartFormatter(argparse.HelpFormatter):
    def _split_lines(self, text, width):
        if text.startswith("R|"):
            return text[2:].splitlines()
        # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)
