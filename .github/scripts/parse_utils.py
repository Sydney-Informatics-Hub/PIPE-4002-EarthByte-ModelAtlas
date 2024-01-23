import os
import re
import json
import pandas as pd
import subprocess

from metadata_utils import get_record, get_authors, parse_author, parse_publication, parse_software, is_orcid_format, check_uri

def parse_name_or_orcid(name_or_orcid):
    error_log = ""

    if is_orcid_format(name_or_orcid):
        orcid_record, log1 = get_record("author", name_or_orcid)
        creator_record, log2 = parse_author(orcid_record)
        if log1 or log2:
            error_log += log1 + log2
    else:
        try:
            familyName, givenName = name_or_orcid.split(",")
            creator_record = {
                "@type": "Person",
                "givenName": givenName,
                "familyName": familyName,
            }
        except:
            error_log += f"- Error: name `{name_or_orcid}` in unexpected format. Expected `last name(s), first name(s)` or ORCID. \n"
            creator_record = {}

    return creator_record, error_log

def parse_yes_no_choice(input):
    if "X" in input[0] and "X" in input[1]:
        return "Error: both 'yes' and 'no' selected"
    elif "X" in input[0]:
        return True
    elif "X" in input[1]:
        return False
    else:
        return "Error: no selection made"

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

    # animation

    # graphic abstract

    # model setup figure

    # description



    return data_dict, error_log

def dict_to_report(issue_dict):

    #############
    # Section 1
    #############
    report = "## Section 1: Summary of your model \n"
    # creator/contributor
    report += "**Creator/Contributor**\n"
    report += f"Creator/contributor is {issue_dict['creator']['givenName']} {issue_dict['creator']['familyName']} "
    if "@id" in issue_dict['creator']:
        report += f"([{issue_dict['creator']['@id'].split('/')[-1]}]({issue_dict['creator']['@id']}))"
    report += "\n\n"

    # slug
    report += "**Model Repository Slug**\n"
    report += f"Model repo will be created with name `{issue_dict['slug']}` \n\n"

    # FoR codes
    report += "**Field of Research (FoR) Codes**\n"
    for for_code in issue_dict["for_codes"]:
        report += f"- `{for_code['@id']}`: {for_code['name']} \n"
    report += "\n"

    # license
    report += "**License**\n"
    if "url" in issue_dict["license"]:
        report += f"[{issue_dict['license']['name']}]({issue_dict['license']['url']})\n\n"
    else:
        report += f"{issue_dict['license']['name']}\n\n"

    # model category
    report += "**Model Category**\n"
    for category in issue_dict["model_category"]:
        report += f"- {category} \n"
    report += "\n"

    # associated publication DOI
    if "@id" in issue_dict["publication"]:
        report += "**Associated Publication**\n"
        report += f"Found publication: _[{issue_dict['publication']['name']}]({issue_dict['publication']['@id']})_ \n\n"

    # title
    report += "**Title**\n"
    report += issue_dict["title"] + "\n\n"

    # description
    report += "**Description**\n"
    report += issue_dict["description"] + "\n\n"

    # model authors
    report += "**Model Authors**\n"
    for author in issue_dict["authors"]:
        report += f"- {author['givenName']} {author['familyName']} "
        if "@id" in author:
            report += f"([{author['@id'].split('/')[-1]}]({author['@id']}))"
        report += "\n"
    report += "\n"

    # scientific keywords
    if issue_dict["keywords"]:
        report += "**Scientific Keywords**\n"
        for keyword in issue_dict["keywords"]:
            report += f"- {keyword} \n"
        report += "\n"

    # funder
    report += "**Funder**\n"
    for funder in issue_dict["funder"]:
        report += f"- {funder['name']} "
        if "@id" in funder:
            report += f"({funder['@id']})"
        elif "url" in funder:
            report += f"({funder['url']})"
        report += "\n"
    report += "\n"


    #############
    # Section 2
    #############
    report += "## Section 2: your model code, output data \n"
    # include model code
    if "include_model_code" in issue_dict:
        report += "**Include model code?** \n"
        report += f"{str(issue_dict['include_model_code'])} \n\n"

    # model code URI/DOI
    if "model_code_uri" in issue_dict:
        report += "**Model code URI/DOI** \n"
        report += f"{issue_dict['model_code_uri']} \n\n"

    # include model output data
    if "include_model_output" in issue_dict:
        report += "**Include model output data?** \n"
        report += f"{str(issue_dict['include_model_output'])} \n\n"

    # model output URI/DOI
    if "model_output_uri" in issue_dict:
        report += "**Model output URI/DOI** \n"
        report += f"{issue_dict['model_output_uri']} \n\n"

    #############
    # Section 3
    #############
    report += "## Section 3: software framework and compute details \n"
    # software framework DOI/URI
    if "@id" in issue_dict["software"]:
        report += "**Software Framework DOI/URI**\n"
        report += f"Found software: _[{issue_dict['software']['name']}]({issue_dict['software']['@id']})_ \n\n"

    # software framework source repository
    if "codeRepository" in issue_dict["software"]:
        report += "**Software Repository** \n"
        report += f"{issue_dict['software']['codeRepository']} \n\n"

    # name of primary software framework
    if "name" in issue_dict["software"]:
        report += "**Name of primary software framework**\n"
        report += f"{issue_dict['software']['name']}"

    # software framework authors
    if "author" in issue_dict["software"]:
        report += "**Software framework authors**\n"
        for author in issue_dict["software"]["authors"]:
            if "givenName" in author:
                report += f"- {author['givenName']} {author['familyName']} "
            elif "name" in author:
                report += f"- {author['name']} "
            if "@id" in author:
                report += f"([{author['@id'].split('/')[-1]}]({author['@id']}))"
            report += "\n"
        report += "\n"

    # software & algorithm keywords
    if "keywords" in issue_dict["software"]:
        report += "**Software & algorithm keywords**\n"
        for keyword in issue_dict["software"]["keywords"]:
            report += f"- {keyword} \n"
        report += "\n"

    # computer URI/DOI
    if "computer_uri" in issue_dict:
        report += "**Computer URI/DOI** \n"
        report += f"{issue_dict['computer_uri']} \n\n"

    #############
    # Section 4
    #############
    report += "## Section 4: web material (for mate.science) \n"
    # landing page image and caption
    # animation
    # graphic abstract
    # model setup figure
    # description
    # associated publication DOI   

    report += "\n Dumping dictionary during testing"
    report += str(issue_dict)

    return report

def dict_to_metadata(issue_dict):

    metadata = json.dumps(issue_dict)

    return metadata