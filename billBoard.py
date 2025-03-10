import requests
from bs4 import BeautifulSoup
import csv
import time
import argparse
from datetime import datetime, timedelta
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import random
import sys

from config.config import SPOTIPY_CLIENT_ID
from config.config import SPOTIPY_CLIENT_SECRET

def get_random_90s_date():
    """Generate a random date from the 1990s in YYYY-MM-DD format."""
    # Start date: January 1, 1990
    start_date = datetime(1990, 1, 1)
    # End date: December 31, 1999
    end_date = datetime(1999, 12, 31)

    # Calculate the difference in days
    delta_days = (end_date - start_date).days

    # Generate a random number of days to add to start date
    random_days = random.randint(0, delta_days)

    # Create the random date
    random_date = start_date + timedelta(days=random_days)

    # Format as YYYY-MM-DD
    return random_date.strftime("%Y-%m-%d")

def get_random_historical_date():
    """Generate a random date between 1950 and 5 years ago in YYYY-MM-DD format."""
    # Start date: January 1, 1950
    start_date = datetime(1950, 1, 1)
    
    # End date: 5 years ago from today
    current_date = datetime.now()
    end_date = datetime(current_date.year - 5, current_date.month, current_date.day)

    # Calculate the difference in days
    delta_days = (end_date - start_date).days

    # Generate a random number of days to add to start date
    random_days = random.randint(0, delta_days)

    # Create the random date
    random_date = start_date + timedelta(days=random_days)

    # Format as YYYY-MM-DD
    return random_date.strftime("%Y-%m-%d")

def get_billboard_chart(chart_name="hot-100", date=None):
    """
    Scrape Billboard chart data for a specific chart and date.

    Args:
        chart_name (str): Name of the Billboard chart (e.g., "hot-100", "billboard-200")
        date (str): Date in YYYY-MM-DD format. If None, uses the latest chart.

    Returns:
        list: List of dictionaries with song titles and artists
    """
    # Form the URL
    base_url = "https://www.billboard.com/charts/"
    url = f"{base_url}{chart_name}"
    if date:
        # Format date as needed by Billboard (YYYY-MM-DD)
        url = f"{url}/{date}/"

    # Set headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    print(f"Fetching chart: {url}")

    try:
        # Make the request with a timeout
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract chart entries
        chart_entries = []

        # This selector targets the chart entries on Billboard's new layout
        entries = soup.select('li.o-chart-results-list__item')

        if not entries:
            # Fallback to alternative selectors if the primary one doesn't find entries
            entries = soup.select('div.o-chart-results-list-row')

        if not entries:
            # Another fallback for some charts
            entries = soup.select('div.chart-list-item')

        if not entries:
            print("Could not find chart entries. Billboard may have changed their HTML structure.")
            return []

        for entry in entries:
            # Try different selectors to accommodate various chart layouts
            title_elem = entry.select_one('h3.c-title') or entry.select_one('span.c-title')
            artist_elem = entry.select_one('span.c-label') or entry.select_one('span.a-font-primary-s')

            if title_elem and artist_elem:
                title = title_elem.get_text(strip=True)
                artist = artist_elem.get_text(strip=True)

                # Skip entries that are likely not songs (e.g., headers, ads)
                if title and artist and len(title) > 1 and len(artist) > 1:
                    chart_entries.append({
                        "title": title,
                        "artist": artist
                    })

        print(f"Found {len(chart_entries)} entries")
        return chart_entries

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the chart: {e}")
        return []

