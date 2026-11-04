import streamlit as st
from PIL import Image
from io import BytesIO
from xml.sax.saxutils import escape


from modules.video_detector import analyze_video
from modules.audio_detector import analyze_audio
from modules.news_verifier import extract_article
from modules.image_detector import analyze_image
from modules.metadata_analyzer import analyze_metadata
from modules.fact_checker import check_claim
from modules.evidence_verifier import verify_claim, check_gemini_models

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Deepfake Detective",
    page_icon="🛡️",
    layout="wide"
)


# ==========================================================
# SESSION STATE
# ==========================================================

session_defaults = {
    "url_article_data": None,
    "manual_article_data": None,
    "combined_google_result": None,
    "combined_ai_result": None,
    "combined_claim": None,
    "image_result": None,
    "video_result": None,
    "audio_result": None
}

for key, value in session_defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================================
# APPLICATION HEADER
# ==========================================================

st.title("🛡️ Deepfake Detective")

st.subheader("AI Media Forensics & News Verification")

st.write(
    "Investigate suspicious images and verify online "
    "information using AI-assisted forensic tools."
)

st.divider()


# ==========================================================
# SIDEBAR NAVIGATION
# ==========================================================

page = st.sidebar.radio(
    "Choose a Module",
    [
        "Home",
        "AI Image Investigation",
        "Video Investigation",
        "Audio Investigation",
        "News & Social Media Verification",
        "Multimodal Dashboard"
    ],
    key="navigation"
)


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def safe_float(value, default=0.0):

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def display_classification_scores(results):
    if not isinstance(results, list) or not results:
        st.info("No important classification scores available.")
        return

    important_labels = [
    "AI_GEN",
    "REAL",
    "HIGGSFIELD",
    "AIVoice",
    "HumanVoice"
]

    for item in results:

        if not isinstance(item, dict):
            continue

        label = item.get("label", "Unknown")

        if label not in important_labels:
            continue

        score = safe_float(item.get("score"))

        st.write(
            f"**{label}: {score * 100:.2f}%**"
        )

        st.progress(
            max(0.0, min(1.0, score))
        )

def display_evidence_reference(number, sources):

    try:
        source_number = int(number)

    except (TypeError, ValueError):

        st.write(f"Source reference: {number}")
        return

    if 1 <= source_number <= len(sources):

        source = sources[source_number - 1]

        title = source.get("title", "Untitled")
        url = source.get("url")

        st.markdown(
            f"**Source {source_number}: {title}**"
        )

        if url:
            st.markdown(
                f"[🔗 Visit Original Source]({url})"
            )

        content = source.get("content", "")

        if content:

            with st.expander("View source information"):
                st.write(str(content)[:3000])

    else:

        st.write(
            f"Source {source_number}: Details unavailable."
        )


def pdf_paragraph(text, style):

    return Paragraph(
        escape(str(text)).replace("\n", "<br/>"),
        style
    )


def make_pdf_table(data, widths):

    table = Table(
        data,
        colWidths=widths,
        repeatRows=1
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#17365D")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            )
        ])
    )

    return table
def clear_previous_news_results():

    st.session_state["url_article_data"] = None
    st.session_state["manual_article_data"] = None

    st.session_state["combined_google_result"] = None
    st.session_state["combined_ai_result"] = None
    st.session_state["combined_claim"] = None

# ==========================================================
# HOME PAGE
# ==========================================================

if page == "Home":

    st.header("Welcome to Deepfake Detective 🛡️")

    st.write(
        """
        Deepfake Detective is a multimodal AI-assisted media
        forensics and news verification platform.

        It combines pretrained AI models, media metadata
        analysis and evidence-based verification techniques
        to help users investigate suspicious digital content.
        """
    )

    st.divider()

    st.subheader("🔍 Investigation Modules")

    col1, col2 = st.columns(2)

    with col1:

        st.info(
            """
            ### 🖼️ AI Image Investigation

            Upload images to examine their metadata and
            screen for patterns associated with AI-generated images.
            """
        )

    with col2:

        st.info(
    """
    ### 🎬 Video Investigation

    Uses the pretrained CakeLens V5 model to screen
    selected video frames for AI-generated content.
    """
)

    col3, col4 = st.columns(2)

    with col3:

        st.info(
            """
            ### 🎧 Audio Investigation

            Screen speech recordings using a pretrained
            audio classification model.
            """
        )

    with col4:

        st.info(
            """
            ### 📰 News Verification

            Investigate articles and factual claims using
            published fact-checks, external evidence and Gemini.
            """
        )

    st.divider()

    st.subheader("⚙️ Technology Behind the Platform")

    st.info(
        """
        **Media Analysis:** Python, Streamlit, PIL,
        OpenCV and pretrained AI models.

        **Fact Verification:** Google Fact Check API.

        **Evidence Assessment:** Tavily Search and Gemini AI.
        """
    )

    st.success(
        "One platform. Four investigation modules. "
        "A unified approach to digital media verification."
    )

    st.caption(
        "AI predictions are preliminary assessments, "
        "not definitive proof of authenticity."
    )


