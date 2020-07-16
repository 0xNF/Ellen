import base64
import os
from PIL import Image  

class Config():
    """ Configuration object that dictates the details for how the saved IVAR data is stored """
    def __init__(self, store_full_json: bool, store_image: bool, store_image_kind: str, max_size: int, max_records: int, max_days: int, save_path: str):
        self.STORE_FULL_JSON: bool = store_full_json
        self.STORE_IMAGE: bool = store_image
        self.STORE_IMAGE_KIND: str = store_image_kind
        self.MAX_SIZE: int = max_size
        self.MAX_RECORD_COUNT: int = max_records
        self.MAX_KEEP_DAYS: int = max_days
        self.SAVE_PATH: str = save_path


class Candidate():
    """ simplified Gorilla candidate containing only its gorilla id, display name, and score """
    def __init__(self, id: int, display: str, score: float):
        self.Id: int = id
        self.DisplayName: str = display
        self.SimiliarityScore: float = score

class GImage():
    """ simplified Gorilla image data """
    def __init__(self, ext: str, fname: str, b64: str):
        self.Ext: str = ext
        self.FName: str = fname
        self.B64: str = b64


def dump_b64_img_to_file(b64: str, path: str):
    """ Takes a b64 encoded jpeg, decodes it, and saves it to the specified path """
    file = base64.b64decode(b64)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(file)
    return

def resize_image(path: str, square_size_px: int):
    """ resizes the image at path to be a square image of pixel dimensions square_size_px """
    im: Image = Image.open(path)
    im = im.resize((square_size_px, square_size_px))
    im.save(path)
    return
