import requests
import trafilatura

from urllib.parse import urlparse
from ipaddress import ip_address
import socket


# VALIDATE PUBLIC URLS

def validate_url(url):

    try:

        if not isinstance(url, str) or not url.strip():
            return False, "Please enter a valid URL."

        url = url.strip()

        parsed_url = urlparse(url)

        # ALLOW ONLY HTTP AND HTTPS

        if parsed_url.scheme.lower() not in ["http", "https"]:
            return False, "Only HTTP and HTTPS URLs are allowed."

        hostname = parsed_url.hostname

        if not hostname:
            return False, "Invalid URL."

        hostname = hostname.rstrip(".").lower()

        # BLOCK LOCALHOST

        if hostname in ["localhost", "localhost.localdomain"]:
            return False, "Localhost URLs are not allowed."

        # BLOCK URLS CONTAINING USER CREDENTIALS

        if parsed_url.username or parsed_url.password:
            return False, "URLs containing login credentials are not allowed."

        # VALIDATE PORT

        try:
            port = parsed_url.port

            if port is not None and not (1 <= port <= 65535):
                return False, "Invalid URL port."

        except ValueError:
            return False, "Invalid URL port."

        # CHECK DIRECT IP ADDRESS

        try:

            ip = ip_address(hostname)

            if not ip.is_global:
                return False, "Private or local IP addresses are not allowed."

        except ValueError:

            # RESOLVE DOMAIN NAME

            try:

                addresses = socket.getaddrinfo(
                    hostname,
                    None,
                    type=socket.SOCK_STREAM
                )

                if not addresses:
                    return False, "Unable to resolve the website address."

                # CHECK EVERY RESOLVED IP ADDRESS

                for address in addresses:

                    resolved_ip = ip_address(address[4][0])

                    if not resolved_ip.is_global:
                        return False, (
                            "URL resolves to a private or local address."
                        )

            except socket.gaierror:
                return False, "Unable to resolve the website address."

        return True, "URL is valid."

    except Exception:

        return False, "Unable to validate this URL."


# EXTRACT ARTICLE CONTENT

def extract_article(url):

    try:

        # VALIDATE URL BEFORE ACCESSING IT

        is_valid, message = validate_url(url)

        if not is_valid:
            return {"error": message}

        url = url.strip()

        # RETRIEVE PUBLIC WEBPAGE

        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "DeepfakeDetective/1.0"
            },
            allow_redirects=False,
            stream=True
        )

        # HANDLE WEBSITE ACCESS RESTRICTIONS

        if response.status_code == 403:

            return {
                "error": (
                    "This website blocks automated access. "
                    "Please try another public article URL "
                    "or paste the article text manually."
                )
            }

        if response.status_code == 429:

            return {
                "error": (
                    "This website is temporarily limiting requests. "
                    "Please try again later."
                )
            }

        # DO NOT FOLLOW REDIRECTS AUTOMATICALLY

        if response.is_redirect:

            return {
                "error": (
                    "The website redirected the request. "
                    "Please enter the final public article URL."
                )
            }

        response.raise_for_status()

        # CHECK CONTENT TYPE

        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()

        if "text/html" not in content_type:

            return {
                "error": "The URL does not contain an HTML webpage."
            }

        # READ WEBPAGE CONTENT

        downloaded = response.text

        if not downloaded.strip():

            return {
                "error": "The webpage returned empty content."
            }

        # EXTRACT ARTICLE TEXT

        article_text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False
        )

        # EXTRACT ARTICLE METADATA

        metadata = trafilatura.extract_metadata(downloaded)

        if not article_text:

            return {
                "error": (
                    "Could not extract article text from this webpage. "
                    "You can paste the article text manually instead."
                )
            }

        title = (
            metadata.title
            if metadata and metadata.title
            else "Title unavailable"
        )

        return {
            "title": title,
            "text": article_text,
            "url": url
        }

    except requests.exceptions.Timeout:

        return {
            "error": "The webpage took too long to respond."
        }

    except requests.exceptions.SSLError:

        return {
            "error": (
                "SSL connection error. Please check the website."
            )
        }

    except requests.exceptions.HTTPError:

        return {
            "error": "The website returned an HTTP error."
        }

    except requests.exceptions.RequestException:

        return {
            "error": (
                "A network or webpage connection error occurred."
            )
        }

    except Exception:

        return {
            "error": (
                "An unexpected error occurred while extracting "
                "the article."
            )
        }
