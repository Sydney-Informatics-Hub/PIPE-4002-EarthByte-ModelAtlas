import re
import requests
import filetype
from filetypes import Svg

from improved_request_utils import get_record, search_organization
from parse_metadata_utils import parse_author, parse_organization

def parse_name_or_orcid(name_or_orcid):
    error_log = ""

    if is_orcid_format(name_or_orcid):
        orcid_record, log1 = get_record("author", name_or_orcid)
        author_record, log2 = parse_author(orcid_record)
        if log1 or log2:
            error_log += log1 + log2
    else:
        try:
            familyName, givenName = name_or_orcid.split(",")
            author_record = {
                "@type": "Person",
                "givenName": givenName,
                "familyName": familyName,
            }
        except:
            error_log += f"- Error: name `{name_or_orcid}` in unexpected format. Expected `last name(s), first name(s)` or ORCID. \n"
            author_record = {}

    return author_record, error_log

def parse_yes_no_choice(input):
    if "X" in input[0] and "X" in input[1]:
        return "Error: both 'yes' and 'no' selected"
    elif "X" in input[0]:
        return True
    elif "X" in input[1]:
        return False
    else:
        return "Error: no selection made"

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
