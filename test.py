import streamlit as st
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser
import sys


def autheticate_spotify(sp_oauth):
    # Initialize sp as None
    sp = None

    # Create an empty container for the button
    placeholder_loggin_button = st.sidebar.empty()

    # Check if user is already authenticated, using session state
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # If not authenticated, show login button
    if not st.session_state["authenticated"]:
        submit = placeholder_loggin_button.button("Log in with Spotify")

        # If login button is clicked, generate authorization URL
        if submit:
            auth_url = sp_oauth.get_authorize_url()
            webbrowser.open(auth_url)

    # Check for the 'code' parameter in the URL (which indicates a successful login)
    if "code" in st.query_params:
        code = st.query_params["code"]

        # Retrieve the token info, using the authorization code
        token_info = sp_oauth.get_cached_token()
        if not token_info:
            token_info = sp_oauth.get_access_token(code)

        # Store access token and mark user as authenticated
        access_token = token_info["access_token"]
        sp = spotipy.Spotify(auth=access_token)

        # Mark the user as authenticated and hide the login button
        st.session_state["authenticated"] = True
        st.sidebar.success("You have successfully logged in to Spotify!")

    # If authenticated, show other content
    if st.session_state["authenticated"]:
        # After the login is successful, clear the placeholder (removes the button)
        placeholder_loggin_button.empty()

    return sp


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Define the Spotify access scope
    scope = "user-read-recently-played user-top-read playlist-modify-public playlist-modify-private user-library-read"

    # Initialize Spotify OAuth
    sp_oauth = SpotifyOAuth(client_id=os.getenv('SPOTIFY_CLIENT_ID'), 
                            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'), 
                            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'), 
                            scope=scope)
    
    st.title("Spotify Testing")




    # Gets the user to autheticate their spotify account
    sp = autheticate_spotify(sp_oauth)



    cadence = 120

    if st.session_state["authenticated"]:
        # Retrieve all liked tracks in batches of 50
        liked_tracks = []
        offset = 0
        while True:
            results = sp.current_user_saved_tracks(limit=50, offset=offset)
            liked_tracks.extend(results['items'])
            if len(results['items']) < 50:  # No more tracks left to retrieve
                break
            offset += 50  # Move to the next batch

        # Extract the track IDs and names from all liked tracks
        liked_track_ids = [track['track']['id'] for track in liked_tracks]
        liked_track_names = [track['track']['name'] for track in liked_tracks]

        # Retrieve the user's most recent 50 playlists
        playlists = sp.current_user_playlists(limit=100)

        # Extract tracks from each playlist
        playlist_track_ids = []
        playlist_track_names = []
        for playlist in playlists['items']:
            playlist_tracks = sp.playlist_tracks(playlist['id'], limit=100)  # Get up to 100 tracks from each playlist
            for item in playlist_tracks['items']:
                track = item['track']
                playlist_track_ids.append(track['id'])
                playlist_track_names.append(track['name'])

        # Combine liked track IDs and playlist track IDs
        all_track_ids = liked_track_ids + playlist_track_ids
        all_track_names = liked_track_names + playlist_track_names

        # Helper function to batch the list into chunks of 100
        def batch(iterable, n=1):
            l = len(iterable)
            for ndx in range(0, l, n):
                yield iterable[ndx:min(ndx + n, l)]

        # Get audio features (including tempo) in batches of 100
        audio_features = []
        for track_batch in batch(all_track_ids, 100):  # Split track IDs into batches of 100
            audio_features.extend(sp.audio_features(track_batch))

        # Filter tracks based on the tempo range [cadence-5, cadence+5]
        filtered_tracks = []
        for track_name, track_id, features in zip(all_track_names, all_track_ids, audio_features):
            if features and (cadence - 5) <= features['tempo'] <= (cadence + 5):
                filtered_tracks.append((track_name, track_id, features['tempo']))

        # Limit to 20 songs with the closest tempo match to your cadence
        st.text(len(filtered_tracks))

        filtered_tracks = filtered_tracks[:20]  # Show only 20 tracks

        # Display the filtered track name, ID, and tempo
        st.text(f"Songs matching your cadence ({(cadence - 5)}-{(cadence + 5)} BPM):")
        for track_name, track_id, tempo in filtered_tracks:
            st.text(f"Track: {track_name}, ID: {track_id}, Tempo: {tempo} BPM")