# ==========================================================
# IMAGE INVESTIGATION
# ==========================================================

elif page == "AI Image Investigation":

    st.header("🔍 AI Image Investigation")

    st.write(
        "Upload an image to investigate its metadata "
        "and analyze it using a pretrained AI model."
    )

    uploaded_file = st.file_uploader(
        "Upload an image",
        type=["jpg", "jpeg", "png"],
        key="image_upload"
    )

    if uploaded_file is not None:

        try:

            image = Image.open(uploaded_file)

            st.image(
                image,
                caption="Uploaded Image",
                use_container_width=True
            )

            st.success("Image uploaded successfully!")

            st.divider()

            st.subheader("📋 Image Metadata Investigation")

            metadata = analyze_metadata(
                image,
                uploaded_file.name
            )

            if not isinstance(metadata, dict):

                st.error("Invalid metadata response.")

            elif "error" in metadata:

                st.error(metadata["error"])

            else:

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "Image Width",
                        f"{metadata.get('Width', 'Unavailable')} px"
                    )

                    st.metric(
                        "Image Height",
                        f"{metadata.get('Height', 'Unavailable')} px"
                    )

                    st.metric(
                        "Image Format",
                        str(metadata.get("Format", "Unavailable"))
                    )

                with col2:

                    st.metric(
                        "Colour Mode",
                        metadata.get("Color Mode", "Unavailable")
                    )

                    st.metric(
                        "Processed Image Size",
                        metadata.get(
                            "Processed Image Size",
                            "Unavailable"
                        )
                    )

                with st.expander("View EXIF Metadata"):

                    exif = metadata.get("EXIF Data", {})

                    if exif:
                        st.json(exif)

                    else:
                        st.info("No EXIF metadata found.")

            st.divider()

            st.subheader("🤖 AI Image Detection")

            if st.button(
                "Analyze Image",
                key="analyze_image_button"
            ):

                with st.spinner("Analyzing image using AI..."):

                    result = analyze_image(image)

                if not isinstance(result, dict):

                    st.error("Unexpected AI detector response.")

                elif "error" in result:

                    st.error(result["error"])

                elif not all(
                    key in result
                    for key in [
                        "label",
                        "confidence",
                        "all_results"
                    ]
                ):

                    st.error("Incomplete AI detection response.")

                else:

                    st.session_state["image_result"] = result

                    st.success("Image analysis completed!")

                    col1, col2 = st.columns(2)

                    with col1:

                        st.metric(
                            "Model Prediction",
                            result["label"]
                        )

                    with col2:

                        st.metric(
                            "Model Confidence",
                            f"{result['confidence']:.2f}%"
                        )

                    st.divider()
                    st.subheader("Classification Scores")

                    display_classification_scores(
                        result["all_results"]
                    )

                    st.warning(
                        "AI predictions are not proof of authenticity. "
                        "Model confidence is not equivalent to real-world "
                        "accuracy. Compression and image quality can "
                        "affect predictions."
                    )

        except Exception as error:

            st.error(
                f"Image investigation error: {error}"
            )


# ==========================================================
# NEWS AND SOCIAL MEDIA VERIFICATION
# ==========================================================

