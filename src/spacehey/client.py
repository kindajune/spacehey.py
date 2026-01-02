from .core import HTTPClient
from bs4 import BeautifulSoup

class MobileClient(HTTPClient):
    """
    authenticated client using the official mobile api (v1).
    requires a JWT token (obtainable via login flow or sniffing).
    """
    IM_API_URL = "https://im.spacehey.com/api_v2"

    def __init__(self, token):
        if not token:
            raise ValueError("token is required for user actions")
        super().__init__(token=token)

    def _api_call(self, method, endpoint, json=None, data=None, files=None):
        """helper to parse json responses from the api"""
        resp = self.request(method, endpoint, use_api=True, json=json, data=data, files=files)
        
        # DELETE requests often return empty bodies on success
        if resp.status_code == 204 or not resp.content:
            return True

        try:
            return resp.json().get("data", {})
        except:
            return resp.text

    def _im_request(self, data):
        """internal helper for the IM api (using mobile token auth)."""
        # im api is separate from the main v1 api, so we request it directly

        try:
            resp = self.session.post(self.IM_API_URL, data=data, headers=self.api_headers)
            resp.raise_for_status()
            
            json_data = resp.json()
            if not json_data.get("ok"):
                raise Exception(f"IM API Error: {json_data}")
                
            return json_data.get("data")
        except Exception as e:
            raise e

    # --- User & Profile ---

    def get_self(self):
        """get own profile and stats."""
        return self._api_call("GET", "/users/me")

    def get_profile(self, user_id):
        """get any user's profile info."""
        return self._api_call("GET", f"/users/{user_id}/profile")

    def update_status(self, status, mood, you):
        """
        update the header status fields.
        uses multipart form data.
        """
        # passing as 'files' forces multipart/form-data which the api expects
        payload = {
            "status": (None, status),
            "mood": (None, mood),
            "you": (None, you)
        }
        return self._api_call("POST", "/users/me/status", files=payload)
        
    def get_profile_editor_data(self):
        """
        fetches the current profile data (blurbs + layout/css) exactly as it appears in the mobile editor.
        useful to get current data before editing, so you don't overwrite fields with empty strings.
        returns a dict.
        """
        # this endpoint returns html with the data pre-filled in textareas
        resp = self.request("GET", "/hosted/editprofile", use_api=True)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        fields = [
            "about_me", "meet", "general", "music", "movies", 
            "television", "books", "heroes", "code"
        ]
        
        data = {}
        for field in fields:
            # find textarea by name attribute
            node = soup.find('textarea', attrs={'name': field})
            if node:
                data[field] = node.get_text()
            else:
                data[field] = ""
                
        return data

    def save_profile(self, details):
        """
        update profile blurbs, interests, AND layout (css).
        
        details: dict containing any of:
                 'about_me', 'meet', 'general', 'music', 'movies', 
                 'television', 'books', 'heroes', 'code' (layout/css)
        """
        # map dict to multipart format
        # keys must match the form-data names exactly
        files = {k: (None, v) for k, v in details.items()}
        return self._api_call("POST", "/users/me/profile", files=files)

    def update_settings(self, settings):
        """
        update account settings (email, name, privacy, etc).
        """
        files = {k: (None, str(v)) for k, v in settings.items()}
        return self._api_call("POST", "/account/settings", files=files)

    # --- Social ---

    def search_users(self, query):
        return self._api_call("GET", "/search/users", params={"q": query})

    def get_friends(self, user_id, limit=25, offset=0):
        return self._api_call("GET", f"/users/{user_id}/friends", params={"limit": limit, "offset": offset})

    def send_friend_request(self, user_id):
        """
        sends a friend request. NO CAPTCHA required on v1 api.
        """
        return self._api_call("POST", f"/users/{user_id}/addfriend")

    def get_friend_requests(self):
        return self._api_call("GET", "/requests")

    def accept_friend_request(self, user_id):
        return self._api_call("POST", f"/requests/{user_id}/accept")

    def decline_friend_request(self, user_id):
        return self._api_call("POST", f"/requests/{user_id}/decline")

    def block_user(self, user_id):
        return self._api_call("POST", f"/users/{user_id}/block")

    # --- Instant Messaging ---

    def get_conversations(self, page=1):
        """get list of active DM conversations."""
        return self._im_request({"action": "get_conversations", "page": page, "filter": ""})

    def get_messages(self, user_id, last_time=0, include_user_data=False):
        """
        get messages with a specific user.
        last_time: timestamp to fetch messages after.
        """
        return self._im_request({
            "action": "get_messages",
            "user": user_id,
            "last_time": last_time,
            "include_user_data": str(include_user_data).lower()
        })

    def send_message(self, user_id, content):
        """send a DM to a user."""
        return self._im_request({"action": "send_message", "user": user_id, "content": content})

    # --- Bulletins ---

    def get_bulletins(self, limit=25, offset=0):
        return self._api_call("GET", "/bulletins", params={"limit": limit, "offset": offset})

    def post_bulletin(self, subject, content, duration="10d", allow_comments=True):
        """
        duration: '1d', '5d', '10d'
        """
        files = {
            "subject": (None, subject),
            "content": (None, content),
            "duration": (None, duration),
            "comments": (None, "enabled" if allow_comments else "disabled")
        }
        return self._api_call("POST", "/bulletins/new", files=files)

    def delete_bulletin(self, bulletin_id):

        return self._api_call("DELETE", f"/bulletins/{bulletin_id}")

    # --- Blogs ---

    def get_blog_posts(self, category_id=None, limit=25, offset=0):
        if category_id:
            return self._api_call("GET", f"/blog/category/{category_id}", params={"limit": limit, "offset": offset})
        return self._api_call("GET", "/blog/recent", params={"limit": limit, "offset": offset})

    def post_blog_entry(self, subject, content, category_id, privacy="public", allow_comments=True):
        """
        privacy: 'public', 'friends', 'diary' (private)
        """
        files = {
            "subject": (None, subject),
            "content": (None, content),
            "category": (None, str(category_id)),
            "privacy": (None, privacy),
            "comments": (None, "enabled" if allow_comments else "disabled")
        }
        return self._api_call("POST", "/blog/new", files=files)

    def delete_blog_entry(self, blog_id):
        return self._api_call("DELETE", f"/blog/{blog_id}")

    # --- Comments ---

    def post_comment(self, target_type, target_id, text):
        """
        post a comment on a blog or bulletin.
        target_type: 'blog', 'bulletin', 'profile' (maybe?)
        """
        # mimics the XHR FormData behavior found in source
        files = {"comment": (None, text)}
        return self._api_call("POST", f"/comments/{target_type}/{target_id}/new", files=files)

    # --- Auth ---
    
    def validate_token(self):
        return self._api_call("GET", "/auth/validate")
        
    def logout(self):
        return self._api_call("POST", "/auth/invalidate")

