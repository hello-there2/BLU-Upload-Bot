from UNIT3D_Image.DEFAULT import ImageHost as UNIT3D_I


class ImageHost(UNIT3D_I):
    host = "BTN ImgBin"
    base_url = "https://imgbin.broadcasthe.net"
    file_param = "file"

    def __init__(self, config=None, section=None, debug=False):
        UNIT3D_I.__init__(self, config=config, section=section, debug=debug)
        self.headers["Authorization"] = f"Bearer {self.api_key}"
        self.upload_url = f"{self.base_url}/upload"
        self.headers["Referer"] = self.upload_url
        self.response_to_urls = self.btn_imgbin

    def btn_imgbin(self,response):
        if not self.check_response(response):
            return None
        response = response.json()
        img_json = response[list(response.keys())[0]]
        image_url = img_json["hotlink"]
        viewer_url = img_json["location"]
        return {"viewer": viewer_url, "direct": image_url}

