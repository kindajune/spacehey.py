from .public import SpaceHeyPublic
import os
from bs4 import BeautifulSoup
import re

class WebClient(SpaceHeyPublic):
    """
    authenticated actions. requires SPACEHEY_SESSID (cookie).
    inherits from SpaceHeyPublic so you can still do read-only stuff.
    """
    IM_API_URL = "https://im.spacehey.com/api_v2"
    
    LINK_KEYS = [
        "instagram", "twitter", "youtube", "tumblr", "twitch", "facebook", 
        "tiktok", "github", "reddit", "snapchat", "dribbble", "pinterest", 
        "spotify", "soundcloud", "lastfm", "deviantart", "behance", "vsco", 
        "ello", "letterboxd", "bereal", "mastodon", "threads", "bluesky", 
        "linktree", "producthunt", "telegram", "patreon", "paypal", 
        "buymeacoffee", "kofi", "website"
    ]

    def __init__(self, session_id):
        if not session_id:
            raise ValueError("session_id is required for user actions")
        super().__init__()
        self.session.headers.update({
            "Cookie": f"SPACEHEY_SESSID={session_id}",
            "Referer": "https://spacehey.com/",
            # mimic a real browser to avoid simple bot detection
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0"
        })

    def _im_request(self, data):
        """internal helper for the IM api."""
        response = self.session.post(self.IM_API_URL, data=data)
        response.raise_for_status()
        
        json_data = response.json()
        if not json_data.get("ok"):
            raise Exception(f"IM API Error: {json_data}")
            
        return json_data.get("data")

    def _parse_html_response(self, html_text):
        """
        parses generic spacehey success/error messages.
        returns (is_success, message_text)
        """
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # check for error
        error_tag = soup.find('p', class_='error')
        if error_tag:
            return False, error_tag.get_text(strip=True)
            
        # check for success
        success_tag = soup.find('p', class_='success')
        if success_tag:
            return True, success_tag.get_text(strip=True)
            
        # fallback
        return False, "unknown response status"

    # --- IM API Methods ---

    def get_self(self):
        return self._im_request({"action": "get_self"})

    def get_conversations(self, page=1):
        return self._im_request({"action": "get_conversations", "page": page, "filter": ""})

    def get_messages(self, user_id, last_time=0, include_user_data=False):
        return self._im_request({
            "action": "get_messages",
            "user": user_id,
            "last_time": last_time,
            "include_user_data": str(include_user_data).lower()
        })

    def send_message(self, user_id, content):
        return self._im_request({"action": "send_message", "user": user_id, "content": content})

    # --- Web Actions ---

    def update_settings(self, email, name, username, show_online=True, im_privacy='everyone', profile_visibility='public'):
        data = {
            "email": email, "name": name, "username": username,
            "im_privacy": im_privacy, "profile_visibility": profile_visibility,
            "submit": ""
        }
        if show_online:
            data["show_online"] = "on"
            
        resp = self.session.post(f"{self.BASE_URL}/settings", data=data)
        resp.raise_for_status()
        success, msg = self._parse_html_response(resp.text)
        return {"success": success, "message": msg}

    def kick_session(self, session_id):
        data = {"logout_session[]": session_id, "submit": ""}
        resp = self.session.post(f"{self.BASE_URL}/settings", data=data)
        resp.raise_for_status()
        success, msg = self._parse_html_response(resp.text)
        return {"success": success, "message": msg}

    def update_status_details(self, status, mood, you):
        data = {
            "category[status]": status[:65],
            "category[mood]": mood[:65],
            "category[you]": you[:65],
            "submit": ""
        }
        resp = self.session.post(f"{self.BASE_URL}/editstatus", data=data)
        resp.raise_for_status()
        success, msg = self._parse_html_response(resp.text)
        return {"success": success, "message": msg}

    def update_links(self, links_dict):
        data = {"submit": ""}
        for key in self.LINK_KEYS:
            val = links_dict.get(key, "")
            data[f"category[{key}]"] = val

        resp = self.session.post(f"{self.BASE_URL}/editlinks", data=data)
        resp.raise_for_status()
        success, msg = self._parse_html_response(resp.text)
        return {"success": success, "message": msg}

    def update_profile_picture(self, file_path=None, delete=False):
        url = f"{self.BASE_URL}/editphoto"
        if delete:
            resp = self.session.post(url, data={"action": "delete", "submit": ""})
        elif file_path:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"image not found: {file_path}")
            with open(file_path, 'rb') as f:
                resp = self.session.post(url, files={'photo': f}, data={'submit': ''})
        else:
            return {"success": False, "message": "no file or delete action specified"}
        resp.raise_for_status()
        success, msg = self._parse_html_response(resp.text)
        return {"success": success, "message": msg}

    def export_data(self):
        resp = self.session.get(f"{self.BASE_URL}/export")
        resp.raise_for_status()
        return resp.json()

    # --- Bulletin Actions ---

    def create_bulletin(self, subject, content, duration="10d", allow_comments=True):
        if duration not in ["1d", "5d", "10d"]:
            raise ValueError("duration must be '1d', '5d', or '10d'")

        data = {
            "subject": subject, "content": content, "duration": duration,
            "comments": "enabled" if allow_comments else "disabled",
            "submit": ""
        }
        resp = self.session.post(f"{self.BASE_URL}/createbulletin", data=data)
        resp.raise_for_status()
        
        success, msg = self._parse_html_response(resp.text)
        result = {"success": success, "message": msg, "id": None}
        
        if success:
            soup = BeautifulSoup(resp.text, 'html.parser')
            link = soup.find('a', href=re.compile(r'/bulletin\?id=\d+'))
            if link:
                match = re.search(r'id=(\d+)', link['href'])
                if match:
                    result['id'] = int(match.group(1))
        return result

    def delete_bulletin(self, bulletin_id):
        url = f"{self.BASE_URL}/deletebulletin"
        resp = self.session.post(url, params={"id": bulletin_id}, data={"submit": ""})
        resp.raise_for_status()
        success, msg = self._parse_html_response(resp.text)
        return {"success": success, "message": msg}

    def add_bulletin_comment(self, bulletin_id, text, reply_to_id=None):
        """
        posts a comment and verifies success by checking the comments list for the newest entry by the current user.
        """
        # 0. Get current user ID for verification
        try:
            me = self.get_self()
            my_id = me['user']['id']
        except Exception as e:
            return {"success": False, "message": f"Could not fetch user info for verification: {e}", "id": None}

        url = f"{self.BASE_URL}/addbulletincomment"
        params = {"id": bulletin_id}
        
        if reply_to_id:
            params["reply"] = reply_to_id
            referer = f"{self.BASE_URL}/addbulletincomment?id={bulletin_id}&reply={reply_to_id}"
        else:
            referer = f"{self.BASE_URL}/bulletin?id={bulletin_id}"
            
        headers = {
            "Referer": referer,
            "Origin": "https://spacehey.com",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
            
        # 1. Post Blindly (ignoring result content as it might redirect to login)
        try:
            self.session.post(url, params=params, data={"comment": text, "submit": ""}, headers=headers)
        except Exception:
            pass # ignore network errors on post, verification step will catch failure
            
        # 2. Verification: Fetch Comments List
        list_url = f"{self.BASE_URL}/bulletincomments"
        list_params = {"id": bulletin_id}
        resp = self.session.get(list_url, params=list_params)
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        result = {"success": False, "message": "Verification failed - comment not found", "id": None}
        
        # 3. Find newest comment/reply
        candidates = []
        
        # Helper to extract ID from profile link
        def get_uid(link):
            if link and link.has_attr('href'):
                m = re.search(r'id=(\d+)', link['href'])
                if m: return int(m.group(1))
            return None

        # Helper to extract Comment ID
        def get_cid(link):
            if link and link.has_attr('href'):
                # Try bulletincomment?id=XXX
                m = re.search(r'[?&]id=(\d+)', link['href'])
                if m: return int(m.group(1))
                # Try comment=XXX (delete links)
                m = re.search(r'comment=(\d+)', link['href'])
                if m: return int(m.group(1))
            return None

        for t in soup.find_all('time', class_='ago'):
            try:
                # Get timestamp (prefer data-timestamp, fallback to text)
                if t.has_attr('data-timestamp'):
                    ts = int(t['data-timestamp'])
                else:
                    ts = int(t.get_text(strip=True))
                
                found_uid = None
                found_cid = None
                
                # Check A: Top-level comment (time is in a td, user info in previous td)
                row = t.find_parent('tr')
                if row:
                    user_td = row.find('td')
                    if user_td:
                        user_link = user_td.find('a', href=re.compile(r'profile\?id='))
                        found_uid = get_uid(user_link)
                
                # Check B: Reply (time is in a div.comment-reply)
                reply_div = t.find_parent('div', class_='comment-reply')
                if reply_div:
                    user_link = reply_div.find('a', href=re.compile(r'profile\?id='))
                    found_uid = get_uid(user_link)
                
                # Match against logged-in user
                if found_uid == my_id:
                    # Extract ID: try parent anchor first (permalink)
                    parent_a = t.find_parent('a', href=True)
                    if parent_a:
                        found_cid = get_cid(parent_a)
                    
                    # If no permalink, search container for delete/report links
                    if not found_cid:
                        container = reply_div if reply_div else row
                        if container:
                            # Look for delete link
                            del_link = container.find('a', href=re.compile(r'deletebulletincomment'))
                            if del_link:
                                found_cid = get_cid(del_link)
                            # Fallback to report link
                            if not found_cid:
                                rep_link = container.find('a', href=re.compile(r'type=bulletin_comment'))
                                found_cid = get_cid(rep_link)
                    
                    if found_cid:
                        candidates.append((ts, found_cid))

            except (ValueError, AttributeError):
                continue
                
        if candidates:
            # Sort by timestamp descending
            candidates.sort(key=lambda x: x[0], reverse=True)
            result['success'] = True
            result['message'] = "Comment verified on list"
            result['id'] = candidates[0][1]

        return result

    def delete_bulletin_comment(self, bulletin_id, comment_id):
        url = f"{self.BASE_URL}/deletebulletincomment"
        params = {"id": bulletin_id, "comment": comment_id}
        resp = self.session.post(url, params=params, data={"submit": ""})
        resp.raise_for_status()
        success, msg = self._parse_html_response(resp.text)
        return {"success": success, "message": msg}

    # legacy alias
    def post_bulletin(self, title, body):
        return self.create_bulletin(title, body)

    def send_friend_request(self, user_id):
        pass