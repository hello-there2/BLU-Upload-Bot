from UNIT3D_Image.DEFAULT import ImageHost as UNIT3D_I
import requests, re, os


class ImageHost(UNIT3D_I):
    host = "ImgBox"
    base_url = "https://imgbox.com/"
    session = None
    gallery = None
    csrf = None
    img_too_big_code = 400
    url_viewer = "url"
    response_url = "original_url"

    def __init__(self, config=None, section=None, debug=False):
        UNIT3D_I.__init__(self, config=config, section=section, debug=debug)
        self.headers["Referer"] = f"{self.base_url}/index.php"

    def login(self):
        if self.session:
            return self.session
        self.session = requests.Session()
        self.csrf = re.search(
            '<meta content="(.+?)" name="csrf-token" />',
            self.session.get(f"{self.base_url}/login").text,
        ).group(1)
        imgbox_login = self.session.post(
            f"{self.base_url}/login",
            data={
                "utf8": "✓",
                "authenticity_token": self.csrf,
                "user[login]": self.username,
                "user[password]": self.password,
            },
        )

    def create_gallery(self, name):
        self.gallery = self.session.post(
            f"{self.base_url}/ajax/token/generate",
            data={"gallery": "true", "gallery_title": name, "comments_enabled": "0"},
            cookies={"request_method": "POST"},
            headers={
                "X-csrf-Token": self.csrf,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": self.base_url,
            },
        )
        self.gallery = self.gallery.json()

    def upload_image(self, file, addToList=True):
        if not self.session:
            self.login()
        if not self.gallery:
            if not self.gallery_name:
                self.create_gallery(os.path.basename(file))
            else:
                self.create_gallery(self.gallery_name)
        upload = self.session.post(
            f"{self.base_url}/upload/process",
            files={"files[]": (str(file), open(str(file), "rb"), "image/png")},
            data={
                "token_id": self.gallery["token_id"],
                "token_secret": self.gallery["token_secret"],
                "content_type": "1",
                "thumbnail_size": "300r",
                "gallery_id": self.gallery["gallery_id"],
                "gallery_secret": self.gallery["gallery_secret"],
                "comments_enabled": "0",
            },
            cookies={"request_method": "POST"},
            headers={
                "X-CSRF-Token": self.csrf,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": self.base_url,
            },
        )
        image_urls = self.response_to_urls(response=upload)
        image_dict = {
            "filename": os.path.basename(file),
            "viewer": image_urls["viewer"],
            "direct": image_urls["direct"],
            "path": file,
        }
        if not image_urls:
            return None
        if addToList:
            self.images.append(image_dict)
        print(f'Uploaded "{file}" to {self.host}')

    def response_to_urls(self, response):
        if not self.check_response(response):
            return None
        response = response.json()["files"][0]
        return {
            "viewer": response[self.url_viewer],
            "direct": response[self.response_url],
        }