elif page == "News & Social Media Verification":

    st.header("📰 News & Social Media Verification")

    st.write(
        "Investigate news articles and factual claims "
        "using Google Fact Check and AI evidence assessment."
    )

    st.divider()

    # ARTICLE INPUT

    st.subheader("Step 1: Provide Article Content")

    input_method = st.radio(
    "Choose article input method:",
    [
        "Enter Article URL",
        "Paste Article Text"
    ],
    horizontal=True,
    key="article_input_method",
    on_change=clear_previous_news_results
)

    # URL INPUT

    if input_method == "Enter Article URL":

        with st.form("url_article_form"):

            url = st.text_input(
                "News Article URL",
                key="url_input_field"
            )

            permission = st.checkbox(
                "I authorize retrieval of this publicly accessible webpage.",
                key="url_permission"
            )

            url_submit = st.form_submit_button(
                "Extract Article from URL"
            )

        if url_submit:

            if not url.strip():

                st.warning("Please enter a URL.")

            elif not permission:

                st.warning(
                    "Please authorize article retrieval."
                )

            else:

                with st.spinner("Extracting article..."):

                    article_result = extract_article(
                        url.strip()
                    )

                if not isinstance(article_result, dict):

                    st.error("Unexpected article extraction response.")

                elif "error" in article_result:

                    st.error(article_result["error"])

                elif not article_result.get("text", "").strip():

                    st.error("No article text was extracted.")

                else:

                    st.session_state["url_article_data"] = article_result

                    st.session_state["manual_article_data"] = None

                    st.session_state["combined_google_result"] = None
                    st.session_state["combined_ai_result"] = None
                    st.session_state["combined_claim"] = None

                    st.success("Article extracted successfully!")

    # MANUAL INPUT

    else:

        with st.form("manual_article_form"):

            manual_title = st.text_input(
                "Article Title",
                key="manual_title_field"
            )

            manual_url = st.text_input(
                "Original Article URL (Optional)",
                key="manual_url_field"
            )

            manual_text = st.text_area(
                "Paste Complete Article Text",
                height=300,
                key="manual_text_field"
            )

            manual_submit = st.form_submit_button(
                "Add Article"
            )

        if manual_submit:

            if not manual_text.strip():

                st.warning("Please paste the article text.")

            else:

                st.session_state["manual_article_data"] = {

                    "title": (
                        manual_title.strip()
                        or "Manually Provided Article"
                    ),

                    "text": manual_text.strip(),

                    "url": (
                        manual_url.strip()
                        or "Manually Provided Text"
                    )
                }

                st.session_state["url_article_data"] = None

                st.session_state["combined_google_result"] = None
                st.session_state["combined_ai_result"] = None
                st.session_state["combined_claim"] = None

                st.success("Article added successfully!")

    # SELECT ARTICLE

    if input_method == "Enter Article URL":

        article = st.session_state["url_article_data"]

    else:

        article = st.session_state["manual_article_data"]

    # ARTICLE DISPLAY

    if article:

        st.divider()

        st.subheader("Step 2: Article Content")

        st.write(
            "**Article Title:**",
            article.get("title", "Unavailable")
        )

        st.write(
            "**Source:**",
            article.get("url", "Unavailable")
        )

        with st.expander("Read Article Content"):

            st.write(article.get("text", ""))

        # CLAIM INPUT

        st.divider()

        st.subheader("Step 3: Factual Claim Verification")

        with st.form("combined_verification_form"):

            combined_claim = st.text_area(
                "Enter the factual claim:",
                placeholder=(
                    "Enter one specific factual statement "
                    "from the article."
                ),
                height=100,
                key="combined_claim_input"
            )

            combined_submit = st.form_submit_button(
                "🔍 Verify Claim Using Both Systems",
                use_container_width=True
            )

        if combined_submit:

            if not combined_claim.strip():

                st.warning("Please enter a factual claim.")

            else:

                claim = combined_claim.strip()

                st.session_state["combined_google_result"] = None
                st.session_state["combined_ai_result"] = None
                st.session_state["combined_claim"] = claim

                # GOOGLE FACT CHECK

                with st.spinner(
                    "Step 1/2: Searching Google Fact Check..."
                ):

                    try:

                        google_result = check_claim(claim)

                    except Exception as error:

                        google_result = {
                            "error": str(error)
                        }

                st.session_state["combined_google_result"] = (
                    google_result
                )

                # GEMINI EVIDENCE ASSESSMENT

                with st.spinner(
                    "Step 2/2: Comparing article with external evidence..."
                ):

                    try:

                        # IMPORTANT:
                        # Article context is now passed to Gemini.

                        ai_result = verify_claim(
                            claim,
                            article_context=article
                        )

                    except Exception as error:

                        ai_result = {
                            "success": False,
                            "error": str(error)
                        }

                st.session_state["combined_ai_result"] = ai_result

                st.success("Verification processes completed.")

        # DISPLAY SAVED RESULTS

        google_result = st.session_state[
            "combined_google_result"
        ]

        ai_result = st.session_state[
            "combined_ai_result"
        ]

        saved_claim = st.session_state[
            "combined_claim"
        ]

        if google_result is not None and ai_result is not None:

            st.divider()

            st.header("📊 Verification Results")

            st.info(
                f"**Claim under investigation:** {saved_claim}"
            )

            if not isinstance(google_result, dict):

                google_result = {
                    "error": "Invalid Google Fact Check response."
                }

            if not isinstance(ai_result, dict):

                ai_result = {
                    "error": "Invalid Gemini response."
                }

            col1, col2 = st.columns(2)

            # GOOGLE RESULTS

            with col1:

                st.subheader("🔎 Google Fact Check")

                if "error" in google_result:

                    st.error(google_result["error"])

                else:

                    st.info(
                        google_result.get(
                            "verdict",
                            "No Matching Fact-Check Found"
                        )
                    )

                    st.write(
                        google_result.get(
                            "message",
                            "No additional information available."
                        )
                    )

                    reviews = google_result.get("results", [])

                    if reviews:

                        st.markdown(
                            "#### Published Fact-Check Reviews"
                        )

                        for review in reviews:

                            with st.expander(
                                review.get(
                                    "publisher",
                                    "Fact-check review"
                                )
                            ):

                                st.write(
                                    "**Claim:**",
                                    review.get("claim", "Unavailable")
                                )

                                st.write(
                                    "**Publisher:**",
                                    review.get("publisher", "Unknown")
                                )

                                st.write(
                                    "**Original Rating:**",
                                    review.get("rating", "Unavailable")
                                )

                                st.write(
                                    "**Review Title:**",
                                    review.get("title", "Unavailable")
                                )

                                if review.get("url"):

                                    st.markdown(
                                        f"[Read Original Fact Check]"
                                        f"({review['url']})"
                                    )

                                st.write(
                                    "**Review Date:**",
                                    review.get(
                                        "review_date",
                                        "Unavailable"
                                    )
                                )

                    else:

                        st.info(
                            "No matching published fact-check reviews found."
                        )

            # GEMINI RESULTS

            with col2:

                st.subheader("🤖 AI Evidence Assessment")

                if "error" in ai_result:

                    st.error(ai_result["error"])

                else:

                    st.info(
                        f"**AI Verdict:** "
                        f"{ai_result.get('verdict', 'Unverified')}"
                    )

                    confidence = safe_float(
                        ai_result.get("confidence")
                    )

                    st.metric(
                        "AI Assessment Confidence",
                        f"{confidence:.2f}%"
                    )

                    st.caption(
                        "This is the model's assessment confidence, "
                        "not a guaranteed probability of truth."
                    )

                    st.write("**Explanation:**")

                    st.write(
                        ai_result.get(
                            "explanation",
                            "No explanation available."
                        )
                    )

                    st.write("**Limitations:**")

                    st.write(
                        ai_result.get(
                            "limitations",
                            "No limitations information returned."
                        )
                    )

                    if ai_result.get("model_used"):

                        st.caption(
                            "Gemini model: "
                            + str(ai_result["model_used"])
                        )

            # DETAILED EVIDENCE

            if "error" not in ai_result:

                st.divider()

                st.header("📚 Detailed Evidence Analysis")

                sources = ai_result.get("sources", [])

                supporting = ai_result.get(
                    "supporting_sources",
                    []
                )

                contradicting = ai_result.get(
                    "contradicting_sources",
                    []
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.subheader("✅ Supporting Evidence")

                    if supporting:

                        for number in supporting:

                            display_evidence_reference(
                                number,
                                sources
                            )

                    else:

                        st.info(
                            "No supporting external sources identified."
                        )

                with col2:

                    st.subheader("⚠️ Contradicting Evidence")

                    if contradicting:

                        for number in contradicting:

                            display_evidence_reference(
                                number,
                                sources
                            )

                    else:

                        st.info(
                            "No contradicting external sources identified."
                        )

            # SUMMARY

            st.divider()

            st.header("📝 Verification Summary")

            if "error" not in ai_result:

                st.write(
                    "**Google Fact Check:**",
                    google_result.get(
                        "verdict",
                        "Unavailable"
                    ) if "error" not in google_result
                    else "Unavailable"
                )

                st.write(
                    "**AI Evidence Assessment:**",
                    ai_result.get("verdict", "Unverified")
                )

                st.warning(
                    "Google Fact Check retrieves previously published "
                    "reviews. Gemini provides an AI-assisted assessment. "
                    "Neither result guarantees truth. Examine original "
                    "sources before drawing conclusions."
                )

            else:

                st.warning(
                    "The AI evidence assessment could not be completed. "
                    "Check the error message and API configuration."
                )

    else:

        st.info(
            "Provide an article using the selected input method "
            "to begin verification."
        )

    # GEMINI DIAGNOSTICS

    st.divider()

    st.subheader("⚙️ Gemini API Diagnostics")

    if st.button(
        "Check Available Gemini Models",
        key="gemini_model_check"
    ):

        with st.spinner("Checking Gemini API..."):

            model_result = check_gemini_models()

        if isinstance(model_result, list) and model_result:

            st.success("Gemini models retrieved successfully.")

            st.write(model_result)

        elif isinstance(model_result, dict) and "error" in model_result:

            st.error(model_result["error"])

        else:

            st.error("No eligible Gemini models found.")


# ==========================================================
# VIDEO INVESTIGATION - CAKELENS V5
# ==========================================================

elif page == "Video Investigation":

    st.header("🎬 Video Investigation")

    st.write(
        "Upload a video for AI-assisted deepfake screening "
        "using the pretrained CakeLens V5 model."
    )

    video_file = st.file_uploader(
        "Upload Video",
        type=["mp4"],
        key="video_upload"
    )

    if video_file is not None:

        st.video(video_file)

        if st.button(
            "Analyze Video",
            key="analyze_video_button"
        ):

            with st.spinner(
                "Analyzing video using CakeLens V5. "
                "Please wait..."
            ):

                result = analyze_video(
                    video_file.getvalue()
                )

            if not isinstance(result, dict):

                st.error(
                    "Unexpected video detector response."
                )

            elif "error" in result:

                st.error(result["error"])

            else:

                st.session_state["video_result"] = result

                st.success(
                    "CakeLens V5 video analysis completed!"
                )

                st.divider()

                st.subheader("📊 Video Analysis Summary")

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Video Duration",
                        f"{result.get('duration', 0):.2f} seconds"
                    )

                with col2:

                    st.metric(
                        "Frames Analyzed",
                        result.get('frames_analyzed', 0)
                    )

                with col3:

                    st.metric(
                        "Original Video Frames",
                        result.get('original_frame_count', 0)
                    )

                st.divider()
                st.subheader("🤖 CakeLens V5 Detection Result")

                ai_score = safe_float(
                        result.get("ai_generation_score", 0)
)

                # FINAL DETECTION STATUS

                if ai_score >= 50:

                    st.error(
                        "🚨 STRONG AI-GENERATION SIGNAL DETECTED"
                    )

                elif ai_score >= 40:

                    st.warning(
                        "⚠️ POSSIBLE AI-GENERATION SIGNAL DETECTED"
                    )

                else:

                    st.success(
                        "✅ NO STRONG AI-GENERATION SIGNAL DETECTED"
                    )

                    st.info(
    "Video not identified as AI-generated by CakeLens V5."
)

                col1, col2 = st.columns(2)

                with col1:

                    st.write("**Model Prediction**")

                    st.write(
                    result.get(
            "label",
            "Detection result unavailable"
        )
    )

                with col2:

                    st.metric(
                        "AI Generation Score",
                        f"{ai_score:.2f}%"
                    )

                st.caption(
                    "The AI Generation Score represents the highest score "
                    "among the model's AI-generation-related categories. "
                    "It is not a calibrated probability of authenticity."
                )

                st.divider()

                # COMPLETE CLASSIFICATION RESULTS

                st.subheader("📈 Complete Classification Scores")

                display_classification_scores(
                    result.get("all_results", [])
                )
                
                st.divider()

                st.subheader("⚠️ Important Limitations")

                for warning in result.get("warnings", []):

                    st.warning(warning)

                st.caption(
                    f"Detection Model: {result.get('model', 'Unavailable')} "
                    f"| Analysis Mode: "
                    f"{result.get('analysis_mode', 'Unavailable')}"
                )


