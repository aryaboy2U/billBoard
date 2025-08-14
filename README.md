# Billboard Chart Scraper & Spotify Playlist Creator

This script scrapes Billboard chart data and can create Spotify playlists from the chart data.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Spotify API credentials:
   - Go to https://developer.spotify.com/dashboard/applications
   - Create a new app and get your Client ID and Client Secret
   - Option 1: Create config file:
     ```bash
     mkdir config
     cp config.template.py config/config.py
     # Edit config/config.py with your actual credentials
     ```
   - Option 2: Use environment variables:
     ```bash
     export SPOTIFY_CLIENT_ID="your_client_id"
     export SPOTIFY_CLIENT_SECRET="your_client_secret"
     ```

## Usage Examples

```bash
# Create a Spotify playlist from current Hot 100
python billBoard.py --output spotify

# Get a random 90s chart and save to CSV
python billBoard.py --random-90s --output csv

# Update an existing playlist with random historical data
python billBoard.py --random-historical --playlist-id YOUR_PLAYLIST_ID

# Run in headless mode (for servers/automation)
python billBoard.py --headless --playlist-id YOUR_PLAYLIST_ID
```

## Command Line Options

- `--chart`: Chart name (default: hot-100)
- `--date`: Specific date (YYYY-MM-DD format)
- `--random-90s`: Use random date from 1990s
- `--random-historical`: Use random date from 1950-5 years ago
- `--output`: Output format (csv, print, spotify)
- `--playlist-id`: Update existing Spotify playlist
- `--limit`: Limit number of tracks
- `--headless`: Run without browser for authentication
