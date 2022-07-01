# BLU-Upload-Bot
Python Script That Upload Torrents Through BLU's API.

Prerequisites:
```
python 3.8
pip3
pyrocore
```

Installing Pyrocore (not under root account!):
```
mkdir -p ~/bin ~/.local
git clone "https://github.com/pyroscope/pyrocore.git" ~/.local/pyroscope

~/.local/pyroscope/update-to-head.sh

# Check success
pyroadmin --version
```

Install Requiurements: 
```
pip3 install -r requirements.txt
```
Config Setup:
```
Copy DEFAULT.ini to your home directory "$HOME"
Name it ".BLU_Auto.ini" and make required changes.
```

Usage Example: 
```
python3 autoup.py "/home/username/torrents/rtorrent/Crash.1996.2160p.UHD.BluRay.Remux.HDR.HEVC.DTS-HD.MA.5.1-PmP.mkv"
```

Help Page: 
```
usage: autoup.py [-h] [-V] [--anonymous] [--sd] [--internal] [--streamop] [--description DESCRIPTION] [--name NAME]
                 [--category CATEGORY_ID] [--type TYPE_ID] [--tmdb TMDB] [--tvdb TVDB] [--imdb IMDB] [--mal MAL]
                 [--igdb IGDB] [--overwrite-existing-torrent] [--featured] [--free] [--doubleup] [--sticky]
                 [--group GROUP] [--nogroup] [--audio AUDIO] [--channels CHANNELS] [--video VIDEO]
                 [--dynamic-range DYNAMIC_RANGE] [--resolution RESOLUTION] [--cut CUT] [--edition EDITION]
                 [--region REGION] [--repack REPACK] [--proper PROPER] [--hybrid] [--episode-title EPISODE_TITLE]
                 [--ptp PTP] [--hdb HDB] [--allow-no-imdb] [--allow-no-tmdb] [--config CONFIG_PATH] [--debug]
                 [--keywords KEYWORDS] [--append-keywords] [--tracker TRACKER] [--client CLIENT] [--nfo NFO]
                 [--personal] [--screens SCREENS] [--screen-kill MAX_WAIT] [--season SEASON] [--episode EPISODE]
                 release-path [release-path ...]

Upload torrents to UNIT3D based trackers through its API

positional arguments:
  release-path          file or directory containing the release

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program version
  --anonymous           Upload as anonymous
  --sd                  Upload is SD
  --internal            Upload is Internal
  --streamop            Upload is Stream Optimized
  --description DESCRIPTION
                        Torrent description
  --name NAME           Torrent name
  --category CATEGORY_ID
                        Upload category, name or ID work.
                        Movie   |TV     |Fanres
                        1       |2      |3
  --type TYPE_ID        Upload type, name or ID work.
                        Disc    |Remux  |Encode |WEB-DL |WEBRip |HDTV
                        1       |3      |12     |4      |5      |6
  --tmdb TMDB           TheMovieDb ID
  --tvdb TVDB           TVDb ID
  --imdb IMDB           IMDb ID
  --mal MAL             MAL ID
  --igdb IGDB           IGDB ID
  --overwrite-existing-torrent
                        overwrite-existing-torrent
  --featured            Upload is Featured
  --free                Upload is Freeleech
  --doubleup            Upload is Double Upload
  --sticky              Upload is Stickied
  --group GROUP         Override group detection
  --nogroup             Remove Detected group
  --audio AUDIO         Audio base codec, e.x. "TrueHD", "Atmos" defaults to "TrueHD Atmos". Requires the use of
                        --channels
  --channels CHANNELS   Audio channels, e.x. "5.1". Can be used without --audio, but is suggested to be used with
  --video VIDEO         Video codec
  --dynamic-range DYNAMIC_RANGE
                        Dynamic range, "DV HDR", "HDR10+", "HDR", "SDR", or others.
  --resolution RESOLUTION
                        Resolution, needs to be one of the following: 8640p, 4320p, 2160p, 1080p, 1080i, 720p, 576p,
                        576i, 480p, 480i, or Other
  --cut CUT             The cut of the movie/show, e.x. "Director's Cut", passing an empty string "" will remove any
                        cut detected
  --edition EDITION     The edition, e.x. "Remastered"
  --region REGION       The region (only applicable for full discs), e.x. "GBR"
  --repack REPACK       Repack number, 0 is none (removes it if detected), 1 is REPACK, 2 is REPACK2, etc.
  --proper PROPER       Proper number, 0 is none, 1 is PROPER, 2 is PROPER2, etc.
  --hybrid              When passed it is considered a Hybrid
  --episode-title EPISODE_TITLE
                        When passed on a TV show it adds the Episode title, 1 is to add the one the parser found,
                        anything else will used what is passed.
  --ptp PTP             Requires your PTP ApiUser and ApiKey to be set. Pass the PTP torrent ID to grab their bbcode.
                        *** (Not yet implemented) pass "auto" for automatic detection, which can be set in the config
                        file too. Pass a torrent ID to match that one directly.
  --hdb HDB             Requires your HDB credentials to be set. Passkey is suggested, as you can use 2fa with it, if
                        both are set passkey is used. pass "auto" for automatic detection, which can be set in the
                        config file too. Pass a torrent ID to match that one directly.
  --allow-no-imdb       When passed it will auto upload with IMDb 0 instead of erroring out in auto mode.
  --allow-no-tmdb       When passed it will auto upload with TMDb 0 instead of erroring out in auto mode.
  --config CONFIG_PATH  Config file path, used for when not in default location $HOME/.BLU_Auto.ini
  --debug               When passed it will run like normally, but not fully upload.
  --keywords KEYWORDS   Comma separated list of keywords.
  --append-keywords     When passed it will append thhe keywords given to the list from TMDb, default is overrite
                        them.
  --tracker TRACKER     Change which tracker to upload to.
  --client CLIENT       Specify which client you are using, default is rTorrent for Linux and Watch Folder for
                        Windows.
  --nfo NFO             The path to the nfo file. If not passed it will search for one.
  --personal            When passed it will mark this release as a "Personal Release"
  --screens SCREENS     Specify how many screens to take. Overrides the screens number in the config.
  --screen-kill MAX_WAIT
                        Number used for the max to wait on ffmpeg to take a screen, in seconds. Default 2 seconds.
  --season SEASON       Season number, values less than 0 mean remove it.
  --episode EPISODE     Episode number, values less than 0 mean remove it.
```