# ==========================================================
# AUDIO INVESTIGATION
# ==========================================================

elif page == "Audio Investigation":

    st.header("🎧 Audio Investigation")

    st.write(
        "Upload a speech recording for AI-assisted "
        "synthetic voice screening."
    )

    audio_file = st.file_uploader(
        "Upload Audio",
        type=["wav", "flac"],
        key="audio_upload"
    )

    if audio_file is not None:

        st.audio(audio_file)

        if st.button("Analyze Audio"):

            with st.spinner(
                "Analyzing audio using the pretrained model..."
            ):

                result = analyze_audio(audio_file)

            if not isinstance(result, dict):

                st.error("Unexpected audio detector response.")

            elif "error" in result:

                st.error(result["error"])

            else:

                st.session_state["audio_result"] = result

                st.success("Audio analysis completed!")

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "Model Prediction",
                        result.get("label", "Unavailable")
                    )

                with col2:

                    st.metric(
                        "Model Confidence",
                        f"{safe_float(result.get('confidence')):.2f}%"
                    )

                st.subheader("Classification Scores")

                display_classification_scores(
                    result.get("all_results", [])
                )

                st.warning(
                    "This is an experimental audio classification result. "
                    "It is not proof of authenticity or manipulation."
                )


# ==========================================================
# ==========================================================
# MULTIMODAL DASHBOARD
# ==========================================================

