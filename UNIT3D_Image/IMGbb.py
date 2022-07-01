from UNIT3D_Image.DEFAULT import ImageHost as UNIT3D_I


class ImageHost(UNIT3D_I):
    host = "IMGbb"
    base_url = "https://www.imgbb.com"
    file_param = "image"
    filename_param = "name"
    img_too_big_code = 400
    withData = True

    def __init__(self, config=None, section=None, debug=False):
        UNIT3D_I.__init__(self, config=config, section=section, debug=debug)
        self.headers["Referer"] = f"{self.base_url}/"
        self.upload_url = f"https://api.imgbb.com/1/upload?key={self.api_key}"
        self.payload["Content-Type"] = "application/json"
        self.payload["key"] = self.api_key
        self.upload_image = self.upload_image_v2
