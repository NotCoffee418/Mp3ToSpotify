import sys
from os import listdir, path
import datetime
import spotipy
import spotipy.util as util
import eyed3

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
def log_line(line):
    f=open(logFilePath, "a+")
    f.write(line + "\r\n")
    f.close()

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
        add_to_spotify_library(searchResult['tracks']['items'][0]['id'])
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
        entry_str = (index + 1) + ") " + value['artists'][0]['name'] + " - " + value['name']
        if (len(value['albums']) > 0): # Add album name if available
            entry += " (Album: " + value['albums'][0]['name'] + ")"
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
        add_to_spotify_library(searchResult['tracks']['items'][uselectionId]['id'])
        songs_added.append(filepath)
        return True




def add_to_spotify_library(track_id):
    #todo
    print("debug: "+track_id)
    return None

###
# Import Script
###

mp3Dir = ""
includeSubdirectories = False

# Disclaimer
print("This tool will add mp3 files to your Spotify library.\r\n")
print("WARNING: This process is irreversable and may be unable to add all songs.\r\n")
print("")

# Input Data
## Get directory containing MP3s
firstPathAttempt = True
while (path.isdir(mp3Dir) == False):
    if (firstPathAttempt):
        firstPathAttempt = False
    else:
        print("The path you entered is not a valid directory.\r\n")
    mp3Dir = input("Enter the full path to the directory containing your MP3 files:\r\n")

## Ask to check subdirectories
includeSubdirectories = bool_input("Would you like to include subdirectories while searching for files?")

## Authenticate with spotify & get spotify handle
sp = spotify_authenticate()
