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


def calculate_cadence(input_dict):
    # Conversion factors
    stride_factor = 0.41
    foot_conv_factor = 0.3048       # feet to metre conversion
    inch_conv_factor = 0.0254       # inch to metre conversion
    kmh_to_mmin = 16.6667           # km/h to m/min conversion
    mph_to_mmin = 26.8224           # mph to m/min conversion

    # Convert feet & inches into metres
    if input_dict['height_option'] != "Metres":
        input_dict['height_m'] = (input_dict['height_ft'] * foot_conv_factor) + (input_dict['height_in'] * inch_conv_factor)

    # Calculate stride length
    stride_length = input_dict['height_m'] * stride_factor

    # convert pace to m/min
    if input_dict['pace_option'] == "km/h":
        speed = input_dict['pace'] * kmh_to_mmin
    else:
        speed = input_dict['pace'] * mph_to_mmin

    # Calculate cadence in steps per minute
    cadence = speed / stride_length

    return cadence


    



def user_inputs(sp):
    # Initialize session state to track if fields are disabled
    if 'disabled' not in st.session_state:
        st.session_state["disabled"] = False
    if 'submitted' not in st.session_state:
        st.session_state["submitted"] = False

    # Initialize cadence as None
    cadence = None

    # Function to disable the input fields
    def disable_fields():
        st.session_state["disabled"] = True
        st.session_state["submitted"] = True
        st.rerun()  # Rerun the script to immediately reflect the disabled state

    # Function to reset the form and re-enable the fields
    def reset_form():
        st.session_state["disabled"] = False
        st.session_state["submitted"] = False
        st.rerun()  # Rerun the script to immediately reflect the reset state

    with st.sidebar:
        # User inputs for height
        st.header("Input your height")
        height_option = st.selectbox("Select height unit:", ("Metres", "Feet & Inches"), disabled=st.session_state.disabled)

        if height_option == "Metres":
            height_m = st.number_input("Enter your height in metres:", min_value=0.0, step=0.01, disabled=st.session_state.disabled)
            height_ft, height_in = None, None  # To keep consistent variables
        else:
            col1, col2 = st.columns(2)  # Create two columns
            with col1:
                height_ft = st.number_input("Feet:", min_value=0, step=1, disabled=st.session_state.disabled)
            with col2:
                height_in = st.number_input("Inches:", min_value=0, max_value=11, step=1, disabled=st.session_state.disabled)
            height_m = None  # To keep consistent variables

        # User inputs for running pace
        st.header("Input your running pace")
        pace_option = st.selectbox("Select pace unit:", ("km/h", "mph"), disabled=st.session_state.disabled)

        if pace_option == "km/h":
            pace = st.number_input("Enter your pace in km/h:", min_value=0.0, step=0.1, disabled=st.session_state.disabled)
        else:
            pace = st.number_input("Enter your pace in mph:", min_value=0.0, step=0.1, disabled=st.session_state.disabled)


        col1, col2, _ = st.columns(3)  # Create two columns
        with col1:
            if st.button("Submit") and not st.session_state.disabled:
                disable_fields()  # Lock the input fields

        # Show Reset button only after submission
        with col2:
            if st.session_state.submitted:
                if st.button("Reset"):
                    reset_form()  # Unlock the input fields and hide the reset button

        inputs_dict = dict()
        inputs_dict['height_option'] = height_option
        inputs_dict['height_m'] = height_m
        inputs_dict['height_ft'] = height_ft
        inputs_dict['height_in'] = height_in
        inputs_dict['pace_option'] = pace_option
        inputs_dict['pace'] = pace

        if st.session_state.submitted:
            cadence = calculate_cadence(inputs_dict)
            st.text(cadence)

        return cadence

    # # Initialize session state variables for search results and selection
    # if 'search_results' not in st.session_state:
    #     st.session_state['search_results'] = None
    # if 'selected_option' not in st.session_state:
    #     st.session_state['selected_option'] = None

    # # Step 1: Input for searching a song or artist
    # st.header("Find Recommendations")
    # search_type = st.radio("Search by:", ("Song", "Artist"))
    # search_input = st.text_input(f"Enter {search_type} name:")

    # # Step 2: Search button to fetch results from Spotify
    # if st.button("Search"):
    #     if search_type == "Song":
    #         search_results = sp.search(q=f"track:{search_input}", type="track", limit=10)
    #         st.session_state['search_results'] = search_results['tracks']['items']
    #     elif search_type == "Artist":
    #         search_results = sp.search(q=f"artist:{search_input}", type="artist", limit=10)
    #         st.session_state['search_results'] = search_results['artists']['items']

    # # Step 3: If search results exist, display a dropdown for the user to select the correct track/artist
    # if st.session_state['search_results']:
    #     if search_type == "Song":
    #         options = [
    #             f"{track['name']} by {track['artists'][0]['name']}"
    #             for track in st.session_state['search_results']
    #         ]
    #     elif search_type == "Artist":
    #         options = [artist['name'] for artist in st.session_state['search_results']]
        
    #     selected_option = st.selectbox("Multiple results found. Please select one:", options)

    #     # Store the user's selected option in session state
    #     if selected_option:
    #         if search_type == "Song":
    #             selected_track = next(
    #                 track for track in st.session_state['search_results']
    #                 if f"{track['name']} by {track['artists'][0]['name']}" == selected_option
    #             )
    #             st.session_state['selected_option'] = selected_track
    #         elif search_type == "Artist":
    #             selected_artist = next(
    #                 artist for artist in st.session_state['search_results']
    #                 if artist['name'] == selected_option
    #             )
    #             st.session_state['selected_option'] = selected_artist

    # # Step 4: Once an option is selected, show the "Find Recommendations" button
    # if st.session_state['selected_option']:
    #     if st.button("Find Recommendations"):
    #         if search_type == "Song":
    #             track = st.session_state['selected_option']
    #             recommendations = sp.recommendations(seed_tracks=[track['id']], limit=10)
    #             st.write(f"Recommended songs based on {track['name']} by {track['artists'][0]['name']}:")
    #         elif search_type == "Artist":
    #             artist = st.session_state['selected_option']
    #             recommendations = sp.recommendations(seed_artists=[artist['id']], limit=10)
    #             st.write(f"Recommended songs based on artist {artist['name']}:")

    #         # Display the recommended tracks
    #         for track in recommendations['tracks']:
    #             track_name = track['name']
    #             artist_name = track['artists'][0]['name']
    #             track_url = track['external_urls']['spotify']
    #             st.write(f"{track_name} by {artist_name} [Listen on Spotify]({track_url})")



if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Define the Spotify access scope
    scope = "user-read-recently-played user-top-read playlist-modify-public playlist-modify-private"

    # Initialize Spotify OAuth
    sp_oauth = SpotifyOAuth(client_id=os.getenv('SPOTIFY_CLIENT_ID'), 
                            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'), 
                            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'), 
                            scope=scope)
    
    st.title("Spotify Running Playlist")

    st.text('Add info here about what this app does....')

    # Gets the user to autheticate their spotify account
    sp = autheticate_spotify(sp_oauth)

    if st.session_state["authenticated"]:
        cadence = user_inputs(sp)