import json
import re
import requests
import streamlit as st


# ==========================================================
# API CONFIGURATION
# ==========================================================

TAVILY_URL = "https://api.tavily.com/search"

GEMINI_MODELS_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
)

# EXISTING GEMINI MODEL PREFERENCES PRESERVED

GEMINI_PREFERRED_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]

REQUEST_TIMEOUT = 30


# ==========================================================
# TAVILY EVIDENCE SEARCH
# ==========================================================

def search_evidence(claim):

    api_key = st.secrets.get("TAVILY_API_KEY", "")

    if not api_key:
        return {
            "success": False,
            "error": "Tavily API key is missing.",
            "results": []
        }

    try:

        payload = {
            "api_key": api_key,
            "query": claim,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": False
        }

        response = requests.post(
            TAVILY_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code != 200:
            return {
                "success": False,
                "error": (
                    f"Tavily API error: HTTP "
                    f"{response.status_code}"
                ),
                "results": []
            }

        data = response.json()

        if not isinstance(data, dict):
            return {
                "success": False,
                "error": "Tavily returned an invalid response.",
                "results": []
            }

        results = []

        for item in data.get("results", []):

            if not isinstance(item, dict):
                continue

            title = item.get("title", "Untitled")
            url = item.get("url", "")
            content = item.get("content", "")

            if not content:
                continue

            try:
                score = float(item.get("score", 0))
            except (ValueError, TypeError):
                score = 0.0

            results.append({
                "title": str(title),
                "url": str(url),
                "content": str(content),
                "score": score
            })

        return {
            "success": True,
            "results": results,
            "error": None
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Tavily request timed out.",
            "results": []
        }

    except requests.exceptions.RequestException:
        return {
            "success": False,
            "error": "Unable to connect to Tavily.",
            "results": []
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error),
            "results": []
        }


# ==========================================================
# GET AVAILABLE GEMINI TEXT MODELS
# ==========================================================

def check_gemini_models():

    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        return []

    try:

        response = requests.get(
            GEMINI_MODELS_URL,
            params={"key": api_key},
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code != 200:
            return []

        data = response.json()

        available_models = []

        excluded_terms = [
            "tts",
            "audio",
            "native-audio",
            "embedding",
            "image",
            "robotics",
            "computer-use"
        ]

        for model in data.get("models", []):

            model_name = model.get("name", "")

            methods = model.get(
                "supportedGenerationMethods",
                []
            )

            short_name = model_name.replace(
                "models/",
                ""
            )

            lower_name = short_name.lower()

            if "generateContent" not in methods:
                continue

            if any(
                term in lower_name
                for term in excluded_terms
            ):
                continue

            if "gemini" not in lower_name:
                continue

            available_models.append(short_name)

        return available_models

    except Exception:
        return []


# ==========================================================
# SELECT GEMINI MODEL
# ==========================================================

def select_gemini_model(available_models):

    if not available_models:
        return None

    for preferred in GEMINI_PREFERRED_MODELS:

        if preferred in available_models:
            return preferred

    for model in available_models:

        if "flash" in model.lower():
            return model

    return available_models[0]


# ==========================================================
# CLEAN GEMINI JSON RESPONSE
# ==========================================================

def clean_json_response(text):

    if not text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "No valid JSON object found."
        )

    return json.loads(
        text[start:end + 1]
    )


# ==========================================================
# NORMALIZE SOURCE NUMBERS
# ==========================================================

def normalize_source_numbers(source_list, source_count):

    valid_numbers = []

    if not isinstance(source_list, list):
        return valid_numbers

    for item in source_list:

        try:

            if isinstance(item, bool):
                continue

            if isinstance(item, int):
                number = item

            else:

                match = re.fullmatch(
                    r"\s*\d+\s*",
                    str(item)
                )

                if not match:
                    continue

                number = int(item)

            if 1 <= number <= source_count:

                if number not in valid_numbers:
                    valid_numbers.append(number)

        except (ValueError, TypeError):
            continue

    return valid_numbers


# ==========================================================
# VALIDATE GEMINI ASSESSMENT
# ==========================================================

def validate_assessment(result, source_count):

    if not isinstance(result, dict):
        raise ValueError(
            "Gemini returned an invalid assessment."
        )

    verdict = str(
        result.get("verdict", "Unverified")
    ).strip().lower()

    allowed_verdicts = {
        "supported": "Supported",
        "contradicted": "Contradicted",
        "unverified": "Unverified"
    }

    verdict = allowed_verdicts.get(
        verdict,
        "Unverified"
    )

    confidence = result.get("confidence", 0)

    try:
        confidence = float(confidence)
    except (ValueError, TypeError):
        confidence = 0

    if not 0 <= confidence <= 100:
        confidence = 0

    supporting = normalize_source_numbers(
        result.get("supporting_sources", []),
        source_count
    )

    contradicting = normalize_source_numbers(
        result.get("contradicting_sources", []),
        source_count
    )

    explanation = str(
        result.get(
            "explanation",
            "No explanation provided."
        )
    )

    limitations = str(
        result.get(
            "limitations",
            "The assessment is limited by the available evidence."
        )
    )

    if supporting and contradicting:

        verdict = "Unverified"
        confidence = min(confidence, 50)

        limitations += (
            " Supporting and contradicting sources were both "
            "identified. Their disagreement requires further review."
        )

    elif verdict == "Supported" and not supporting:

        verdict = "Unverified"
        confidence = min(confidence, 30)

        explanation = (
            "The assessment did not identify valid supporting "
            "external sources. The claim cannot be classified "
            "as supported."
        )

    elif verdict == "Contradicted" and not contradicting:

        verdict = "Unverified"
        confidence = min(confidence, 30)

        explanation = (
            "The assessment did not identify valid contradicting "
            "external sources. The claim cannot be classified "
            "as contradicted."
        )

    return {
        "verdict": verdict,
        "confidence": confidence,
        "explanation": explanation,
        "supporting_sources": supporting,
        "contradicting_sources": contradicting,
        "limitations": limitations
    }


