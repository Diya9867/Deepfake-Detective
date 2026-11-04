from PIL import Image

from .image_detector_second import analyze_image_second


def analyze_image(image):

    try:

        if not isinstance(image, Image.Image):
            return {
                "error": "Please provide a valid image."
            }

        result = analyze_image_second(image)

        if "error" in result:
            return result

        return {
            "label": result["label"],
            "confidence": float(result["confidence"]),
            "all_results": [
                {
                    "label": item["label"],
                    "score": float(item["score"])
                }
                for item in result["all_results"]
            ],
            "model_name": result["model_name"],
            "label_mapping_verified": True,
            "assessment_note": result["assessment_note"]
        }

    except Exception as error:

        return {
            "error": str(error)
        }