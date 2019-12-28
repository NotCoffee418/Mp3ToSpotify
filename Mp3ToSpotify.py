from os import listdir, path
import sys
import datetime

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