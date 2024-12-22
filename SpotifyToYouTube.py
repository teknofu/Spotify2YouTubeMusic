# Before running the code read the README
from tekore import Spotify, request_client_token, scope
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import time
import json

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "client_secret_YouTube.json"
print("We have to get authorized with Google to use the Youtube API")
print("Your browser will open and prompt you to authorize the use and editing ability of your Youtube playlists")
input("Press enter to continue")
# Get credentials and create an API client
flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
credentials = flow.run_local_server()
youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

with open("client_codes_Spotify.json") as f:
    client_codes = json.load(f)
print(
    "First Create a playlist on Youtube Music for the songs to be transferred to and copy the url")
input("Press Enter to continue...")  # Waits for user input
# Initializes Spotify API client codes
client_id = str(client_codes["client_id"])
client_secret = str(client_codes["client_secret"])
app_token = request_client_token(client_id, client_secret)
playlist_id_youtube = input(
    "Now view your playlist page on Youtube Music\r enter the url of the playlist you created here: ")



if "https://music.youtube.com/browse/" in playlist_id_youtube:
    playlist_id_youtube = playlist_id_youtube.replace("/browse/VL", "/browse/")

    # Extract the playlist ID
    start_index = playlist_id_youtube.find("browse/") + len("browse/")
    playlist_id = playlist_id_youtube[start_index:]
    print(f"playlist_id is {playlist_id}")

    # Update playlist_id_youtube with the new format
    playlist_id_youtube = f"https://music.youtube.com/playlist?list={playlist_id}"

    print(f"Playlist ID updated: {playlist_id_youtube}")
else:
    print("Playlist ID already in the correct format.")
playlist_id_youtube = playlist_id_youtube.removeprefix("https://music.youtube.com/playlist?list=")
attempts = 0



# Gets the name of the song and the artist from a spotify playlist
def get_song_spotify(app_token):
    global attempts
    spotify = Spotify(app_token)
    playlist_id_spotify = input("Enter the url of the spotify playlist you want to copy: ")
    playlist_id_spotify = playlist_id_spotify.removeprefix("https://open.spotify.com/playlist/")
    playlist = spotify.playlist_items(playlist_id_spotify, as_tracks=True)
    print(playlist)
    playlist = playlist["items"]
    print(playlist)
    try:
        i = 0
        songIds = []
        whileLoop = True

        # Gets the song ids from the returned dictionary
        while whileLoop:
            subPlaylist = playlist[i]
            subPlaylist.pop("added_at", None)
            subPlaylist.pop("added_by", None)
            subPlaylist.pop("is_local", None)
            subPlaylist.pop("primary_color", None)
            subPlaylist = subPlaylist["track"]
            subPlaylist.pop("album", None)
            subPlaylist.pop("artists", None)
            subPlaylist.pop("available_markets", None)
            subPlaylist = subPlaylist["id"]
            print(subPlaylist)
            songIds.append(subPlaylist)
            i += 1

    except IndexError:
        pass

    for i in range(len(songIds)):
        track = spotify.track(songIds[i], market=None)
        artist = track.artists
        artist = artist[0]
        print(f"{track.name} by {artist.name}")
        get_song_youtube(f"{track.name} by {artist.name}")


# Searches the name of the song by the artist and get the first video on the lists id
def get_song_youtube(full):
    request = youtube.search().list(
        part="snippet",
        maxResults=1,
        q=full
    )
    response = request.execute()

    response = response.get("items")
    response = response[0]
    response = response.get("id")
    videoid = response.get("videoId")
    time.sleep(1)
    place_in_playlist(videoid, playlist_id_youtube, full)


# Using the id from the previous function places that in the playlist
def place_in_playlist(videoid, playlistid, full):
    global attempts
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlistid,
                "position": 0,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": videoid
                }
            }
        }
    )

    try:
        response = request.execute()
        attempts = 0

    except googleapiclient.errors.HttpError as e:
        print(e)
        attempts += 1
        if attempts > 6 or attempts == 6:
            print(full + " failed to add to playlist. The song has been skipped")
            with open("response.txt", "w") as f1:
                f1.write(str(full))
                f1.write("\n")
        else:
            pass


get_song_spotify(app_token)
