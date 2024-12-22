import tkinter as tk
from tkinter import messagebox
from tekore import Spotify, request_client_token
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

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify to YouTube Music Transfer")
        self.root.geometry("525x200")

        # Spotify API credentials
        with open("client_codes_Spotify.json") as f:
            client_codes = json.load(f)
        self.client_id = client_codes["client_id"]
        self.client_secret = client_codes["client_secret"]
        self.app_token = request_client_token(self.client_id, self.client_secret)
        self.playlist_id_youtube = ""

        # Widgets
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="YouTube Music Playlist URL:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.youtube_url_entry = tk.Entry(self.root, width=50)
        self.youtube_url_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.root, text="Spotify Playlist URL:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.spotify_url_entry = tk.Entry(self.root, width=50)
        self.spotify_url_entry.grid(row=1, column=1, padx=10, pady=10)

        self.authorize_button = tk.Button(self.root, text="Authorize YouTube", command=self.authorize_youtube)
        self.authorize_button.grid(row=2, column=0, columnspan=2, pady=10)

        self.transfer_button = tk.Button(self.root, text="Transfer Playlist", command=self.transfer_playlist, state=tk.DISABLED)
        self.transfer_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.message_label = tk.Label(self.root, text="", fg="blue")
        self.message_label.grid(row=4, column=0, columnspan=2, pady=10)

    def authorize_youtube(self):
        self.message_label.config(text="Authorizing with YouTube...")
        self.root.update_idletasks()
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
        credentials = flow.run_local_server()
        self.youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)
        self.message_label.config(text="YouTube authorization successful!")
        self.transfer_button.config(state=tk.NORMAL)

    def transfer_playlist(self):
        self.playlist_id_youtube = self.youtube_url_entry.get()
        if "https://music.youtube.com/browse/" in self.playlist_id_youtube:
            self.playlist_id_youtube = self.playlist_id_youtube.replace("/browse/VL", "/browse/")
            start_index = self.playlist_id_youtube.find("browse/") + len("browse/")
            playlist_id = self.playlist_id_youtube[start_index:]
            self.playlist_id_youtube = f"https://music.youtube.com/playlist?list={playlist_id}"
        self.playlist_id_youtube = self.playlist_id_youtube.removeprefix("https://music.youtube.com/playlist?list=")
        self.get_song_spotify(self.app_token)

    def get_song_spotify(self, app_token):
        spotify = Spotify(app_token)
        playlist_id_spotify = self.spotify_url_entry.get()
        playlist_id_spotify = playlist_id_spotify.removeprefix("https://open.spotify.com/playlist/")
        playlist = spotify.playlist_items(playlist_id_spotify, as_tracks=True)
        playlist = playlist["items"]
        try:
            i = 0
            song_ids = []
            while_loop = True
            while while_loop:
                sub_playlist = playlist[i]
                sub_playlist.pop("added_at", None)
                sub_playlist.pop("added_by", None)
                sub_playlist.pop("is_local", None)
                sub_playlist.pop("primary_color", None)
                sub_playlist = sub_playlist["track"]
                sub_playlist.pop("album", None)
                sub_playlist.pop("artists", None)
                sub_playlist.pop("available_markets", None)
                sub_playlist = sub_playlist["id"]
                song_ids.append(sub_playlist)
                i += 1
        except IndexError:
            pass

        for song_id in song_ids:
            track = spotify.track(song_id, market=None)
            artist = track.artists[0]
            self.get_song_youtube(f"{track.name} by {artist.name}")

    def get_song_youtube(self, full):
        request = self.youtube.search().list(
            part="snippet",
            maxResults=1,
            q=full
        )
        response = request.execute()
        response = response.get("items")[0]
        videoid = response.get("id").get("videoId")
        time.sleep(1)
        self.place_in_playlist(videoid, self.playlist_id_youtube, full)

    def place_in_playlist(self, videoid, playlistid, full):
        request = self.youtube.playlistItems().insert(
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
            request.execute()
            self.message_label.config(text=f"Added '{full}' to playlist.")
        except googleapiclient.errors.HttpError as e:
            print(e)
            self.message_label.config(text=f"Failed to add '{full}' to playlist.")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
