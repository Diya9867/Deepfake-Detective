import os
import pathlib
import tempfile

import streamlit as st
import cv2


# WINDOWS DLL CONFIGURATION
# Helps TorchCodec locate FFmpeg and PyTorch DLL files.

FFMPEG_BIN = (
    r"C:\Users\Umeshchandra\Downloads"
    r"\ffmpeg-9.0.2-full_build-shared\bin"
)

os.environ["PATH"] = (
    FFMPEG_BIN + os.pathsep + os.environ.get("PATH", "")
)

_DLL_DIRECTORY_HANDLES = []

if os.name == "nt" and os.path.isdir(FFMPEG_BIN):
    _DLL_DIRECTORY_HANDLES.append(
        os.add_dll_directory(FFMPEG_BIN)
    )


import torch

TORCH_LIB = os.path.join(
    os.path.dirname(torch.__file__),
    "lib"
)

if os.name == "nt" and os.path.isdir(TORCH_LIB):
    _DLL_DIRECTORY_HANDLES.append(
        os.add_dll_directory(TORCH_LIB)
    )


# CAKELENS IMPORTS

from cakelens.model import Model
from cakelens.detect import Detector
from cakelens.data_types import Label


MODEL_LABELS = list(Label)

AI_LABELS = {
    "AI_GEN",
    "KLING",
    "HIGGSFIELD",
    "WAN",
    "MIDJOURNEY",
    "HAILUO",
    "RAY",
    "VEO",
    "RUNWAY",
    "SORA",
    "CHATGPT",
    "PIKA",
    "HUNYUAN",
    "VIDU",
}

SAMPLED_FRAME_COUNT = 9


@st.cache_resource
def load_video_model():

    model = Model()

    model.load_from_huggingface_hub(
        device="cpu"
    )

    detector = Detector(
        model=model,
        batch_size=1,
        device="cpu"
    )

    return detector


def analyze_video(video_bytes):

    temporary_paths = []

    try:

        if not video_bytes:
            return {
                "error": "No video was provided."
            }

        # SAVE ORIGINAL VIDEO

        with tempfile.NamedTemporaryFile(
            suffix=".mp4",
            delete=False
        ) as file:

            file.write(video_bytes)

            original_path = pathlib.Path(file.name)

            temporary_paths.append(original_path)

        # READ VIDEO INFORMATION

        capture = cv2.VideoCapture(
            str(original_path)
        )

        if not capture.isOpened():
            return {
                "error": "Unable to open this video."
            }

        total_frames = int(
            capture.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        fps = capture.get(
            cv2.CAP_PROP_FPS
        )

        duration = (
            total_frames / fps
            if fps and fps > 0
            else 0
        )

        if total_frames < SAMPLED_FRAME_COUNT:

            capture.release()

            return {
                "error": "Please upload a video containing at least 9 readable frames."
            }

        width = int(
            capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        )

        height = int(
            capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        )

        width -= width % 2
        height -= height % 2

        if width <= 0 or height <= 0:

            capture.release()

            return {
                "error": "Invalid video dimensions."
            }

        # SELECT 9 FRAMES UNIFORMLY

        frame_indices = [
            round(
                i * (total_frames - 1)
                / (SAMPLED_FRAME_COUNT - 1)
            )
            for i in range(SAMPLED_FRAME_COUNT)
        ]

        # CREATE TEMPORARY SAMPLED VIDEO

        with tempfile.NamedTemporaryFile(
            suffix=".mp4",
            delete=False
        ) as file:

            sampled_path = pathlib.Path(file.name)

        temporary_paths.append(sampled_path)

        output_fps = (
            fps if fps > 0 else 25.0
        )

        writer = cv2.VideoWriter(
            str(sampled_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            output_fps,
            (width, height)
        )

        if not writer.isOpened():

            capture.release()
            writer.release()

            return {
                "error": "Unable to create the sampled video."
            }

        sampled_count = 0

        try:

            for frame_index in frame_indices:

                capture.set(
                    cv2.CAP_PROP_POS_FRAMES,
                    frame_index
                )

                success, frame = capture.read()

                if not success:
                    continue

                frame = cv2.resize(
                    frame,
                    (width, height)
                )

                writer.write(frame)

                sampled_count += 1

        finally:

            capture.release()
            writer.release()

        if sampled_count != SAMPLED_FRAME_COUNT:

            return {
                "error": "Unable to extract all 9 sampled frames."
            }

        # LOAD CAKELENS V5 MODEL

        detector = load_video_model()

        # ANALYSE SAMPLED VIDEO

        verdict = detector.detect(
            sampled_path
        )

        # CONVERT SCORES INTO PERCENTAGES

        predictions = {}

        for label, score in zip(
            MODEL_LABELS,
            verdict.predictions
        ):

            predictions[label.value] = (
                float(score) * 100
            )

        if not predictions:

            return {
                "error": "The model returned no predictions."
            }

        # SORT RESULTS

        all_results = sorted(
            [
                {
                    "label": label,
                    "score": score / 100
                }
                for label, score in predictions.items()
            ],
            key=lambda item: item["score"],
            reverse=True
        )

        # FIND STRONGEST AI-GENERATION SIGNAL

        ai_scores = [
            score
            for label, score in predictions.items()
            if label in AI_LABELS
        ]

        ai_score = (
            max(ai_scores)
            if ai_scores
            else 0.0
        )

        if ai_score >= 50:

            result_label = (
        "Strong AI-generation signal detected"
    )

        elif ai_score >= 40:
            result_label = (
        "Possible AI-generation signal detected"
    )

        else:

            result_label = (
        "No strong AI-generation signal detected"
    )

        return {

            "label": result_label,

            "confidence": ai_score,

            "ai_generation_score": ai_score,

            "duration": duration,

            "frames_analyzed": sampled_count,

            "original_frame_count": total_frames,

            "flagged_percentage": ai_score,

            "all_results": all_results,

            "model": "CakeLens V5",

            "analysis_mode": "Limited-Sample Analysis",

            "warnings": [

                "A low score does not prove that a video is authentic.",

                "This model is not a universal detector of all video manipulations."

            ]

        }

    except Exception as error:

        return {
            "error": str(error)
        }

    finally:

        for path in temporary_paths:

            if path.exists():
                path.unlink()