elif page == "Multimodal Dashboard":

    st.header("📊 Multimodal Investigation Dashboard")

    st.write(
        "Review and download your image, video, audio "
        "and news verification results."
    )

    # ======================================================
    # RETRIEVE SAVED RESULTS
    # ======================================================

    image_result = st.session_state.get("image_result")
    video_result = st.session_state.get("video_result")
    audio_result = st.session_state.get("audio_result")

    google_result = st.session_state.get(
        "combined_google_result"
    )

    ai_result = st.session_state.get(
        "combined_ai_result"
    )

    saved_claim = st.session_state.get(
        "combined_claim"
    )

    st.divider()

    # ======================================================
    # IMAGE RESULTS
    # ======================================================

    st.subheader("🖼️ Image Investigation")

    if isinstance(image_result, dict):

        if "error" in image_result:

            st.error(image_result["error"])

        else:

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Prediction",
                    image_result.get("label", "Unavailable")
                )

            with col2:

                st.metric(
                    "Confidence",
                    f"{safe_float(image_result.get('confidence')):.2f}%"
                )

            st.subheader("Image Classification Scores")

            display_classification_scores(
                image_result.get("all_results", [])
            )

    else:

        st.info("No image results available.")

    st.divider()

    # ======================================================
    # VIDEO RESULTS
    # ======================================================

    st.subheader("🎬 Video Investigation")

    if isinstance(video_result, dict):

        if "error" in video_result:

            st.error(video_result["error"])

        else:

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Video Duration",
                    f"{safe_float(video_result.get('duration')):.2f} sec"
                )

            with col2:

                st.metric(
                    "Frames Analysed",
                    video_result.get("frames_analyzed", 0)
                )

            with col3:

                st.metric(
                    "Original Video Frames",
                    video_result.get("original_frame_count", 0)
                )

            ai_score = safe_float(
                video_result.get("ai_generation_score")
            )

            st.divider()

            st.subheader("CakeLens V5 Detection Result")

            # UPDATED VIDEO CLASSIFICATION THRESHOLDS

            if ai_score >= 50:

                st.error(
                    "🚨 STRONG AI-GENERATION SIGNAL DETECTED"
                )

                result_status = "Strong AI-generation signal detected"

            elif ai_score >= 40:

                st.warning(
                    "⚠️ POSSIBLE AI-GENERATION SIGNAL DETECTED"
                )

                result_status = "Possible AI-generation signal detected"

            else:

                st.success(
                    "✅ NO STRONG AI-GENERATION SIGNAL DETECTED"
                )

                result_status = "No strong AI-generation signal detected"

            st.metric(
                "AI Generation Score",
                f"{ai_score:.2f}%"
            )

            st.progress(
                max(0.0, min(1.0, ai_score / 100))
            )

            st.write(
                "**Detection Status:**",
                result_status
            )

            st.write(
                "**Model Prediction:**",
                video_result.get("label", "Unavailable")
            )

            st.caption(
                "The model score is not a calibrated probability "
                "of authenticity."
            )

            st.subheader("Complete Classification Scores")

            display_classification_scores(
                video_result.get("all_results", [])
            )

            # VIDEO WARNINGS

            warnings = video_result.get("warnings", [])

            if warnings:

                st.subheader("Important Limitations")

                for warning in warnings:

                    st.warning(warning)

    else:

        st.info(
            "No video results available. "
            "Complete a video investigation to view results here."
        )

    st.divider()

    # ======================================================
    # AUDIO RESULTS
    # ======================================================

    st.subheader("🎧 Audio Investigation")

    if isinstance(audio_result, dict):

        if "error" in audio_result:

            st.error(audio_result["error"])

        else:

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Prediction",
                    audio_result.get("label", "Unavailable")
                )

            with col2:

                st.metric(
                    "Confidence",
                    f"{safe_float(audio_result.get('confidence')):.2f}%"
                )

            st.subheader("Audio Classification Scores")

            display_classification_scores(
                audio_result.get("all_results", [])
            )

            st.caption(
                audio_result.get(
                    "assessment_note",
                    "Experimental audio classification result."
                )
            )

    else:

        st.info("No audio results available.")

    st.divider()

    # ======================================================
    # NEWS RESULTS
    # ======================================================

    st.subheader("📰 News Verification")

    if saved_claim and isinstance(ai_result, dict):

        st.write("**Claim:**", saved_claim)

        if "error" in ai_result:

            st.error(ai_result["error"])

        else:

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "AI Verdict",
                    ai_result.get("verdict", "Unverified")
                )

            with col2:

                st.metric(
                    "AI Confidence",
                    f"{safe_float(ai_result.get('confidence')):.2f}%"
                )

            st.write(
                ai_result.get(
                    "explanation",
                    "No explanation available."
                )
            )

        if isinstance(google_result, dict):

            if "error" in google_result:

                st.error(google_result["error"])

            else:

                st.write(
                    "**Google Fact Check:**",
                    google_result.get("verdict", "Unavailable")
                )

    else:

        st.info("No news verification results available.")

    # ======================================================
    # PDF REPORT
    # ======================================================

    st.divider()

    st.header("📄 Download Investigation Report")

    def generate_pdf_report():

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        story = []

        story.append(
            Paragraph(
                "DEEPFAKE DETECTIVE",
                styles["Title"]
            )
        )

        story.append(
            Paragraph(
                "Multimodal Media Investigation Report",
                styles["Heading2"]
            )
        )

        story.append(Spacer(1, 20))

        # --------------------------------------------------
        # IMAGE PDF
        # --------------------------------------------------

        story.append(
            Paragraph(
                "1. Image Investigation",
                styles["Heading2"]
            )
        )

        if isinstance(image_result, dict) and "error" not in image_result:

            data = [
                ["Parameter", "Result"],

                [
                    "Prediction",
                    escape(str(image_result.get("label", "Unavailable")))
                ],

                [
                    "Confidence",
                    f"{safe_float(image_result.get('confidence')):.2f}%"
                ]
            ]

            for item in image_result.get("all_results", []):

                data.append([
                    escape(str(item.get("label", "Unknown"))),
                    f"{safe_float(item.get('score', 0)) * 100:.2f}%"
                ])

            story.append(
                make_pdf_table(data, [230, 230])
            )

        else:

            story.append(
                pdf_paragraph(
                    "No image investigation results available.",
                    styles["Normal"]
                )
            )

        story.append(Spacer(1, 20))

        # --------------------------------------------------
        # VIDEO PDF
        # --------------------------------------------------

        story.append(
            Paragraph(
                "2. Video Investigation",
                styles["Heading2"]
            )
        )

        if isinstance(video_result, dict) and "error" not in video_result:

            video_score = safe_float(
                video_result.get("ai_generation_score")
            )

            if video_score >= 50:

                video_status = "Strong AI-generation signal detected"

            elif video_score >= 40:

                video_status = "Possible AI-generation signal detected"

            else:

                video_status = "No strong AI-generation signal detected"

            data = [
                ["Parameter", "Result"],

                ["Detection Model", "CakeLens V5"],

                [
                    "Video Duration",
                    f"{safe_float(video_result.get('duration')):.2f} seconds"
                ],

                [
                    "Original Video Frames",
                    str(video_result.get("original_frame_count", 0))
                ],

                [
                    "Frames Analysed",
                    str(video_result.get("frames_analyzed", 0))
                ],

                [
                    "Detection Status",
                    video_status
                ],

                [
                    "Model Prediction",
                    pdf_paragraph(
                        video_result.get("label", "Unavailable"),
                        styles["Normal"]
                    )
                ],

                [
                    "AI Generation Score",
                    f"{video_score:.2f}%"
                ]
            ]

            for item in video_result.get("all_results", []):

                data.append([
                    escape(str(item.get("label", "Unknown"))),
                    f"{safe_float(item.get('score')) * 100:.2f}%"
                ])

            story.append(
                make_pdf_table(data, [180, 280])
            )

            story.append(Spacer(1, 10))

            story.append(
                Paragraph(
                    "Video Analysis Limitations",
                    styles["Heading3"]
                )
            )

            for warning in video_result.get("warnings", []):

                story.append(
                    pdf_paragraph(
                        "• " + str(warning),
                        styles["Normal"]
                    )
                )

        else:

            story.append(
                pdf_paragraph(
                    "No video investigation results available.",
                    styles["Normal"]
                )
            )

        story.append(Spacer(1, 20))


        # --------------------------------------------------
        # AUDIO PDF
        # --------------------------------------------------

        story.append(
            Paragraph(
                "3. Audio Investigation",
                styles["Heading2"]
            )
        )

        if isinstance(audio_result, dict) and "error" not in audio_result:

            data = [
                ["Parameter", "Result"],

                [
                    "Prediction",
                    escape(str(audio_result.get("label", "Unavailable")))
                ],

                [
                    "Confidence",
                    f"{safe_float(audio_result.get('confidence', 0)):.2f}%"
                ]
            ]

            for item in audio_result.get("all_results", []):

                data.append([
                    escape(str(item.get("label", "Unknown"))),
                    f"{safe_float(item.get('score', 0)) * 100:.2f}%"
                ])

            story.append(
                make_pdf_table(data, [230, 230])
            )

        else:

            story.append(
                pdf_paragraph(
                    "No audio investigation results available.",
                    styles["Normal"]
                )
            )

        story.append(Spacer(1, 20))
        # --------------------------------------------------
        # NEWS PDF
        # --------------------------------------------------

        story.append(
            Paragraph(
                "4. News Verification",
                styles["Heading2"]
            )
        )

        if saved_claim:

            news_data = [
                ["Parameter", "Result"],

                [
                    "Claim",
                    pdf_paragraph(saved_claim, styles["Normal"])
                ]
            ]

            if isinstance(google_result, dict):

                news_data.append([
                    "Google Fact Check",
                    pdf_paragraph(
                        google_result.get("verdict", "Unavailable"),
                        styles["Normal"]
                    )
                ])

            if isinstance(ai_result, dict):

                news_data.append([
                    "AI Verdict",
                    pdf_paragraph(
                        ai_result.get("verdict", "Unavailable"),
                        styles["Normal"]
                    )
                ])

                news_data.append([
                    "AI Confidence",
                    f"{safe_float(ai_result.get('confidence')):.2f}%"
                ])

                news_data.append([
                    "Explanation",
                    pdf_paragraph(
                        ai_result.get("explanation", "Unavailable"),
                        styles["Normal"]
                    )
                ])

                news_data.append([
                    "Limitations",
                    pdf_paragraph(
                        ai_result.get("limitations", "Unavailable"),
                        styles["Normal"]
                    )
                ])

            story.append(
                make_pdf_table(news_data, [130, 330])
            )

        else:

            story.append(
                pdf_paragraph(
                    "No news verification results available.",
                    styles["Normal"]
                )
            )

        story.append(Spacer(1, 25))

        # --------------------------------------------------
        # DISCLAIMER
        # --------------------------------------------------

        story.append(
            Paragraph(
                "Important Disclaimer",
                styles["Heading2"]
            )
        )

        story.append(
            pdf_paragraph(
                "This report contains AI-assisted investigation results. "
                "Model predictions and confidence scores are not "
                "conclusive proof of authenticity or manipulation. "
                "Video results are based on selected-frame analysis. "
                "Audio results depend on the capabilities of the "
                "pretrained model. News assessments depend on the "
                "availability and reliability of external evidence. "
                "All findings should be interpreted with caution.",
                styles["Normal"]
            )
        )

        document.build(story)

        buffer.seek(0)

        return buffer.getvalue()

    # ======================================================
    # PDF GENERATION BUTTON
    # ======================================================

    if st.button(
        "Generate PDF Investigation Report",
        use_container_width=True
    ):

        try:

            with st.spinner("Generating PDF report..."):

                pdf_data = generate_pdf_report()

            st.success("PDF report generated successfully!")

            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_data,
                file_name="Deepfake_Detective_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        except Exception as error:

            st.error(
                f"PDF generation failed: {error}"
            )

    st.divider()

    st.caption(
        "Deepfake Detective | AI-Assisted Multimodal Media Forensics"
    )