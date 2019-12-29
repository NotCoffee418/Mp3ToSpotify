import sys
from os import listdir, path, walk, makedirs
import datetime
import spotipy
import spotipy.util as util
import eyed3
from shutil import copyfile

spotify = spotipy.Spotify()

# Function to request bool inputs
def bool_input(queryString):
    result = None

    # Check until we get a y or n
    while (result == None):
        rStr = str.lower(input(queryString + " (y/n)\n"))
        if (rStr == "y"):
            result = True
        elif (rStr == "n"):
            result = False

    # Return boolean result
    return result

# Logger function. File is in the same directory as the script.
logFilePath = "Mp3ToSpotify-log-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".log"
def log_line(line, alsoPrint=False):
    f=open(logFilePath, "a+")
    f.write(line + "\r\n")
    f.close()
    if (alsoPrint):
        print(line + "\r\n")

# Authenticate the user with spotify
def spotify_authenticate():
    username=""
    while (username == ""):
        username=input("Please enter your Spotify username:\n")
    scope="user-library-read user-library-modify playlist-read-private playlist-modify-private user-read-private"
    auth_token = util.prompt_for_user_token(username,scope,client_id='05794919be674441824fcb3267a22437',client_secret='7014411cbff3403285415679b1dea145',redirect_uri='http://localhost:5932/')
    return spotipy.Spotify(auth=auth_token)


# Result data
songs_added = []
songs_skipped = []
songs_not_found = []
uncertain_skipall = False

# Attempts to find and add a song to spotify library
def process_mp3(sp, filepath):
    global uncertain_skipall, songs_added, songs_skipped, songs_not_found
    query = ""
    prompt_user_confirm = True # indicates if user should be prompted to confirm if multiple results
    basis = "unknown"

    # log
    log_line("Processing file: " + filepath)

    # Attempt to extract song info from metadata as it's usually more reliable
    mfile = eyed3.load(filepath)
    # Both artist and title are in metadata, don't prompt
    if (mfile.tag.artist != None and mfile.tag.title != None): 
        query = mfile.tag.artist + " - " + mfile.tag.title
        prompt_user_confirm = False
        basis = "artist and title metadata"
    # Judgement call based on my own library, will assume artist name is in the title tag
    elif (mfile.tag.title != None):
        query = mfile.tag.title
        basis = "title metadata only"
    # Rely on filename to extract artist and title, this will likely be messy
    else:
        fileNameNoExt = path.basename(path.splitext(filepath)[0])
        query = fileNameNoExt.replace("_", " ").replace("%20", " ")
        basis = "filename"
    
    # Search spotify
    log_line("Searching Spotify for \"" + query + "\" based on " + basis)
    searchResult = sp.search(q=query, limit=9, offset=0, type='track', market='from_token')

    # Determine what to do with search results
    sresults_found = len(searchResult['tracks']['items'])
    if (sresults_found == 0): # No results, log & move on
        log_line("Failed to find song: " + query)
        print("Couldn't find a spotify track for " + filepath + "\r\n")
        songs_not_found.append(filepath)
        return False
    elif (sresults_found == 1 or prompt_user_confirm == False): # Perfect or assume first, adding
        log_line("Found one match for song: " + query)
        add_to_spotify_library(sp, searchResult['tracks']['items'][0]['id'])
        songs_added.append(filepath)
        return True
    
    # implied else: Multiple results found and user should be prompted
    # Check if user propted to skip uncertain results
    if (uncertain_skipall):
        log_line("Found multiple results for song '" + query + "' - Skipping (skipall enabled)")
        songs_skipped.append(filepath)
        return False
    
    # Initiate manual selection
    print("\r\nFound multiple matches for '" + query + "' (" + filepath + ")\r\n")
    print("Please enter the correct number or write 'skipall' to skip files that require manual selection.\r\n")

    # Display choices (index+1 to reserve 0 for skip)
    for index, value in enumerate(searchResult['tracks']['items']):
        entry_str = str(index + 1) + ") " + value['artists'][0]['name'] + " - " + value['name']
        print(entry_str + "\r\n")
    print("0) (Skip this song)\r\n")

    # Handle user input
    selection_incomplete = True
    uselectionId = -1
    while (selection_incomplete):
        uselection = input("\r\nSelect number: ")
        
        # Handle skipall
        if (uselection == 'skipall'):
            uncertain_skipall = True
            print("Enabled skipall - Will no longer prompt ask about uncertain results")
            log_line("Enabled skipall")
            songs_skipped.append(filepath)
            return False
        
        # Attempt to parse to int and turn selection to track index (so -1)
        try:
            uselectionId = int(uselection) - 1

            # Handle manual skip
            if (uselectionId == -1):
                print("Skipped track.\r\n")
                songs_skipped.append(filepath)
                return False

            # verify that the input number is a valid index
            if (uselectionId >= len(searchResult['tracks']['items'])):
                raise ValueError("Selection is out of range")
        except:
            print("Invalid selection. Please enter the number of the correct track.\r\n")
            continue

        # Add selected track to library
        log_line("Manually selected track for " + filepath)
        add_to_spotify_library(sp, searchResult['tracks']['items'][uselectionId]['id'])
        songs_added.append(filepath)
        return True

