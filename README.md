# spacehey.py

An unofficial, reverse-engineered Python wrapper for [SpaceHey](https://spacehey.com).

This library provides two clients:
* **MobileClient**: Uses the official SpaceHey mobile API (v1). Best for fast, reliable social interactions and profile editing.
* **WebClient**: Mimics a browser session. Required for features not available in the API.
* ~~**PublicClient**~~: Currently WIP. Will be full scraping.

**Disclaimer**: This project is not affiliated with SpaceHey. Use responsibly.

## Installation

Currently available via Git:

```bash
pip install git https://github.com/kindajune/spacehey.py.git

```

## Authentication

### 1. Mobile Token (for `MobileClient`)

Required for most standard interactions.

1. Visit: `https://auth.spacehey.com/login?client_id=app-android&return=spacehey://callback/`
2. Log in to your account.
3. Right Click the "If you aren't redirected, please click here" link.
4. Copy the URL it tries to open (starts with `spacehey://`).
5. Your token is the value of `access_key` in that URL.

### 2. Web Session (for `WebClient`)

1. Log in to SpaceHey on a desktop browser.
2. Open Developer Tools (F12) -> Application/Storage -> Cookies.
3. Copy the value of the `SPACEHEY_SESSID` cookie.

## Usage

### Mobile Client

```python
from spacehey import MobileClient

client = MobileClient("YOUR_MOBILE_TOKEN")

# Post a Bulletin
client.post_bulletin(subject="Hello", content="Sent from Python!", duration="1d")


# Edit Profile (Blurbs + CSS)
# First, fetch current data to avoid overwriting with blanks
current = client.get_profile_editor_data()

# Modify what you want
current['about_me'] = "<p>Updated via API!</p>"
current['code'] = "body { background: black; color: green; }" # CSS

# Save
client.save_profile(current)

```

### Web Client

```python
from spacehey import WebClient

web = WebClient("YOUR_COOKIE_VALUE")

# Send an Instant Message
web.send_message(user_id=12345, content="Hey!")

```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
