import requests
import streamlit as st


# ==========================================
# GOOGLE FACT CHECK API CONFIGURATION
# ==========================================

API_URL = (
    "https://factchecktools.googleapis.com/"
    "v1alpha1/claims:search"
)

REQUEST_TIMEOUT = 20


# ==========================================
# SEARCH GOOGLE FACT CHECK DATABASE
# ==========================================

def check_claim(claim):

    try:

        # VALIDATE CLAIM

        if not isinstance(claim, str) or not claim.strip():

            return {
                "error": "Please enter a factual claim."
            }

        claim = claim.strip()

        # GET API KEY FROM STREAMLIT SECRETS

        api_key = st.secrets.get(
            "GOOGLE_FACT_CHECK_API_KEY"
        )

        if not api_key:

            return {
                "error": "Google Fact Check API key is missing."
            }

        # PREPARE API PARAMETERS

        params = {
            "query": claim,
            "key": api_key,
            "languageCode": "en",
            "pageSize": 10
        }

        # SEND REQUEST TO GOOGLE API

        response = requests.get(
            API_URL,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        # HANDLE API ERRORS

        if response.status_code != 200:

            try:

                error_data = response.json()

                error_message = error_data.get(
                    "error", {}
                ).get(
                    "message",
                    "Unknown API error"
                )

            except (ValueError, AttributeError):

                error_message = "Invalid API response."

            return {
                "error": (
                    f"Google Fact Check API error: "
                    f"{error_message}"
                )
            }

        # READ JSON RESPONSE

        data = response.json()

        if not isinstance(data, dict):

            return {
                "error": "Google returned an unexpected response."
            }

        claims = data.get("claims", [])

        if not isinstance(claims, list):
            claims = []

        # HANDLE NO MATCHING CLAIMS

        if not claims:

            return {

                "verdict": "No Matching Fact-Check Found",

                "message": (
                    "Google's Fact Check database did not return "
                    "any previously published fact-checking "
                    "articles matching this claim. This does not "
                    "mean the claim is false, misleading or "
                    "unverified. It only means that no matching "
                    "published review was found in this database. "
                    "Use the separate AI Evidence Assessment "
                    "to investigate the claim using external sources."
                ),

                "results": [],

                "assessment_status": "No Published Review Found"

            }

        # COLLECT PUBLISHED FACT-CHECK REVIEWS

        results = []

        for item in claims:

            if not isinstance(item, dict):
                continue

            claim_text = item.get(
                "text",
                "Claim unavailable"
            )

            reviews = item.get(
                "claimReview",
                []
            )

            if not isinstance(reviews, list):
                continue

            for review in reviews:

                if not isinstance(review, dict):
                    continue

                publisher = review.get(
                    "publisher",
                    {}
                )

                if not isinstance(publisher, dict):
                    publisher = {}

                results.append({

                    "claim": claim_text,

                    "publisher": publisher.get(
                        "name",
                        "Unknown publisher"
                    ),

                    "rating": review.get(
                        "textualRating",
                        "Rating unavailable"
                    ),

                    "title": review.get(
                        "title",
                        "No title available"
                    ),

                    "url": review.get(
                        "url",
                        ""
                    ),

                    "review_date": review.get(
                        "reviewDate",
                        "Date unavailable"
                    )

                })

        # HANDLE EMPTY REVIEW RESULTS

        if not results:

            return {

                "verdict": "No Matching Fact-Check Found",

                "message": (
                    "Google returned claim information but no "
                    "usable published fact-check reviews. "
                    "This is not evidence that the claim is false. "
                    "The claim requires separate investigation "
                    "using reliable external evidence."
                ),

                "results": [],

                "assessment_status": "No Usable Published Review Found"

            }

        # RETURN PUBLISHED FACT-CHECK RESULTS

        return {

            "verdict": "Review Available",

            "message": (
                "Previously published fact-checking reviews "
                "were found. Their ratings are displayed as "
                "reference information. They do not automatically "
                "establish the truth of the submitted claim. "
                "Check whether each review concerns the same "
                "claim, context and date."
            ),

            "results": results,

            "assessment_status": "Requires Evidence Review"

        }

    # ==========================================
    # ERROR HANDLING
    # ==========================================

    except requests.exceptions.Timeout:

        return {
            "error": "Google Fact Check service timed out."
        }

    except requests.exceptions.RequestException:

        return {
            "error": (
                "Unable to connect to Google Fact Check."
            )
        }

    except ValueError:

        return {
            "error": (
                "Google returned an invalid JSON response."
            )
        }

    except Exception as error:

        return {
            "error": (
                f"Unexpected error: {str(error)}"
            )
        }