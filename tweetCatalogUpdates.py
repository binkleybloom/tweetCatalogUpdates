#################################
#
# Twitter munki-catalog change notification script
#
# Written by Tim Schutt - taschutt@syr.edu
#
# November, 2014
# Updates applied March, 2015
#
#################################

import os, plistlib, tweepy, datetime, sys, subprocess, shutil, shlex, hashlib

#========== Modify to match your environment ===========#

### munki repo root ###
munki_root = "/Volumes/munki-repo"  # munki repo root

### Twitter Consumer API key & token, and Access token & secret ###
ckey = ''
csecret = ''
atok = ''
asecret = ''

### Set armed to True to send tweets. Otherwise, tweet contents will be written
### to stout.

armed = False

#============ Do not modify below this line ============#

all_items_path = os.path.join(munki_root, 'catalogs','all')
script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
cached_file = str(script_path) + '/cached.plist'
response = []

auth = tweepy.OAuthHandler(ckey, csecret)
auth.secure = True
auth.set_access_token(atok, asecret)
api = tweepy.API(auth)
updated = False

def updateCached():
# copies current 'all' catalog to local cached file

    shutil.copy(all_items_path, cached_file)

def checkHashes():
    # generate sha256 hashes for original and chached files to compare for changes

    hashed_origin = hashlib.sha256()
    hashed_cached = hashlib.sha256()

    with open(all_items_path, 'rb') as afile:
        buf = afile.read()
        hashed_origin.update(buf)

    with open(cached_file, 'rb') as cfile:
        cbuf = cfile.read()
        hashed_cached.update(cbuf)

    if ((hashed_origin.hexdigest()) == (hashed_cached.hexdigest())):
        update = True
    else:
        update = False


def compareCatalogs():
# reads the "all" catalog from your repo, and compares it against the last
# cached snapshot.
    update = False
    # read in the "all" catalog from the repo
    current = plistlib.readPlist(all_items_path)

    # read in the cached snapshot
    cached = plistlib.readPlist(cached_file)

    # set up the list to store any move details
    global response

    # walk through the items in the current 'all' catalog
    for item in current:
        curName = item.get('name')
        curVer = item.get('version')
        curCatalogs = item.get('catalogs')

        # with the current catalog item, walk through the cached list
        for cachedItem in cached:
            # check for the cached item name
            if item.get('name') == cachedItem.get('name'):
                # check its version
                if item.get('version') == cachedItem.get('version'):
                    # and get its catalog list if it's a match
                    cachedCatalogs = cachedItem.get('catalogs')

                    # walk through the catalogs defined in the repo
                    for curCatalog in curCatalogs:
                        # if the current catalog isn't in the cached list,
                        # and it's not part of a 'testing' catalog
                        if ((curCatalog not in cachedCatalogs) & \
                           ("testing" not in curCatalog)):

                            # create the description of the move.
                            response.append(curName + " " + curVer + \
                            " added to " + curCatalog)

                            # Yes, we have updates
                            update = True
    # send the details back
    return (response, update)

def tweetMove(moves):
# walk through list of moves, and create tweets for each item in list.

    for twout in moves:
        # put the mm/dd/yy date at the beginning of the tweet
        tweetbuild = [datetime.date.today().strftime("%m/%d/%y"), "-", twout]
        tweet = ' '.join(tweetbuild)
        api.update_status(tweet)

# run makecatalogs to ensure that everything is fine-n-dandy before starting

subprocess.call(['/usr/local/munki/makecatalogs', munki_root])

# test if the cache file exists, and create it before comparing against it if not.
if not os.path.isfile(cached_file):
    print "Generating catalog cache file from current state of respository."
    updateCached()

(moves, updated) = compareCatalogs()

# check if any announcable updates - tweet if there are.
if (updated):
    if (armed):
        tweetMove(moves)
    else:
        for twout in moves:
            print twout
    updateCached()
