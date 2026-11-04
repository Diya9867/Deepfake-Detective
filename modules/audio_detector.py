import streamlit as st
import numpy as np
import soundfile as sf
import io

from scipy.signal import resample_poly
from math import gcd
from transformers import pipeline


MODEL_NAME = "Shanmugapriya6/voice-fake-detector-v1"


@st.cache_resource
def load_audio_model():

    model = pipeline(
        "audio-classification",
        model=MODEL_NAME,
        device=-1
    )

    return model


def analyze_audio(audio_file):

    try:

        model = load_audio_model()

        # Read uploaded audio
        audio_bytes = audio_file.getvalue()

        audio, sr = sf.read(
            io.BytesIO(audio_bytes)
        )

        # Convert stereo to mono
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)

        # Convert to 16 kHz
        if sr != 16000:

            common = gcd(sr, 16000)

            audio = resample_poly(
                audio,
                16000 // common,
                sr // common
            )

            sr = 16000

        audio = audio.astype(np.float32)

        # Split audio into 10-second segments
        chunk_size = 16000 * 10

        predictions = []

        for start in range(0, len(audio), chunk_size):

            chunk = audio[start:start + chunk_size]

            if len(chunk) < 16000:
                continue

            result = model(
                {
                    "raw": chunk,
                    "sampling_rate": 16000
                },
                top_k=2
            )

            predictions.append(result)

        if not predictions:

            return {
                "error": "Audio is too short. Please upload at least 1 second of audio."
            }

        # Average classification scores
        scores = {}

        for result in predictions:

            for item in result:

                label = item["label"]

                scores.setdefault(label, [])

                scores[label].append(item["score"])

        averaged_scores = {
            label: float(np.mean(values))
            for label, values in scores.items()
        }

        # PROVISIONAL LABEL MAPPING
        # Based on the known human recording:
        # LABEL_0 = Human
        # LABEL_1 = AI

        human_score = averaged_scores.get("LABEL_0", 0)
        ai_score = averaged_scores.get("LABEL_1", 0)

        if ai_score > human_score:

            final_label = "AIVoice"
            confidence = ai_score * 100

        else:

            final_label = "HumanVoice"
            confidence = human_score * 100

        all_results = [
            {
                "label": "HumanVoice",
                "score": human_score
            },
            {
                "label": "AIVoice",
                "score": ai_score
            }
        ]

        return {
            "label": final_label,
            "confidence": confidence,
            "all_results": all_results,
            "model": MODEL_NAME,
            "assessment_note": (
                "Experimental result. Predictions may be inaccurate, "
                "especially for mixed, compressed or unfamiliar audio."
            )
        }

    except Exception as e:

        return {
            "error": str(e)
        }