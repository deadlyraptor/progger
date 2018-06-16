# progger.py

'''
1. Accept cli call with desired year, e.g. progger 2018
2. Build URL for top albums in given year on ProgArchives
3. Parse the page using BS4 for top ten albums & artists
4. Create Spotify playlist for given year, i.e. PA 2018
5. Append each album from PA to the playlist
'''

import sys
import re
from bs4 import BeautifulSoup
import spotipy
import spotipy.util as util
from credentials import user, scope, client_id, client_secret

year = sys.argv[1]
pa_url = f'http://www.progarchives.com/top-prog-albums.asp?syears={year}' \
         f'&smaxresults=10'
page = requests.get(pa_url)

soup = BeautifulSoup(page.text, 'html.parser')

albums = []
artists = []

table = soup.find('td', class_='cls_TableHeader').find_parent('table')
for row in table.find_all('tr'):
    for cell in row.find_all('td'):
        # append artist to artists & album to albums
        if cell.find('a', href=re.compile('artist.asp')):
            album = cell.contents[0].get_text()
            albums.append(album)
            artist = cell.contents[2].get_text()
            artists.append(artist)

# spotify authorization
token = util.prompt_for_user_token(user, scope,
                                   redirect_uri='http://localhost/',
                                   client_id=client_id,
                                   client_secret=client_secret)
if token:
    sp = spotipy.Spotify(auth=token)
    # create playlist
    sp.user_playlist_create(user, f'PA {year}')
    print('Playlist created.')
    # retrieve playlist ID
    playlists = sp.user_playlists(user)
    for playlist in playlists['items']:
        if playlist['name'] == f'PA {year}':
            playlist_uri = playlist['uri']
    print(f'Playlist uri: {playlist_uri}')
    # retrieve album URIs from albums
    album_uris = []
    for album, artist in zip(albums, artists):
        search_string = (f'album:{album} artist:{artist}')
        search_result = sp.search(search_string, limit=1, type='album')
        # filters out the response from Spotify for empty results, that is
        # if the album and is not available
        if search_result['albums']['items'] != []:
            album_uris.append(search_result['albums']['items'][0]['uri'])
    print(f'Album uris: {album_uris}')
    # retrieve track URIs from albums
    track_uris = []
    for album_uri in album_uris:
        tracks = sp.album_tracks(album_uri)
        for track in tracks['items']:
            track_uris.append(track['uri'])
    result = sp.user_playlist_add_tracks(user, playlist_uri, track_uris)
    print(result)
    print('Tracks added to playlist.')
else:
    print('Can\'t get token')
