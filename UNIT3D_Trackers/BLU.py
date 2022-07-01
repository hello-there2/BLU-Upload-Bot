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
    tracker = "Blutopia (BLU) - Home of UNIT3D"
    INTERNALS = ["BLURANiUM", "BLUTONiUM", "CultFilms™", "ISA", "PmP"]

    def __init__(self, data={}, torrent_file={"path": "", "file": None}, debug=False):
        UNIT3D_T.__init__(self, data, torrent_file, debug)
        self.process()

    def process(self):
        UNIT3D_T.process(self)
        keywords = self.keywords.replace(",", ", ").replace("  ", " ")
        self.files["keywords"] = (None, keywords)
        self.files["description"] = (None, self.description.replace("<br>", f"\r\n"))
        self.fix_internal()
