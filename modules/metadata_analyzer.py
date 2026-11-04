from PIL import Image
from PIL.ExifTags import TAGS
import io


# ANALYZE IMAGE METADATA

def analyze_metadata(image, filename):

    try:
        # VALIDATE IMAGE

        if not isinstance(image, Image.Image):
            return {
                "error": "Please provide a valid image."
            }

        metadata = {}

        # BASIC IMAGE INFORMATION

        metadata["Filename"] = filename
        metadata["Format"] = image.format
        metadata["Dimensions"] = f"{image.width} x {image.height}"
        metadata["Width"] = image.width
        metadata["Height"] = image.height
        metadata["Color Mode"] = image.mode

        # CALCULATE PROCESSED IMAGE SIZE

        image_bytes = io.BytesIO()

        image.save(image_bytes, format="PNG")

        metadata["Processed Image Size"] = (
            f"{len(image_bytes.getvalue()) / 1024:.2f} KB"
        )

        # EXTRACT EXIF METADATA

        exif_information = {}

        try:
            exif_data = image.getexif()

            for tag_id, value in exif_data.items():

                tag_name = TAGS.get(tag_id, str(tag_id))

                exif_information[str(tag_name)] = str(value)

        except Exception:
            exif_information = {}

        metadata["EXIF Data"] = exif_information

        return metadata

    except Exception as error:
        return {
            "error": str(error)
        }