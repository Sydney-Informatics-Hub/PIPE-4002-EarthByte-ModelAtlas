import os
import re
import filetype
import requests
import subprocess
from github import Github, Auth

from metadata_utils import get_authors, is_orcid_format, get_record, parse_author, parse_publication, get_funders

token = os.environ.get("GITHUB_TOKEN")
issue_number = int(os.environ.get("ISSUE_NUMBER"))

parse_log = "Thank you for submitting. Please check the output below, and fix any errors, etc.\n\n"

# Get issue
auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo("hvidy/PIPE-4002-EarthByte-ModelAtlas")
issue = repo.get_issue(number = issue_number)


# Parse issue body
# Identify headings and subsequent text
regex = r"### *(?P<key>.*?)\s*[\r\n]+(?P<value>[\s\S]*?)(?=###|$)"
data = dict(re.findall(regex, issue.body))

#############
# Section 1
#############

# Creator/contributor
parse_log += '**Creator/Contributor**\n'

creator = data["-> creator/contributor ORCID (or name)"].strip()

if is_orcid_format(creator):
    orcid_record,log1 = get_record("author", creator)
    creator_record, log2 = parse_author(orcid_record)
    if log1 or log2:
        parse_log += log1 + log2
    else:
        parse_log += f"Creator/contributor is {creator_record['givenName']} {creator_record['familyName']} ({creator_record['@id']})\n"
else:
    try:
        familyName, givenName = author.split(",")
        creator_record = {
            "@type": "Person",
            "givenName": givenName,
            "familyName": familyName,
        }
        parse_log += f"Creator/contributor is {creator_record['givenName']} {creator_record['familyName']}\n"
    except:
        log += f"- Error: creator name `{author}` in unexpected format. Expected `last name(s), first name(s)` or ORCID. \n"

parse_log += "\n"


# Verify repo name can be created
parse_log += "**Model Repository Slug**\n"

proposed_slug = data["-> slug"].strip()
os.environ['SLUG'] = proposed_slug
cmd = "python3 .github/scripts/generate_identifier.py"
try:
    slug = subprocess.check_output(cmd, shell=True, text=True, stderr=open(os.devnull)).strip()
    if proposed_slug != slug:
        parse_log += f"Warning: Model repo cannot be created with proposed slug `{proposed_slug}`. \n"
        parse_log += f"Either propose a new slug or repo will be created with name `{slug}`. \n" 
    else:
        parse_log += f"Model repo will be created with name `{slug}` \n"
except Exception as err:
    parse_log += "- Unable to create valid repo name... \n"
    parse_log += f"`{err}`\n"

parse_log += "\n"


# FoR codes
parse_log += "**Field of Research (FoR) Codes**\n"

for_codes = data["-> field of Research (FoR) Codes"].strip().split(", ")

about_record = []
for for_code in for_codes:
    id = "#FoR_"+for_code.split(":")[0]
    about_record.append({"@id": id, "@type": "DefinedTerm", "name": for_code})
    parse_log += for_code + "\n"

parse_log += "\n"


# License
parse_log += "**License**\n"

license = data["-> license"].strip()
parse_log += license + "\n"

parse_log += "\n"


# Model category
parse_log += "**Model category**\n"

model_categories = data["-> model category"].strip().split(", ")
for model_category in model_categories:
    parse_log += f"- {model_category} \n"

parse_log += "\n" 


# Associated Publication
parse_log += "**Associated Publication**\n"

publication_doi = data["-> associated publication DOI"].strip()

if publication_doi == "_No response_":
    parse_log += "No DOI provided. \n"
else:
    try:
        publication_metadata, log1 = get_record("publication", publication_doi)
        publication_record, log2 = parse_publication(publication_metadata)
        if log1 or log2:
            parse_log += log1 + log2
        else:
            parse_log += f"Found publication: _{publication_record['name']}_. \n"
    except Exception as err:
        parse_log += f"- Error: unable to obtain metadata for DOI {publication_doi} \n"
        parse_log += f"`{err}`\n"

parse_log += "\n"

# Title
parse_log += "**Title**\n"

title = data["-> title"].strip()