# ==========================================================
# PREPARE SUBMITTED ARTICLE
# ==========================================================

def prepare_article_context(article_context):

    if not isinstance(article_context, dict):
        return None

    title = str(
        article_context.get(
            "title",
            "Title unavailable"
        )
    )

    url = str(
        article_context.get(
            "url",
            "URL unavailable"
        )
    )

    content = str(
        article_context.get(
            "text",
            ""
        )
    )

    if not content.strip():
        return None

    return {
        "title": title[:1000],
        "url": url[:2000],
        "text": content[:12000]
    }


# ==========================================================
# PREPARE EXTERNAL EVIDENCE
# ==========================================================

def prepare_evidence_text(evidence):

    evidence_text = ""

    for index, item in enumerate(evidence, start=1):

        evidence_text += (
            f"\nSOURCE {index}\n"
            f"Title: {item.get('title', '')}\n"
            f"URL: {item.get('url', '')}\n"
            f"Search relevance score: {item.get('score', 0)}\n"
            f"Content: {str(item.get('content', ''))[:5000]}\n"
        )

    return evidence_text


# ==========================================================
# GEMINI EVIDENCE ANALYSIS
# ==========================================================

def analyze_evidence(
    claim,
    evidence,
    article_context=None
):

    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        return {
            "success": False,
            "error": "Gemini API key is missing."
        }

    if not evidence:
        return {
            "success": False,
            "error": "No external evidence was found to analyze."
        }

    available_models = check_gemini_models()

    if not available_models:
        return {
            "success": False,
            "error": (
                "No eligible Gemini text-generation models "
                "were found. Check your API key and model access."
            )
        }

    selected_model = select_gemini_model(
        available_models
    )

    models_to_try = [selected_model]

    for model in available_models:

        if model not in models_to_try:
            models_to_try.append(model)

    evidence_text = prepare_evidence_text(evidence)

    article_text = ""

    prepared_article = prepare_article_context(
        article_context
    )

    if prepared_article:

        article_text = f"""
SUBMITTED ARTICLE UNDER INVESTIGATION

Article Title:
{prepared_article["title"]}

Article URL:
{prepared_article["url"]}

Article Content:
{prepared_article["text"]}

IMPORTANT:
This submitted article is the material being investigated.
It must NOT be treated as independent confirmation
of its own factual claims.

Use external evidence to examine whether its
statements are supported, contradicted or unverified.
"""

    else:

        article_text = """
NO ARTICLE CONTENT WAS PROVIDED.

Analyze the factual claim using the available
external evidence only.
"""

    # ======================================================
    # GEMINI PROMPT
    # ======================================================

    prompt = f"""
You are a careful, neutral and evidence-based
news and factual claim verification assistant.

Your task is to investigate the exact factual claim
using the submitted article and external evidence.

CLAIM UNDER INVESTIGATION:

{claim}

{article_text}

EXTERNAL EVIDENCE RETRIEVED THROUGH TAVILY:

{evidence_text}

IMPORTANT VERIFICATION RULES:

1. Examine the exact wording of the claim.
2. Read the submitted article and understand its context.
3. Compare the article's statements with external evidence.
4. Do not treat the submitted article as independent confirmation.
5. Examine actual source content, not just headlines or titles.
6. Check whether sources discuss the same people, events and circumstances.
7. Pay attention to publication dates and changing facts.
8. A source that merely repeats the submitted article is not independent confirmation.
9. Give appropriate consideration to primary sources and credible independent reporting.
10. A search relevance score is not proof of accuracy.
11. Do not assume that a claim is false merely because supporting evidence is missing.
12. Do not invent facts, quotations, sources or URLs.
13. If evidence is insufficient, unrelated or inconclusive, use Unverified.
14. If sources genuinely disagree, explain the disagreement and use Unverified when necessary.
15. Distinguish between the article's reporting and the truth of the underlying claim.

VERDICT RULES:

SUPPORTED:
Use only when relevant external evidence directly
and sufficiently supports the exact claim.

CONTRADICTED:
Use only when reliable external evidence directly
establishes that the exact claim is false or
materially conflicts with it.

UNVERIFIED:
Use when evidence is insufficient, unrelated,
incomplete, outdated or inconclusive.

SOURCE NUMBER RULES:

- Source numbers refer ONLY to external Tavily results.
- The submitted article is NOT a numbered source.
- Use only source numbers supplied above.
- Supporting sources must directly support the claim.
- Contradicting sources must directly contradict the claim.
- Do not invent source numbers.
- If no source supports the claim, return [].
- If no source contradicts the claim, return [].

CONFIDENCE:

Return a number between 0 and 100.
Confidence must reflect the quality and relevance
of available evidence.
Do not present confidence as a guaranteed probability
that the claim is true.

RETURN ONLY A VALID JSON OBJECT.
Do not include Markdown fences or additional commentary.

{{
    "verdict": "Supported, Contradicted, or Unverified",
    "confidence": 0,
    "explanation": "Evidence-based explanation",
    "supporting_sources": [],
    "contradicting_sources": [],
    "limitations": "Limitations of available evidence"
}}

The verdict must be exactly one of:
Supported
Contradicted
Unverified
"""

    last_error = None

    # ======================================================
    # TRY AVAILABLE GEMINI MODELS
    # ======================================================

    for model in models_to_try:

        api_url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/{model}:generateContent"
        )

        # JSON MODE REMOVED:
        # The selected model does not support JSON mode.
        # The prompt requests JSON and clean_json_response()
        # processes the generated text.

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1
            }
        }

        try:

            response = requests.post(
                api_url,
                params={"key": api_key},
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code != 200:

                error_text = response.text

                last_error = (
                    f"Gemini HTTP {response.status_code}: "
                    f"{error_text[:1000]}"
                )

                # Retry another model for temporary or
                # model-specific errors.

                if response.status_code in [
                    404,
                    429,
                    500,
                    502,
                    503,
                    504
                ]:

                    continue

                return {
                    "success": False,
                    "error": last_error
                }

            data = response.json()

            candidates = data.get(
                "candidates",
                []
            )

            if not candidates:

                last_error = (
                    "Gemini returned no analysis candidates."
                )

                continue

            parts = candidates[0].get(
                "content",
                {}
            ).get(
                "parts",
                []
            )

            generated_text = ""

            for part in parts:

                if "text" in part:
                    generated_text += part["text"]

            if not generated_text:

                last_error = (
                    "Gemini returned no text response."
                )

                continue

            result = clean_json_response(
                generated_text
            )

            validated = validate_assessment(
                result,
                len(evidence)
            )

            return {
                "success": True,
                "verdict": validated["verdict"],
                "confidence": validated["confidence"],
                "explanation": validated["explanation"],
                "supporting_sources": (
                    validated["supporting_sources"]
                ),
                "contradicting_sources": (
                    validated["contradicting_sources"]
                ),
                "limitations": validated["limitations"],
                "model_used": model
            }

        except requests.exceptions.Timeout:

            last_error = (
                f"Request timed out while using {model}."
            )

            continue

        except json.JSONDecodeError:

            last_error = (
                f"Gemini returned invalid JSON using {model}."
            )

            continue

        except requests.exceptions.RequestException as error:

            last_error = (
                f"Network error while using {model}: {str(error)}"
            )

            continue

        except Exception as error:

            last_error = str(error)

            continue

    return {
        "success": False,
        "error": (
            "All eligible Gemini models failed. "
            + str(last_error)
        )
    }


# ==========================================================
# COMPLETE CLAIM VERIFICATION
# ==========================================================

def verify_claim(
    claim,
    article_context=None
):

    if not isinstance(claim, str) or not claim.strip():

        return {
            "success": False,
            "error": "Please provide a claim to verify."
        }

    claim = claim.strip()

    # STEP 1: SEARCH EXTERNAL EVIDENCE

    evidence_result = search_evidence(claim)

    if not evidence_result["success"]:

        return {
            "success": False,
            "error": evidence_result["error"]
        }

    evidence = evidence_result["results"]

    # STEP 2: HANDLE NO EXTERNAL EVIDENCE

    if not evidence:

        return {
            "success": True,
            "verdict": "Unverified",
            "confidence": 0,
            "explanation": (
                "No relevant external evidence was retrieved. "
                "The submitted article alone cannot independently "
                "establish the truth of the claim."
            ),
            "supporting_sources": [],
            "contradicting_sources": [],
            "limitations": (
                "No external evidence was available for comparison."
            ),
            "sources": [],
            "model_used": None
        }

    # STEP 3: ANALYZE ARTICLE AND EXTERNAL EVIDENCE

    analysis = analyze_evidence(
        claim,
        evidence,
        article_context=article_context
    )

    if not analysis["success"]:

        return {
            "success": False,
            "error": analysis["error"],
            "sources": evidence
        }

    # STEP 4: RETURN COMPLETE RESULTS

    return {
        "success": True,
        "verdict": analysis["verdict"],
        "confidence": analysis["confidence"],
        "explanation": analysis["explanation"],
        "supporting_sources": (
            analysis["supporting_sources"]
        ),
        "contradicting_sources": (
            analysis["contradicting_sources"]
        ),
        "limitations": analysis["limitations"],
        "sources": evidence,
        "model_used": analysis["model_used"]
    }