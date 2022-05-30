from typing import Generator, BinaryIO
import os
import os.path as pth

from imagekitio import ImageKit
from werkzeug.utils import secure_filename

imagekit = ImageKit(
    private_key=os.getenv("IMAGEKIT_PRIVATE_KEY", "private_FaYgSFEErpK64vnKQgL9N+FWHOc="),
    public_key=os.getenv("IMAGEKIT_PUBLIC_KEY", "public_vSY3i045Esk9adgxknJARpYeXTg="),
    url_endpoint = os.getenv("IMAGEKIT_URL_ENDPOINT", "https://ik.imagekit.io/matthewwisdom/")
)

def upload_file(file_obj: BinaryIO, name: str, ext: str = "mp3", folder=""): #10mb
    try:
        res = imagekit.upload_file(
            file=file_obj,
            file_name= f"{name}.{ext}",
            options = {
                "folder" : folder,
                "tags": ["sample-tag"],
                "is_private_file": False,
                "use_unique_file_name": True,
            }
        )
        if res['error']:
            raise Exception(res['error'])
        res = res['response']
        return {"id": res["fileId"], "name": res["name"],
                 "url": res["url"]}
    except Exception as e:
        raise Exception(e)

def delete_file(file_id):
    try:
        res = imagekit.delete_file(file_id)
        if res["error"]:
            raise Exception(res['error'])
    except Exception as e:
        raise Exception(e)
    return res

class ImageKit:
    def __init__(self) -> None:
        """
            Object for storing files locally            
        """
        pass
    
    def upload_media(self, file_object: BinaryIO, name: str,
                     extension: str = "mp3", playlist: str = '') -> dict:
        """
            Save file with content `byte_content`
            using `name` and `extension` to imagekit.
        """
        data = upload_file(file_object, name, extension, folder=playlist)
        return data
    
    def delete_media(self, fileId):
        """
            Delete fie represented by `name` and `playlist`
        """
        delete_file(fileId)
    
    def get_media(self, name: str, playlist: str = '') -> bytes:
        """
            Locate file and return the content in bytes.
        """
        raise NotImplemented
    
    def stream_media(self, name: str, playlist: str = '', 
                     chunk_size: int = 1024) -> Generator[bytes, None, None]:
        """
            Return a generator to stream file content
        """
        raise NotImplemented