# Checks if the track is already in saved tracks
user_saved_tracks = None
def is_duplicate(sp, track_id):
    global user_saved_tracks

    # Get current saved tracks from spotify if not done already
    if (user_saved_tracks == None):
        user_saved_tracks = get_currently_saved_tracks(sp)

    # Check if it's duplicate
    return (track_id in user_saved_tracks)

# This can be modified to add to specific playlists or do other things with the track
# Currently it only adds the song to liked songs (saved tracks)
def add_to_spotify_library(sp, track_id):
    global user_saved_tracks
    if (is_duplicate(sp, track_id)):
        log_line("Track was already in library, continuing...")
        return False

    # Add to saved tracks (likes)
    log_line("Adding track to Spotify: " + track_id)
    sp.current_user_saved_tracks_add([track_id])

    # Add to local saved tracks arr
    user_saved_tracks.append(track_id)
    return True

# Returns all track ID's that are currently liked on spotify
def get_currently_saved_tracks(sp):
        result = sp.current_user_saved_tracks()
        saved_tracks = []
        for item in result['items']:
            saved_tracks.append(item['track']['id'])
        return saved_tracks


###
# Import Script
###

mp3Dir = ""

# Disclaimer
print("This tool will add mp3 files to your Spotify library.\r\n")
print("WARNING: This process is irreversable and may be unable to add all songs or add incorrect songs to your Spotify library.\r\n")

# Input Data
## Get directory containing MP3s
firstPathAttempt = True
while (path.isdir(mp3Dir) == False):
    if (firstPathAttempt):
        firstPathAttempt = False
    else:
        print("The path you entered is not a valid directory.\r\n")
    mp3Dir = input("Enter the full path to the directory containing your MP3 files:\r\n")

## Authenticate with spotify & get spotify handle
sp = spotify_authenticate()

# Request & create backup (trackids to text file, one per line)
if (bool_input("Would you like to back up your current likes before proceeding (Recommended)?")):
    saved_trackids = get_currently_saved_tracks(sp)
    backupFilePath = "Mp3ToSpotify-backup-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
    f=open(backupFilePath, "a+")
    for track in saved_trackids:
        f.write(track + "\r\n")
    f.close()

# Find all eligible files
print("Scanning for valid mp3 files...\r\n")
mp3_files = []
for root, dirs, files in walk(mp3Dir):
    for file in files:
        if(file.endswith(".mp3")):
            fpath = path.join(root,file)
            mp3_files.append(fpath)
total_to_process = len(mp3_files)
print("Found " + str(total_to_process) + " mp3 files in this directory and it's subdirectories.\r\n\r\n")

# Final "are you sure" prompt
if (not bool_input("Ready to import songs. Are you sure you want to proceed?")):
    log_line("User closed application. Nothing was done.")
    sys.exit("Manually stopped")

# Process all MP3 files
for index, filepath in enumerate(mp3_files):
    print("Processed " + str(index + 1) + " of " + str(total_to_process) + " songs.\r\n")
    process_mp3(sp, filepath)

# Print/log results
log_line("\r\nAll songs have been processed.", True)
log_line("Added or duplicate: " + str(len(songs_added)), True)
log_line("Failed to find: " + str(len(songs_not_found)), True)
log_line("Skipped: " + str(len(songs_not_found)), True)

log_line("\r\nFiles added to spotify library:")
for filepath in songs_added:
    log_line(filepath)

log_line("\r\nFiles we couldn't find in spotify:")
for filepath in songs_not_found:
    log_line(filepath)

log_line("\r\nFiles that were skipped:")
for filepath in songs_skipped:
    log_line(filepath)

# Copy skipped/missing files for manual review
if (bool_input("Would you like to copy missing and skipped files to your desktop for manual review?")):
    log_line("Copying files...", True)
    # Prepare directories
    copyIncompleteDir = path.expanduser("~/Desktop/Mp3ToSpotify/") # works cross-platform
    copySkippedDir = copyIncompleteDir + "/skipped/"
    copyNotFoundDir = copyIncompleteDir + "/notfound/"
    if not path.exists(copyIncompleteDir):
        makedirs(copyIncompleteDir)
    if not path.exists(copySkippedDir):
        makedirs(copySkippedDir)
    if not path.exists(copyNotFoundDir):
        makedirs(copyNotFoundDir)

    # Copy skipped files
    for filepath in songs_skipped:
        copyfile(filepath, path.join(copySkippedDir, path.basename(filepath)))

    # Copy notfound files
    for filepath in songs_not_found:
        copyfile(filepath, path.join(copyNotFoundDir, path.basename(filepath)))

# Done
input("Done! Press Enter to exit.")