from pathlib import Path
import tempfile

from .integrated_inspection import inspect_image


def inspect_uploaded_image(image_bytes):
    

    
    with tempfile.NamedTemporaryFile(
        suffix=".png",
        delete=False
    ) as temp_file:

        temp_file.write(image_bytes)
        temp_path = Path(temp_file.name)

    try:
        
        result = inspect_image(temp_path)

        return result

    finally:
        
        if temp_path.exists():
            temp_path.unlink()