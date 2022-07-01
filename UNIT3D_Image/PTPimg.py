from UNIT3D_Image.DEFAULT import ImageHost as UNIT3D_I


class ImageHost(UNIT3D_I):
    host = "PTPImg"
    base_url = "https://ptpimg.me"
    file_param = "file-upload[0]"

    def __init__(self, config=None, section=None, debug=False):
        UNIT3D_I.__init__(self, config=config, section=section, debug=debug)
        self.payload["api_key"] = self.api_key
        self.headers["Referer"] = f"{self.base_url}/index.php"
        self.response_to_urls = self.response_to_urls_same