if title == "_No response_":
    try:
        title = publication_record['name']
        parse_log += "_Title taken from associated publication_ \n"
    except:
        parse_log += "- Error: no title found \n"

parse_log += title + "\n \n"

# Description
parse_log += "**Description**\n"

description = data["-> description"].strip()

if description == "_No response_":
    try:
        description = publication_record['abstract']
        parse_log += "_Description taken from associated publication abstract_ \n"
    except:
        parse_log += "- Error: no descrition found, nor abstract for associated publication \n"

parse_log += description + "\n \n"


# Identify authors
parse_log += "**Model authors**\n"

authors = data['-> model authors'].strip().split('\r\n')

if authors[0] == "_No response_":
    try:
        author_list = publication_record['author']
        parse_log += "_Author list taken from associated publication_ \n"
    except:
        parse_log += "- Error: no authors found \n"
else:
    author_list, log = get_authors(authors)
    parse_log += log

parse_log += "\n"
parse_log += "The following author(s) were found successfully:\n"
for author in author_list:
    if "@id" in author:
        parse_log += f"- {author['givenName']} {author['familyName']} ({author['@id']})\n"
    else:
        parse_log += f"- {author['givenName']} {author['familyName']}\n"
parse_log += "\n"


# Scientific Keywords
parse_log += "**Scientific keywords**\n"

keywords = data["-> scientific keywords"].strip().split(", ")
for keyword in keywords:
    parse_log += f"- {keyword} \n"

parse_log += "\n" 


# Identify funders
parse_log += "**Funder**\n"

funders = data["-> funder"].strip().split("\r\n")

if funders[0] == "_No response_":
    try:
        funder_list = publication_record['funder']
        parse_log += "_Funder list taken from associated publication_ \n"
    except:
        parse_log += "- Warning: No funders provided or found in publication. \n"
else:
    funder_list, log = get_funders(funders)
    parse_log += log

parse_log += "\n"
parse_log += "The following funder(s) were found successfully:\n"
for funder in funder_list:
    parse_log += f"- {funder['name']} \n"
parse_log += "\n"

#############
# Section 2
#############

#############
# Section 3
#############

#############
# Section 4
#############

# Landing page image and caption
parse_log += "**Landing page image**\n"

img_string = data["-> add landing page image and caption"].strip()

if img_string == "_No response_":
    parse_log += "No image uploaded.\n"
else:
    landing_image_record, log = parse_image_and_caption(img_string)
    parse_log += f"Filename: {landing_image_record['filename']}\n"
    parse_log += f"Caption: {landing_image_record['caption']}"


# Animation
parse_log += "**Animation**\n"

img_string = data["-> add an animation (if relevant)"].strip()

if img_string == "_No response_":
    parse_log += "No image uploaded.\n"
else:
    animation_record, log = parse_image_and_caption(img_string)
    parse_log += f"Filename: {animation_record['filename']}\n"
    parse_log += f"Caption: {animation_record['caption']}"


# Graphic abstract
parse_log += "**Graphic abstract**\n"

img_string = data["-> add a graphic abstract figure (if relevant)"].strip()

if img_string == "_No response_":
    parse_log += "No image uploaded.\n"
else:
    graphic_abstract_record, log = parse_image_and_caption(img_string)
    parse_log += f"Filename: {graphic_abstract_record['filename']}\n"
    parse_log += f"Caption: {graphic_abstract_record['caption']}"


# Model setup figure
parse_log += "**Model setup figure**\n"

img_string = data["-> add a model setup figure (if relevant)"].strip()

if img_string == "_No response_":
    parse_log += "No image uploaded.\n"
else:
    model_setup_fig_record, log = parse_image_and_caption(img_string)
    parse_log += f"Filename: {model_setup_fig_record['filename']}\n"
    parse_log += f"Caption: {model_setup_fig_record['caption']}"

# Model setup description
parse_log += "**Model setup description**\n"

model_description = data["-> add a description of your model setup"].strip()
parse_log += model_description


parse_log += "\n"
parse_log += "When you have finished adding file descriptions and fixing any identified errors, please add a 'Review Requested' label to this issue."

issue.create_comment(parse_log)