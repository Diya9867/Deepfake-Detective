import streamlit as st
import numpy as np
import onnxruntime as ort

from PIL import Image
from huggingface_hub import hf_hub_download


MODEL_NAME = "TensorFold/detectra-v1"

IMAGE_SIZE = 384
RESIZE_EDGE = 440

MEAN = np.array(
    [0.485, 0.456, 0.406],
    dtype=np.float32
)

STD = np.array(
    [0.229, 0.224, 0.225],
    dtype=np.float32
)


@st.cache_resource
def load_second_detector():

    model_path = hf_hub_download(
        repo_id=MODEL_NAME,
        filename="model.onnx"
    )

    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1

    session = ort.InferenceSession(
        model_path,
        sess_options=options,
        providers=["CPUExecutionProvider"]
    )

    input_name = session.get_inputs()[0].name

    return session, input_name


def preprocess_image(image):

    image = image.convert("RGB")

    width, height = image.size

    scale = RESIZE_EDGE / min(width, height)

    new_width = int(round(width * scale))
    new_height = int(round(height * scale))

    image = image.resize(
        (new_width, new_height),
        Image.Resampling.BILINEAR
    )

    left = (new_width - IMAGE_SIZE) // 2
    top = (new_height - IMAGE_SIZE) // 2

    image = image.crop(
        (
            left,
            top,
            left + IMAGE_SIZE,
            top + IMAGE_SIZE
        )
    )

    array = np.asarray(
        image,
        dtype=np.float32
    ) / 255.0

    array = (array - MEAN) / STD

    array = array.transpose(2, 0, 1)

    return np.ascontiguousarray(
        np.expand_dims(array, axis=0),
        dtype=np.float32
    )


def analyze_image_second(image):

    try:

        if not isinstance(image, Image.Image):
            return {"error": "Please provide a valid image."}

        session, input_name = load_second_detector()

        processed = preprocess_image(image)

        outputs = session.run(
            None,
            {input_name: processed}
        )

        logits = np.asarray(
            outputs[0],
            dtype=np.float32
        ).reshape(-1)

        if logits.size != 1 or not np.isfinite(logits[0]):
            return {"error": "Unexpected model output."}

        logit = float(logits[0])

        if logit >= 0:
            ai_probability = 1 / (1 + np.exp(-logit))
        else:
            exp_value = np.exp(logit)
            ai_probability = exp_value / (1 + exp_value)

        human_probability = 1 - ai_probability

        label = (
            "AI-generated"
            if ai_probability >= 0.5
            else "human"
        )

        results = [
            {
                "label": "AI-generated",
                "score": float(ai_probability)
            },
            {
                "label": "human",
                "score": float(human_probability)
            }
        ]

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return {
            "label": label,
            "confidence": max(
                ai_probability,
                human_probability
            ) * 100,
            "all_results": results,
            "model_name": MODEL_NAME,
            "assessment_note": (
                "Experimental AI-image screening. "
                "The score is not proof of authenticity."
            )
        }

    except Exception as error:

        return {"error": str(error)}