import requests

base_urls = {
    "publication": "https://api.crossref.org/works/",
    "software": "https://zenodo.org/api/records/",
    "organization": "https://api.ror.org/organizations/",
    "author": "https://pub.orcid.org/v3.0/"
}

def get_record(record_type,record_id):
    log = ""
    metadata = {}

    assert (record_type in ["publication","software","organization","author"]), f"Record type `{record_type}` not supported"

    url = base_urls[record_type] + record_id
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse JSON response
        metadata = response.json()

    except requests.exceptions.RequestException as e:
        log += f"Error fetching metadata: {e} \n"

    return metadata, log


def search_organization(org_url):
    log = ""
    ror_id = ""
    result = {}
    
    base_url = "https://api.ror.org/organizations"
    org_url = org_url.split("://")[-1]

    #Check if last character is a '/' and if so drop it
    if org_url[-1] == "/": org_url = org_url[:-1]

    url = base_url + '?query.advanced=links:' + org_url
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        result = response.json()

    except requests.exceptions.RequestException as e:
        log += f"Error fetching metadata: {e} \n"

    # Deal with response and determine ROR ID
    if result["number_of_results"] == 0:
        log += f"Unable to find ROR for {org_url} \n"
    elif result["number_of_results"] == 1:
        ror_id = result["items"][0]["id"]
        log += f"Found ROR record for {org_url}: {result['items'][0]['name']} ({ror_id}) \n"
        for relation in result["items"][0]["relationships"]:
            if relation["type"] == "Parent":
                log += f"Note: This organization has a parent organization: {relation['label']} ({relation['id']}) \n"
    else:
        ror_id = result["items"][0]["id"]
        log += f"Found more than one ROR record for {org_url}. Assuming the first result is correct; if not please enter the correct ROR. \n"
        for record in result["items"]:
            log += f"\t - {record['name']} ({record['id']}) \n"

    return ror_id, log


def check_uri(uri):
    try:
        response = requests.get(uri)
        response.raise_for_status()  # Raise an exception for HTTP errors

        return "OK"

    except Exception as err:
        return err.args[0]