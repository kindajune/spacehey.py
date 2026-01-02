import requests

class HTTPClient:
    """
    handles raw http requests.
    """
    WEB_BASE = "https://spacehey.com"
    API_BASE = "https://api.spacehey.com/v1"

    def __init__(self, token=None):
        self.session = requests.Session()
        
        # default headers for scraping (web)
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (SpaceheyPy; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        self.token = token
        if token:
            # api headers mimic the android app
            self.api_headers = {
                "User-Agent": "SpaceHey/1.6.0 (net.tibush.spacehey; build:99; SpaceheyPy 14)",
                "X-Client-Id": "app-android",
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
        else:
            self.api_headers = {}

    def request(self, method, endpoint, use_api=False, **kwargs):
        """
        internal request handler.
        use_api=True toggles between spacehey.com (scraping) and api.spacehey.com (json).
        """
        base = self.API_BASE if use_api else self.WEB_BASE
        url = f"{base}{endpoint}"
        
        # merge headers if using api
        headers = kwargs.pop("headers", {})
        if use_api:
            if not self.token:
                raise Exception("cannot use api endpoints without a token")
            headers.update(self.api_headers)
        
        try:
            response = self.session.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"error requesting {url}: {e}")
            raise e