def save_to_csv(chart_entries, chart_name, date=None):
    """Save chart entries to a CSV file."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    filename = f"{chart_name}_{date}.csv"

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'artist']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for entry in chart_entries:
            writer.writerow(entry)

    print(f"Saved {len(chart_entries)} entries to {filename}")

def setup_spotify(headless=False):
    """Set up Spotify client with OAuth, with support for headless operation."""
    client_id = os.environ.get('SPOTIFY_CLIENT_ID', SPOTIPY_CLIENT_ID)
    client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET', SPOTIPY_CLIENT_SECRET)
    redirect_uri = os.environ.get('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8888/callback')
    cache_path = ".spotifycache"

    # Set up the scope for the permissions needed
    scope = "playlist-modify-public playlist-modify-private"

    if headless:
        print("Using headless authentication mode")
        # Check if cache file exists before proceeding
        if not os.path.exists(cache_path):
            print(f"ERROR: Cache file '{cache_path}' not found. Please run this script once on a machine with a browser first.")
            print("Then copy the '.spotifycache' file to this headless machine in the same directory as the script.")
            sys.exit(1)

        # Use the non-interactive OAuth handler that requires a pre-existing cache
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=cache_path,
            open_browser=False,  # Don't try to open a browser
            show_dialog=False    # Don't show the Spotify auth dialog
        )
    else:
        # Standard OAuth for interactive environments
        print(f"Using redirect URI: {redirect_uri}")
        print("Make sure this EXACT URI is added to your Spotify app's Redirect URIs in the developer dashboard")

        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=cache_path
        )

    # Set up the Spotify client
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Test the connection (this will force a token refresh if needed)
    try:
        user = sp.current_user()
        print(f"Authenticated as: {user['display_name']} ({user['id']})")
    except Exception as e:
        print(f"Authentication error: {e}")
        if headless:
            print("Token may have expired and couldn't be refreshed automatically.")
            print("Try generating a fresh .spotifycache file on a machine with a browser.")
        sys.exit(1)

    return sp

def search_track(sp, title, artist):
    """Search for a track on Spotify and return its URI."""
    # Clean up the artist name (remove featuring artists for better search results)
    if "feat." in artist.lower():
        artist = artist.lower().split("feat.")[0].strip()
    if "featuring" in artist.lower():
        artist = artist.lower().split("featuring")[0].strip()
    if "ft." in artist.lower():
        artist = artist.lower().split("ft.")[0].strip()

    # Create search query
    query = f"track:{title} artist:{artist}"
    results = sp.search(q=query, type='track', limit=1)

    # Check if we got a match
    if results['tracks']['items']:
        track_uri = results['tracks']['items'][0]['uri']
        track_name = results['tracks']['items'][0]['name']
        track_artist = results['tracks']['items'][0]['artists'][0]['name']
        print(f"Found: {track_name} by {track_artist}")
        return track_uri
    else:
        # Try a more lenient search with just the title
        results = sp.search(q=title, type='track', limit=1)
        if results['tracks']['items']:
            track_uri = results['tracks']['items'][0]['uri']
            track_name = results['tracks']['items'][0]['name']
            track_artist = results['tracks']['items'][0]['artists'][0]['name']
            print(f"Found close match: {track_name} by {track_artist}")
            return track_uri
        else:
            print(f"Could not find: {title} by {artist}")
            return None

def create_playlist(sp, playlist_name, description, chart_entries):
    """Create a Spotify playlist and add tracks from chart entries."""
    # Get the user's Spotify ID
    user_id = sp.me()['id']

    # Create a new playlist
    playlist = sp.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=True,
        description=description
    )

    playlist_id = playlist['id']
    print(f"Created playlist: {playlist_name} (ID: {playlist_id})")

    # Search for and collect track URIs
    track_uris = []
    found_tracks = 0
    for entry in chart_entries:
        track_uri = search_track(sp, entry['title'], entry['artist'])
        if track_uri:
            track_uris.append(track_uri)
            found_tracks += 1
            # Add tracks in batches to avoid rate limiting
            if len(track_uris) >= 50:
                sp.playlist_add_items(playlist_id, track_uris)
                track_uris = []
                time.sleep(1)  # Avoid rate limiting

    # Add any remaining tracks
    if track_uris:
        sp.playlist_add_items(playlist_id, track_uris)

    print(f"Playlist populated with {found_tracks} tracks")
    return playlist_id

def populate_existing_playlist(sp, playlist_id, chart_entries, chart_name, date_str):
    """
    Add tracks from chart entries to an existing playlist, replacing any existing tracks.
    Also updates the playlist name and description with chart and date information.
    """
    # First, clear all existing tracks from the playlist
    print(f"Clearing existing tracks from playlist {playlist_id}...")
    try:
        sp.playlist_replace_items(playlist_id, [])
        print("Playlist cleared successfully")
    except Exception as e:
        print(f"Error clearing playlist: {e}")
        return None

    # Update the playlist name and description
    try:
        # Format chart name to look nicer (e.g., "hot-100" -> "Hot 100")
        formatted_chart_name = chart_name.replace("-", " ").title()

        # Create new playlist name with chart and date
        new_playlist_name = f"Billboard {formatted_chart_name} - Week of {date_str}"
        new_description = f"Billboard {formatted_chart_name} chart for the week of {date_str}. Automatically updated."

        # Update the playlist metadata
        sp.playlist_change_details(
            playlist_id=playlist_id,
            name=new_playlist_name,
            description=new_description
        )
        print(f"Updated playlist name to: {new_playlist_name}")
    except Exception as e:
        print(f"Error updating playlist details: {e}")

    # Search for and collect track URIs
    track_uris = []
    found_tracks = 0
    for entry in chart_entries:
        track_uri = search_track(sp, entry['title'], entry['artist'])
        if track_uri:
            track_uris.append(track_uri)
            found_tracks += 1
            # Add tracks in batches to avoid rate limiting
            if len(track_uris) >= 50:
                sp.playlist_add_items(playlist_id, track_uris)
                track_uris = []
                time.sleep(1)  # Avoid rate limiting

    # Add any remaining tracks
    if track_uris:
        sp.playlist_add_items(playlist_id, track_uris)

    print(f"Playlist refreshed with {found_tracks} new tracks")
    return playlist_id

def main():
    parser = argparse.ArgumentParser(description='Scrape Billboard chart data and create Spotify playlist')
    parser.add_argument('--chart', default='hot-100', help='Chart name (e.g., hot-100, billboard-200, alternative-songs)')
    parser.add_argument('--date', help='Chart date in YYYY-MM-DD format')
    parser.add_argument('--random-90s', action='store_true', help='Use a random date from the 1990s')
    parser.add_argument('--random-historical', action='store_true', help='Use a random date from 1950 to 5 years ago')
    parser.add_argument('--output', default='spotify', choices=['csv', 'print', 'spotify'], help='Output format')
    parser.add_argument('--playlist-name', help='Name for the Spotify playlist (default: Chart name + date)')
    parser.add_argument('--playlist-id', help='Existing Spotify playlist ID to populate')
    parser.add_argument('--limit', type=int, help='Limit number of tracks to add')
    parser.add_argument('--client-id', help='Spotify Client ID')
    parser.add_argument('--client-secret', help='Spotify Client Secret')
    parser.add_argument('--redirect-uri', default='http://127.0.0.1:8888/callback',
                       help='Spotify redirect URI (default: http://127.0.0.1:8888/callback)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (requires pre-existing auth cache file)')

    args = parser.parse_args()

    # Handle random date selection
    if args.random_90s:
        random_date = get_random_90s_date()
        print(f"Using random 90s date: {random_date}")
        args.date = random_date
    elif args.random_historical:
        random_date = get_random_historical_date()
        print(f"Using random historical date: {random_date}")
        args.date = random_date

    # Use current date if none specified
    date_str = args.date if args.date else datetime.now().strftime("%Y-%m-%d")

    # Set Spotify credentials from command line if provided
    if args.client_id:
        os.environ['SPOTIFY_CLIENT_ID'] = args.client_id
    if args.client_secret:
        os.environ['SPOTIFY_CLIENT_SECRET'] = args.client_secret
    if args.redirect_uri:
        os.environ['SPOTIFY_REDIRECT_URI'] = args.redirect_uri

    # Get chart entries
    chart_entries = get_billboard_chart(args.chart, date_str)

    # Limit the number of tracks if specified
    if args.limit and args.limit > 0:
        chart_entries = chart_entries[:args.limit]

    if args.output == 'csv':
        save_to_csv(chart_entries, args.chart, date_str)
    elif args.output == 'print':
        print("\nChart Entries:")
        for i, entry in enumerate(chart_entries, 1):
            print(f"{i}. {entry['title']} - {entry['artist']}")
    elif args.output == 'spotify':
        # Set up Spotify client with headless mode if specified
        sp = setup_spotify(headless=args.headless)

        if args.playlist_id:
            # Populate existing playlist with new name including chart and date
            populate_existing_playlist(sp, args.playlist_id, chart_entries, args.chart, date_str)
        else:
            # Create a new playlist
            playlist_name = args.playlist_name if args.playlist_name else f"Billboard {args.chart} - {date_str}"
            description = f"Billboard {args.chart} chart from {date_str}. Created automatically."

            create_playlist(sp, playlist_name, description, chart_entries)

if __name__ == "__main__":
    # You can hardcode your playlist ID here if you want
    HARDCODED_PLAYLIST_ID = "54MwfcvssipBoq5LAT3ZC0"

    # Create a parser to check for the playlist ID argument and flags
    parser = argparse.ArgumentParser()
    parser.add_argument('--playlist-id', default=HARDCODED_PLAYLIST_ID)
    parser.add_argument('--random-90s', action='store_true')
    parser.add_argument('--random-historical', action='store_true')
    parser.add_argument('--headless', action='store_true')
    args, unknown = parser.parse_known_args()

    # Call the main function with the custom argv
    import sys
    new_argv = [sys.argv[0]]

    # Add playlist ID if provided
    new_argv.extend(['--playlist-id', args.playlist_id])

    # Add random 90s flag if set
    if args.random_90s:
        new_argv.append('--random-90s')

    # Add random historical flag if set
    if args.random_historical:
        new_argv.append('--random-historical')

    # Add headless flag if set
    if args.headless:
        new_argv.append('--headless')

    # Add any other arguments
    new_argv.extend(unknown)

    sys.argv = new_argv
    main()