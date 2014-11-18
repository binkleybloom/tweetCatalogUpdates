#################################
#
# Twitter munki-catalog change notification script
#
# Written by Tim Schutt - taschutt@syr.edu
#
# November, 2014
#
#################################

import os, plistlib, tweepy, datetime

#========== Modify to match your environment ===========#

### munki repo root ###
munki_root = "/Volumes/munki-repo"  # munki repo root

### Twitter Consumer API key & token, and Access token & secret ###
ckey = ''
csecret = ''
atok = ''
asecret = ''

#============ Do not modify below this line ============#

all_items_path = os.path.join(munki_root, 'catalogs','all')
script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
cached_file = str(script_path) + '/cached.plist'
response = []

auth = tweepy.OAuthHandler(ckey, csecret)
auth.secure = True
auth.set_access_token(atok, asecret)
api = tweepy.API(auth)

def updateCached():
# updates/creates a snapshot of the state of your repo in a local cache file
# consisting of name, version and catalog listing for each item.

    # read the "all" catalog from your repository to a dictionary
    catalogitems = plistlib.readPlist(all_items_path)

    currentResults = []

    # walk through it item by item
    for item in catalogitems:
        name = item.get('name')
        version = item.get('version')
        catalogs = item.get('catalogs')

        # insert each item's data into a list as a dictionary
        merged = {'name':name, 'version':version, 'catalogs':catalogs}
        currentResults.append(merged)

    # write it out to a file
    plistlib.writePlist(currentResults, cached_file)

def compareCatalogs():
# reads the "all" catalog from your repo, and compares it against the last
# cached snapshot.

    # read in the "all" catalog from the repo
    current = plistlib.readPlist(all_items_path)

    # read in the cached snapshot
    cached = plistlib.readPlist(cached_file)

    # set up the list to store any move details
    global response

    # no item catalog changes have happened yet
    update = False

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

    for each move in moves:
        # put the mm/dd/yy date at the beginning of the tweet
        tweetbuild = [datetime.date.today().strftime("%m/%d/%y"), "-", move]
        tweet = ' '.join(tweetbuild)
        api.update_status(tweet)

# test if the cache file exists, and create it before comparing against it if not.
if not os.path.isfile(cached_file):
    print "Generating catalog cache file from current state of respository."
    updateCached()

(moves, updated) = compareCatalogs()

# check if any announcable updates - tweet if there are.
if (updated):
    tweetMove(moves)

# update the cache file at the end of each run.
updateCached()
