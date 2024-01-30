import os
import re
import json
import pandas as pd
import subprocess

from request_utils import get_record, check_uri, search_organization
from parse_metadata_utils import parse_author, parse_publication, parse_software, parse_organization

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


def parse_issue(issue):
    error_log = ""

    # Parse issue body
    # Identify headings and subsequent text
    regex = r"### *(?P<key>.*?)\s*[\r\n]+(?P<value>[\s\S]*?)(?=###|$)"
    data = dict(re.findall(regex, issue.body))

    data_dict = {}

    #############
    # Section 1
    #############
    # creator/contributor
    creator = data["-> creator/contributor ORCID (or name)"].strip()
    creator_record, log = parse_name_or_orcid(creator)
    data_dict["creator"] = creator_record
    if log:
        error_log += "**Creator/Contributor**\n" + log +"\n"

    # slug
    proposed_slug = data["-> slug"].strip()
    cmd = "python3 .github/scripts/generate_identifier.py"
    try:
        slug = subprocess.check_output(cmd, shell=True, text=True, stderr=open(os.devnull)).strip()
        data_dict["slug"] = slug
        if proposed_slug != slug:
            error_log += "**Model Repository Slug**\n"
            error_log += f"Warning: Model repo cannot be created with proposed slug `{proposed_slug}`. \n"
            error_log += f"Either propose a new slug or repo will be created with name `{slug}`. \n" 
    except Exception as err:
        data_dict["slug"] = ""
        error_log += "**Model Repository Slug**\n"
        error_log += "Error: Unable to create valid repo name... \n"
        error_log += f"`{err}`\n"

    # FoR codes
    for_codes = [x.strip() for x in data["-> field of Research (FoR) Codes"].split(",")]
    for_code_lut = pd.read_csv(".github/scripts/for_codes.csv", dtype=str)

    about_record = []
    for for_code in for_codes:
        record = for_code_lut.loc[for_code_lut["code"] == for_code]
        if record.empty:
            error_log += "**Field of Research (FoR) Codes**\n"
            error_log += f"Error: FoR code `{for_code}` not found in look-up table\n"
        else:
            for_id = "#FoR_"+record.code.values[0]
            about_record.append({"@id": for_id, "@type": "DefinedTerm", "name": record.name.values[0]})
    data_dict["for_codes"] = about_record

    # license
    license = data["-> license"].strip()
    license_lut = pd.read_csv(".github/scripts/licenses.csv", dtype=str)

    license_record = {}
    if license != "No license":
        license_record["name"] = license_lut[license_lut.license == license].name.values[0]
        license_record["url"] = license_lut[license_lut.license == license].url.values[0]
    else:
        license_record["name"] = "No license"
    data_dict["license"] = license_record

    # model category
    model_category = [x.strip() for x in data["-> model category"].split(",")]

    if model_category[0] == "_No response_":
        model_category = []
        error_log += "**Model category**\n"
        error_log += "Warning: No category selected \n"

    data_dict["model_category"] = model_category


    # associated publication DOI
    publication_doi = data["-> associated publication DOI"].strip()
    publication_record = {}

    if publication_doi == "_No response_":
        error_log += "**Associated Publication**\n"
        error_log += "Warning: No DOI provided. \n"
    else:
        try:
            publication_metadata, log1 = get_record("publication", publication_doi)
            publication_record, log2 = parse_publication(publication_metadata)
            if log1 or log2:
                error_log += "**Associated Publication**\n" + log1 + log2
        except Exception as err:
            error_log += "**Associated Publication**\n"
            error_log += f"Error: unable to obtain metadata for DOI `{publication_doi}` \n"
            error_log += f"`{err}`\n"
    
    data_dict["publication"] = publication_record

    # title
    title = data["-> title"].strip()

    if title == "_No response_":
        try:
            title = publication_record['name']
        except:
            title = ""
            error_log += "**Title**\n"
            error_log += "Error: no title found \n"

    data_dict["title"] = title

    # description
    description = data["-> description"].strip()

    if description == "_No response_":
        try:
            description = publication_record['abstract']
        except:
            description = ""
            error_log += "**Description**\n"
            error_log += "Error: no descrition found, nor abstract for associated publication \n"

    data_dict["description"] = description

    # model authors
    authors = data['-> model authors'].strip().split('\r\n')

    if authors[0] == "_No response_":
        try:
            author_list = publication_record["author"]
        except:
            author_list = []
            error_log += "**Model authors**\n"
            error_log += "Error: no authors found \n"
    else:
        author_list, log = get_authors(authors)
        if log:
            error_log += "**Model authors**\n" + log

    data_dict["authors"] = author_list

    # scientific keywords
    keywords = [x.strip() for x in data["-> scientific keywords"].split(",")]

    if keywords[0] == "_No response_":
        keywords = []
        error_log += "**Scientific keywords**\n"
        error_log += "Warning: No keywords given \n"

    data_dict["keywords"] = keywords

    # funder
    funders = [x.strip() for x in data["-> funder"].split(",")]

    if funders[0] == "_No response_":
        try:
            funder_list = publication_record['funder']
        except:
            funder_list = []
            error_log += "**Funder**\n"
            error_log += "Warning: No funders provided or found in publication. \n"
    else:
        funder_list, log = get_funders(funders)
        if log:
            error_log += "**Funder**\n" + log

    data_dict["funder"] = funder_list

    #############
    # Section 2
    #############
    # include model code
    model_code = data["-> include model code ?"].strip().split("\n")

    selection = parse_yes_no_choice(model_code)
    if type(selection) is bool:
        data_dict["include_model_code"] = selection
    if type(selection) is str:
        error_log += "**Include model code?**\n" + selection + "\n"

    # model code URI/DOI
    model_code_uri = data["-> model code URI/DOI"].strip()

    if model_code_uri == "_No response_":
        error_log += "**Model code URI/DOI**\n"
        error_log += "Warning: No URI/DOI provided. \n"
    else:
        response = check_uri(model_code_uri)
        if response == "OK":
            data_dict["model_code_uri"] = model_code_uri
        else:
            error_log += "**Model code URI/DOI**\n" + response + "\n"

    # include model output data
    model_output = data["-> include model output data?"].strip().split("\n")
    
    selection = parse_yes_no_choice(model_output)
    if type(selection) is bool:
        data_dict["include_model_output"] = selection
    if type(selection) is str:
        error_log += "**Include model output data?**\n" + selection + "\n"

    # model output URI/DOI
    model_output_uri = data["-> model output URI/DOI"].strip()

    if model_output_uri == "_No response_":
        error_log += "**Model output URI/DOI**\n"
        error_log += "Warning: No URI/DOI provided. \n"
    else:
        response = check_uri(model_output_uri)
        if response == "OK":
            data_dict["model_output_uri"] = model_output_uri
        else:
            error_log += "**Model output URI/DOI**\n" + response + "\n"


    #############
    # Section 3
    #############
    # software framework DOI/URI
    software_doi = data["-> software framework DOI/URI"].strip()

    software_record={"@type": "SoftwareApplication"}

    if software_doi == "_No response_":
        error_log += "**Software Framework DOI/URI**\n"
        error_log += "Warning: no DOI/URI provided.\n"
    else:
        if "zenodo" in software_doi:
            software_doi = software_doi.split("zenodo.")[1]
            try:
                software_metadata, log1 = get_record("software", software_doi)
                software_record, log2 = parse_software(software_metadata)
                if log1 or log2:
                    error_log += "**Software Framework DOI/URI**\n" + log1 + log2
            except Exception as err:
                error_log += "**Software Framework DOI/URI**\n"
                error_log += f"Error: unable to obtain metadata for DOI `{software_doi}` \n"
                error_log += f"`{err}`\n"
        else:
            error_log += "**Software Framework DOI/URI**\n Non-Zenodo software dois not yet supported\n"

    # software framework source repository
    software_repo = data["-> software framework source repository"].strip()

    if software_repo == "_No response_":
        error_log += "**Software Repository**\n"
        error_log += "Warning: no repository URL provided. \n"
    else:
        response = check_uri(software_repo)
        if response == "OK":
            software_record["codeRepository"] = software_repo
        else:
            error_log += "**Software Repository**\n" + response + "\n"

    # name of primary software framework
    software_name = data["-> name of primary software framework (e.g. Underworld, ASPECT, Badlands, OpenFOAM)"].strip()

    if software_name == "_No response_":
        try:
            software_name = software_record['name']
        except:
            error_log += "**Name of primary software framework**\n"
            error_log += "Error: no name found \n"
    else:
        software_record["name"] = software_name     # N.B. this will overwrite any name obtained from the DOI

    # software framework authors
    authors = data['-> software framework authors'].strip().split('\r\n')

    if authors[0] == "_No response_":
        try:
            software_author_list = software_record["author"]
        except:
            software_author_list = []
            error_log += "**Software framework authors**\n"
            error_log += "Error: no authors found \n"
    else:
        software_author_list, log = get_authors(authors)
        software_record["author"] = software_author_list     # N.B. this will overwrite any name obtained from the DOI
        if log:
            error_log += "**Software framework authors**\n" + log

    # software & algorithm keywords
    software_keywords = [x.strip() for x in data["-> software & algorithm keywords"].split(",")]

    if software_keywords[0] == "_No response_":
        error_log += "**Software & algorithm keywords**\n"
        error_log += "Warning: no keywords given. \n"
    else:
        software_record["keywords"] = software_keywords

    data_dict["software"] = software_record

    # computer URI/DOI
    computer_uri = data["-> computer URI/DOI"].strip()

    if computer_uri == "_No response_":
        error_log += "**Computer URI/DOI**\n"
        error_log += "Warning: No URI/DOI provided. \n"
    else:
        response = check_uri(computer_uri)
        if response == "OK":
            data_dict["computer_uri"] = computer_uri
        else:
            error_log += "**Computer URI/DOI**\n" + response + "\n"

    #############
    # Section 4
    #############
    # landing page image and caption
    img_string = data["-> add landing page image and caption"].strip()

    if img_string == "_No response_":
        error_log += "**Landing page image**\n"
        error_log += "Error: No image uploaded.\n\n"
    else:
        landing_image_record, log = parse_image_and_caption(img_string, "landing_image")
        if log:
            error_log += "**Landing page image**\n" + log + "\n"
        data_dict["landing_image"] = landing_image_record

    # animation
    img_string = data["-> add an animation (if relevant)"].strip()

    if img_string == "_No response_":
        error_log += "**Animation**\n"
        error_log += "Warning: No animation uploaded.\n\n"
    else:
        animation_record, log = parse_image_and_caption(img_string, "animation")
        if log:
            error_log += "**Animation**\n" + log + "\n"
        data_dict["animation"] = animation_record

    # graphic abstract
    img_string = data["-> add a graphic abstract figure (if relevant)"].strip()

    if img_string == "_No response_":
        error_log += "**Graphic abstract**\n"
        error_log += "Warning: No image uploaded.\n\n"
    else:
        graphic_abstract_record, log = parse_image_and_caption(img_string, "graphic_abstract")
        if log:
            error_log += "**Graphic abstract**\n" + log + "\n"
        data_dict["graphic_abstract"] = graphic_abstract_record

    # model setup figure
    img_string = data["-> add a model setup figure (if relevant)"].strip()

    if img_string == "_No response_":
        error_log += "**Model setup figure**\n"
        error_log += "Warning: No image uploaded.\n\n"
    else:
        model_setup_fig_record, log = parse_image_and_caption(img_string, "model_setup")
        if log:
            error_log += "**Model setup figure**\n" + log + "\n"
        data_dict["model_setup_figure"] = model_setup_fig_record

    # description
    model_description = data["-> add a description of your model setup"].strip()

    if model_description == "_No response_":
        error_log += "**Model setup description**\n"
        error_log += "Warning: No description given \n"
    else:
        data_dict["model_setup_description"] = model_description


    return data_dict, error_log

