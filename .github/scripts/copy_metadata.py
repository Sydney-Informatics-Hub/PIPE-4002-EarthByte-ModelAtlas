import os
import re
import requests
import subprocess
import json
import pandas as pd
from github import Github, Auth

from metadata_utils import get_authors, is_orcid_format, get_record, parse_author, parse_publication, parse_software, get_funders, parse_image_and_caption

token = os.environ.get("GITHUB_TOKEN")
issue_number = int(os.environ.get("ISSUE_NUMBER"))
model_owner = os.environ.get("OWNER")
model_repo_name = os.environ.get("REPO")


# Get issue
auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo("hvidy/PIPE-4002-EarthByte-ModelAtlas")
issue = repo.get_issue(number = issue_number)


# Get model repo
model_repo = g.get_repo(f"{model_owner}/{model_repo_name}")


# Get metadata template
metadata_template_path = '.github/scripts/metadata_V2.json'

with open(metadata_template_path, 'r') as json_file:
    # Load the JSON data from the file
    metadata = json.load(json_file)


# Parse issue body
# Identify headings and subsequent text
regex = r"### *(?P<key>.*?)\s*[\r\n]+(?P<value>[\s\S]*?)(?=###|$)"
data = dict(re.findall(regex, issue.body))

#############
# Section 1
#############

# Creator/contributor
creator = data["-> creator/contributor ORCID (or name)"].strip()

if is_orcid_format(creator):
    orcid_record,log1 = get_record("author", creator)
    creator_record, log2 = parse_author(orcid_record)
else:
    familyName, givenName = author.split(",")
    creator_record = {
        "@type": "Person",
        "givenName": givenName,
        "familyName": familyName,
    }

metadata["creator"] = creator_record


# Repo name
metadata["name"] = model_repo_name

# FoR codes
for_codes = [x.strip() for x in data["-> field of Research (FoR) Codes"].split(",")]
for_code_ref = pd.read_csv(".github/scripts/for_codes.csv", dtype=str)

about_record = []
for for_code in for_codes:
    record = for_code_ref.loc[for_code_ref["code"] == for_code]
    if not record.empty:
        for_id = "#FoR_"+record.code.values[0]
        about_record.append({"@id": for_id, "@type": "DefinedTerm", "name": record.name.values[0]})

metadata["about"] = about_record

# License
license = data["-> license"].strip()

metadata["license"] = license

# Model category
model_categories = data["-> model category"].strip().split(", ")

# metadata["??"] = model_cateogires

# Associated Publication
publication_doi = data["-> associated publication DOI"].strip()

if publication_doi != "_No response_":
    publication_metadata, log1 = get_record("publication", publication_doi)
    publication_record, log2 = parse_publication(publication_metadata)

metadata["citation"] = publication_record

# Title
title = data["-> title"].strip()

if title == "_No response_":
    try:
        title = publication_record['name']
    except:
        title = ""

# metadata["name"] is already used for slug

# Description
description = data["-> description"].strip()

if description == "_No response_":
    try:
        description = publication_record['abstract']
    except:
        description = ""

metadata["description"] = description


# Identify authors
authors = data['-> model authors'].strip().split('\r\n')

if authors[0] == "_No response_":
    try:
        author_list = publication_record["author"]
    except:
        author_list = {}
else:
    author_list, log = get_authors(authors)

metadata["author"] = author_list


# Scientific Keywords
keywords = data["-> scientific keywords"].strip().split(", ")

metadata["keywords"] = keywords

# Identify funders
funders = data["-> funder"].strip().split(", ")

if funders[0] == "_No response_":
    try:
        funder_list = publication_record['funder']
    except:
        funder_list = {}
else:
    funder_list, log = get_funders(funders)

metadata["funder"] = funder_list

#############
# Section 2
#############

#############
# Section 3
#############

# Software Framework DOI
software_doi = data["-> software framework DOI/URI"].strip().split("zenodo.")[1]

if software_doi == "_No response_":
    software_record={"@type": "SoftwareApplication"}
else:
    software_metadata, log1 = get_record("software", software_doi)
    software_record, log2 = parse_software(software_metadata)


# Software Repository
software_repo = data["-> software framework source repository"].strip()

if software_repo != "_No response_":
    software_record["codeRepository"] = software_repo


# Software Name
software_name = data["-> name of primary software framework (e.g. Underworld, ASPECT, Badlands, OpenFOAM)"].strip()

if software_name == "_No response_":
    try:
        software_name = software_record['name']
    except:
        software_name = ""
else:
    software_record["name"] = software_name


# Software Authors
authors = data['-> software framework authors'].strip().split('\r\n')

if authors[0] == "_No response_":
    try:
        software_author_list = software_record["author"]
    except:
        software_author_list = {}
else:
    software_author_list, log = get_authors(authors)
    software_record["author"] = software_author_list

# Software Keywords
software_keywords = data["-> software & algorithm keywords"].strip().split(", ")
if software_keywords[0] != "_No response_":
    software_record["keywords"] = software_keywords


# Computer URI/DOI
computer_doi = data["-> computer URI/DOI"].strip()

metadata["hasPart"][1] = software_record

#############
# Section 4
#############

website_metadata = {}

# Landing page image and caption
img_string = data["-> add landing page image and caption"].strip()

if img_string != "_No response_":
    landing_image_record, log = parse_image_and_caption(img_string, "landing_image")
    website_metadata["landing_image"] = landing_image_record

# Animation
img_string = data["-> add an animation (if relevant)"].strip()

if img_string != "_No response_":
    animation_record, log = parse_image_and_caption(img_string, "animation")
    website_metadata["animation"] = animation_record

# Graphic abstract
img_string = data["-> add a graphic abstract figure (if relevant)"].strip()

if img_string != "_No response_":
    graphic_abstract_record, log = parse_image_and_caption(img_string, "graphic_abstract")
    website_metadata["graphic_abstract"] = graphic_abstract_record

# Model setup figure
img_string = data["-> add a model setup figure (if relevant)"].strip()

if img_string != "_No response_":
    model_setup_fig_record, log = parse_image_and_caption(img_string, "model_setup_figure")
    website_metadata["model_setup_figure"] = model_setup_fig_record

# Model setup description
model_description = data["-> add a description of your model setup"].strip()
website_metadata["model_description"] = model_description


# Move files to repo
model_repo.create_file(".metadata/mate.json","add mate.json",json.dumps(metadata))
model_repo.create_file("website_files/website_metadata.json","add website_metadata.json",json.dumps(website_metadata))

issue.create_comment(f"Model repository created at https://github.com/{model_owner}/{model_repo_name}")