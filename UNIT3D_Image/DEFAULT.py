"""
This is to be used alongside the UNIT3D auto uploader.
You can define how to upload to different image hosts.
"""

import constants
import requests
import re
import pybase64
import configparser
import os


class ImageHost:
    host = "Base64 Encoded images."
    headers = {"User-Agent": f"UNIT3D API Uploader v{constants.UNIT3D_VERSION}"}
    payload = {"format": "json"}
    base_url = "https://www.myurl.com"
    file_param = "file"
    filename_param = "filename"
    url_viewer = "url_viewer"
    response_url = "url"
    img_too_big_code = 400
    withData = False
    data_name = "data"
    gallery_name = None
    # A list of dictionaries. {"filename": fn, "viewer": vw, "direct": dr, "path": pth}
    # Can have more if the host supports them.
    images = []

    def __init__(self, config=None, section=None, debug=False):
        if not config or not section:
            self = None
        self.debug = debug
        self.width = None
        self.height = None
        self.config = config
        self.config_section = section
        self.upload_url = f"{self.base_url}/upload.php"
        self.read_config()

    def __repr__(self):
        return str(images)

    def __str__(self):
        return str(self.generate_bbcode())

    def read_config(self):
        self.api_key = self.config[self.config_section].get("api key", None)
        self.api_user = self.config[self.config_section].get("api user", None)
        self.username = self.config[self.config_section].get("username", None)
        self.password = self.config[self.config_section].get("password", None)
        if not self.width:
            self.width = self.config[self.config_section].getint(
                "image width", constants.IMAGE_WIDTH
            )
        if not self.height:
            self.height = self.width

    def upload_images(self, files=[], addToList=True, asB64=False):
        uploaded_images = []
        for file in files:
            try:
                upload = None
                if asB64:
                    upload = self.upload_image_b64(file=file, addToList=addToList)
                else:
                    upload = self.upload_image(file=file, addToList=addToList)
                if upload:
                    uploaded_images += upload
            except Exception as e:
                print(f'File: "{file}" failed to upload.')
                if self.debug:
                    print(e)
        return uploaded_images

    def image_to_b64(self, file):
        image_b64 = str(pybase64.b64encode(open(file, "rb").read()))[:-1]
        image_b64 = image_b64[2:]
        return image_b64

    def upload_image_b64(self, file, addToList=True):
        image_b64 = self.image_to_b64(file)
        url_encoded_image = f"data:image/png;base64,{image_b64}"
        image_dict = {
            "filename": os.path.basename(file),
            "viewer": url_encoded_image,
            "direct": url_encoded_image,
            "path": file,
        }
        if addToList:
            self.images.append(image_dict)
        return image_dict

    def upload_image(self, file, addToList=True):
        files = [(self.file_param, open(file, "rb"))]
        upload = requests.request(
            "POST",
            self.upload_url,
            headers=self.headers,
            data=self.payload,
            files=files,
        )
        image_urls = self.response_to_urls(response=upload)
        if not image_urls:
            return None
        image_dict = {
            "filename": os.path.basename(file),
            "viewer": image_urls["viewer"],
            "direct": image_urls["direct"],
            "path": file,
        }
        if addToList:
            self.images.append(image_dict)
        print(f'Uploaded "{file}" to {self.host}')
        return image_dict

    def upload_image_v2(self, file, addToList=True):
        image_b64 = self.image_to_b64(file)
        self.payload[self.filename_param] = os.path.basename(file)
        self.payload[self.file_param] = f"{image_b64}\n"
        upload = requests.post(url=self.upload_url, data=self.payload)
        image_urls = self.response_to_urls(response=upload)
        if not image_urls:
            return None
        image_dict = {
            "filename": os.path.basename(file),
            "viewer": image_urls["viewer"],
            "direct": image_urls["direct"],
            "path": file,
        }
        if addToList:
            self.images.append(image_dict)
        print(f'Uploaded "{file}" to {self.host}')
        return image_dict

    def response_to_urls_same(self, response):
        if not self.check_response(response):
            return None
        response = response.json()
        image_url = f"{self.base_url}/{response[0]['code']}.{response[0]['ext']}"
        return {"viewer": image_url, "direct": image_url}

    def response_to_urls(self, response):
        if not self.check_response(response):
            return None
        response = response.json()
        # Allows the response to get the 'data' part.
        if self.withData:
            response = response[self.data_name]
        return {
            "viewer": response[self.url_viewer],
            "direct": response[self.response_url],
        }

    def check_response(self, response):
        if response.status_code == self.img_too_big_code:
            print("File too big... confinuing...")
            return False
        if response.status_code >= 300:
            print("Unknown error... please report")
            print("---------------------------------------------")
            print(response)
            print("---------------------------------------------")
            return False
        return True

    def generate_bbcode(self, useSize=True, altImage=None, altUrl=None):
        bbcode = ""
        for image in self.images:
            if not altUrl:
                image_bbcode = f"[url={image.get('viewer')}]"
            else:
                image_bbcode = f"[url={image.get(altUrl)}]"
            if useSize:
                image_bbcode += f"[img={self.width}]"
            else:
                image_bbcode += "[img]"
            if not altImage:
                image_bbcode += f"{image.get('direct')}"
            else:
                image_bbcode += f"{image.get(altImage)}"
            image_bbcode += "[/img][/url]"
            bbcode += image_bbcode
        return bbcode

    def get_images(self):
        return self.images

    def set_gallery_name(self, name):
        self.gallery_name = name
