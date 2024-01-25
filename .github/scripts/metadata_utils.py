import os
import re
import orcid
import requests
import filetype
from filetypes import Svg

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

def parse_author(metadata):
    log = ""
    author_record = {}
    
    try:
        author_record = {
            "@type": "Person",
            "@id": metadata["orcid-identifier"]["uri"],
            "givenName": metadata['person']['name']['given-names']['value'],
            "familyName": metadata['person']['name']['family-name']['value'],
        }
        
        affiliation_list = []
        for affiliation in metadata["activities-summary"]["employments"]["affiliation-group"]:
            summary = affiliation["summaries"][0]["employment-summary"]
            if summary["end-date"] is None:
                affiliation_list.append({"@type": "Organization", "name": summary["organization"]["name"]})

        if affiliation_list:
            author_record["affiliation"] = affiliation_list

    except Exception as err:
        log += "Error: unable to parse author metadata. \n"
        log += f"`{err}`\n"

    return author_record, log

def parse_organization(metadata):
    log = ""
    org_record = {}

    try:
       org_record = {
           "@type": "Organization",
           "@id": metadata["id"],
           "name": metadata["name"],
       }

    except Exception as err:
        log += "Error: unable to parse organization metadata. \n"
        log += f"`{err}`\n"

    return org_record, log


def parse_software(metadata):
    log = ""
    software_record = {}

    try:
        software_record = {
            "@type": "SoftwareApplication", # and/or SoftwareSourceCode?
            "@id": metadata["doi_url"],
            "name": metadata["title"],
            "softwareVersion": metadata["metadata"]["version"]
            # Other keywords to be crosswalked
        }

        author_list = []

        for author in metadata["metadata"]["creators"]:
            author_record = {"@type": "Person"}
            if "orcid" in author:
                author_record["@id"] = author["orcid"]
            if "givenName" in author:
                author_record["givenName"] = author["given"]
                author_record["familyName"] = author["family"]
            elif "name" in author:
                author_record["name"] = author["name"]
            if "affiliation" in author:
                author_record["affiliation"] = author["affiliation"]
    
            author_list.append(author_record)

        if author_list:
            software_record["author"] = author_list


    except Exception as err:
        log += "Error: unable to parse software metadata. \n"
        log += f"`{err}`\n"

    return software_record, log

def parse_publication(metadata):
    log = ""
    publication_record = {}

    metadata = metadata['message']

    try:
        publication_record = {
            "@type": "ScholarlyArticle",
            "@id": metadata["URL"],
            "name": metadata["title"][0],
            }

        if "issue" in metadata:
            publication_issue = {
                "@type": "PublicationIssue",
                "issueNumber": metadata["issue"],
                "datePublished": '-'.join(map(str,metadata["published"]["date-parts"][0])),
                "isPartOf": {
                    "@type": [
                        "PublicationVolume",
                        "Periodical"
                    ],
                    "name": metadata["container-title"],
                    "issn": metadata["ISSN"],
                    "volumeNumber": metadata["volume"],
                    "publisher": metadata["publisher"]
                },
            },

            publication_record["isPartOf"] = publication_issue
        else:
            if metadata["published"]:
                publication_record["datePublished"] = '-'.join(map(str,metadata["published"]["date-parts"][0]))
            if metadata["publisher"]:
                publication_record["publisher"] = metadata["publisher"]

        author_list = []

        for author in metadata["author"]:
            author_record = {"@type": "Person"}
            if "ORCID" in author:
                author_record["@id"] = author["ORCID"]
            author_record["givenName"] = author["given"]
            author_record["familyName"] = author["family"]
    
            affiliation_list = []
            for affiliation in author["affiliation"]:
                affiliation_list.append({"@type": "Organization", "name": affiliation["name"]})
                
            if affiliation_list:
                author_record["affiliation"] = affiliation_list
    
            author_list.append(author_record)

        if author_list:
            publication_record["author"] = author_list

        if "abstract" in metadata:
            publication_record["abstract"] = metadata["abstract"].split('<jats:p>')[1].split('</jats:p>')[0]
    
        if "page" in metadata:
            publication_record["pagination"] = metadata["page"]
    
        if "alternative-id" in metadata:
            publication_record["identifier"] = metadata["alternative-id"]
    
        if "funder" in metadata:
            funder_list = []
            for funder in metadata["funder"]:
                funder_list.append({"@type": "Organization", "name": funder["name"]})
            publication_record["funder"] = funder_list

    except Exception as err:
        log += "Error: unable to parse publication metadata. \n"
        log += f"`{err}`\n"

    return publication_record, log


def is_orcid_format(author):

    orcid_pattern = re.compile(r'\d{4}-\d{4}-\d{4}-\d{3}[0-9X]')

    if orcid_pattern.fullmatch(author):
        return True
    else:
        return False


def get_authors(author_list):
    '''
    Parses a list of author names or ORCID iDs and returns a list of dictionaries of schema.org Person type

        Parameters:
            author_list (list of strings): list of names in format Last Name(s), First Name(s) and/or ORCID iDs

        Returns:
            authors (list of dicts)
            log (string)

    '''

    log = ""
    authors = []

    for author in author_list:
        author_record, error_log = parse_name_or_orcid(author)
        if author_record:
            authors.append(author_record)
        if error_log:
            log += error_log

    return authors, log

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



def get_funders(funder_list):

    log = ""
    funders = []

    for funder in funder_list:
        if "ror.org" not in funder:
            ror_id, get_log = search_organization(funder)
            log += get_log

            if not ror_id:
                funders.append({"@type": "Organization", "name": funder, "url": funder})
            else:
                funder = ror_id

        if "ror.org" in funder:
            record, get_log = get_record("organization", funder)
            funder_record, parse_log = parse_organization(record)
            if get_log or parse_log:
                log += get_log + parse_log
            else:
                funders.append(funder_record)

    return funders, log


def parse_image_and_caption(img_string, default_filename):
    log = ""
    image_record = {}
    
    md_regex = r"\[(?P<filename>.*?)\]\((?P<url>.*?)\)"
    html_regex = r'alt="(?P<filename>[^"]+)" src="(?P<url>[^"]+)"'

    # Hack to recognise SVG files
    filetype.add_type(Svg())

    caption = []

    for string in img_string.split("\r\n"):
        if "https://" in string:
            try:
                image_record = re.search(md_regex, string).groupdict()
            except:
                if string.startswith("https://"):
                    image_record = {"filename": default_filename, "url": string}
                elif "src" in string:
                    image_record = re.search(html_regex, string).groupdict()
                else:
                    log += "Error: Could not parse image file and caption\n"
        else:
            caption.append(string)

    # Get correct file extension for images
    if "url" in image_record:
        response = requests.get(image_record["url"])
        content_type = response.headers.get("Content-Type")[:5]
        if content_type in ["video", "image"]:
            image_record["filename"] += "." + filetype.get_type(mime=response.headers.get("Content-Type")).extension

    image_record["caption"] = "\n".join(caption)

    if not caption:
        log += "Error: No caption found for image.\n"

    return image_record, log

def check_uri(uri):
    try:
        response = requests.get(uri)
        response.raise_for_status()  # Raise an exception for HTTP errors

        return "OK"

    except Exception as err:
        return err.args[0]