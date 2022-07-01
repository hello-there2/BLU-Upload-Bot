from UNIT3D_Image.DEFAULT import ImageHost as UNIT3D_I


class ImageHost(UNIT3D_I):
    host = "PStorage"
    base_url = "https://pstorage.space"
    file_param = "source"
    img_too_big_code = 413

    def __init__(self, config=None, section=None, debug=False):
        UNIT3D_I.__init__(self, config=config, section=section, debug=debug)
        self.headers["Referer"] = f"{self.base_url}/"
        self.upload_url = f"{self.base_url}/api/1/upload"
        self.payload["Content-Type"] = "application/json"
        self.payload["key"] = self.api_key
        self.upload_image = self.upload_image_v2
