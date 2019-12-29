# Mp3ToSpotify
As the name implies, it's a quickly thrown together tool to help you add your collection of mp3s to your Spotify library.

##### Warning: It's by no means perfect. 
Expect many songs to not be found either due to the song not being on spotify or your filenames not accurately reflecting the song in Spotify. It may also add incorrect tracks for the same reasons.

But it's still useful. It can save a lot of time if you have a large music library and want to port all of it to spotify's cloud service.

Before you even consider using this script, know that [you can also play mp3 files with Spotify directly](https://support.spotify.com/us/using_spotify/features/listen-to-local-files/).


### How it works
The application will:
1. Scan a folder you provide (and it's subdirectories) for mp3 files.
2. Attempt to extract metadata from each song or use it's filename to search Spotify
3. When there is no perfect match, you will be prompted to select the correct song.
3. Add the correct track to your spotify likes.
4. Export the status of each mp3 to a log file to know which files have/have not been processed.
5. Optionally copy all failed tracks to another folder for manual review.

### Instuctions:
1. [Install Python3](https://www.python.org/downloads/)
2. Install the dependencies ([spotipy](https://github.com/plamere/spotipy) and [eyeD3](https://github.com/nicfit/eyed3))
```
pip3 install spotipy
pip3 install eyeD3
```
3. Download the script (or just download`Mp3ToSpotify.py` from GitHub manually)
```
git clone https://github.com/NotCoffee418/Mp3ToSpotify.git
cd Mp3ToSpotify
```
4. Run the script.
```
python3 Mp3ToSpotify.py
```
5. Answer the questions let the script do it's thing.
