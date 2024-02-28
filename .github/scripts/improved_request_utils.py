
import requests
import logging
import os
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URLs configuration
BASE_URLS = {
    "publication": os.getenv("BASE_URL_PUBLICATION", "https://api.crossref.org/works/"),
    "software": os.getenv("BASE_URL_SOFTWARE", "https://zenodo.org/api/records/"),
    "organization": os.getenv("BASE_URL_ORGANIZATION", "https://api.ror.org/organizations/"),
    "author": os.getenv("BASE_URL_AUTHOR", "https://pub.orcid.org/v3.0/")
}

# Default timeout
TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", 10))

# Initialize a requests session
session = requests.Session()

def handle_request_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs), ""
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.reason}")
        except requests.exceptions.ConnectionError:
            logger.error("Connection error")
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching metadata: {e}")
        return None, "An error occurred during the request."
    return wrapper

@handle_request_errors
def get_record(record_type, record_id):
    """
    Fetches and returns a record from an API based on the provided record type and ID.

    Parameters:
    - record_type (str): The type of the record to fetch (e.g., 'publication').
    - record_id (str): The unique identifier for the record.

    Returns:
    The API response as a JSON object.
    """

    if record_type not in BASE_URLS:
        raise ValueError(f"Record type `{record_type}` not supported")

    url = BASE_URLS[record_type] + record_id
    headers = {"Content-Type": "application/json"}

    response = session.get(url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()

@handle_request_errors
def search_organization(org_url):

    """
    Searches for an organization's information based on a provided URL or identifier.

    Parameters:
    - org_url (str): The URL or identifier of the organization to search for.

    Returns:
    The search results as a JSON object.
    """

    base_url = BASE_URLS["organization"]
    org_url = org_url.split("://")[-1].rstrip('/')

    url = f"{base_url}?query.advanced=links:{org_url}"
    headers = {"Content-Type": "application/json"}

    response = session.get(url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return process_search_results(response.json())

def process_search_results(results):
    if results["number_of_results"] == 0:
        logger.info(f"Unable to find ROR for the provided URL.")
    elif results["number_of_results"] == 1:
        ror_id = results["items"][0]["id"]
        logger.info(f"Found ROR record: {results['items'][0]['name']} ({ror_id})")
    else:
        logger.info("Found more than one ROR record. Please review the results.")
    return results

def check_uri(uri):

    """
    Checks the availability or validity of a URI by making an HTTP GET request.

    Parameters:
    - uri (str): The URI to check.

    Returns:
    'OK' if the request is successful, or an error message if not.
    """



    try:
        response = session.get(uri, timeout=TIMEOUT)
        response.raise_for_status()
        return "OK"
    except Exception as err:
        return str(err.args[0])

if __name__ == "__main__":
    # Example usage
    logger.info("Request Utils Script")
