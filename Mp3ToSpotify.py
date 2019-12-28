import sys
from os import listdir, path
import datetime
import spotipy
import spotipy.util as util

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

###
# Import Script
###

mp3Dir = ""
includeSubdirectories = False

# Disclaimer
print("This tool will add mp3 files to your Spotify library.")
print("WARNING: This process is irreversable and may be unable to add all songs.")
print("")

# Input Data
## Get directory containing MP3s
firstPathAttempt = True
while (path.isdir(mp3Dir) == False):
    if (firstPathAttempt):
        firstPathAttempt = False
    else:
        print("The path you entered is not a valid directory.")
    mp3Dir = input("Enter the full path to the directory containing your MP3 files:\n")

## Ask to check subdirectories
includeSubdirectories = bool_input("Would you like to include subdirectories while searching for files?")

## Authenticate with spotify & get spotify handle
sp = spotify_authenticate()