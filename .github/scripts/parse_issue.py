import os
import re
import filetype
import requests
import subprocess
from github import Github, Auth

from metadata_utils import get_crossref_article, get_authors, is_orcid_format, get_record, parse_author, parse_publication

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
os.environ['ISSUE_NAME'] = proposed_slug
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
# TBD

# License
# TBD

# Model category
# TBD

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
        title = publication_record['abstract']
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
# TBD

# Identify funders
parse_log += "**Funder**\n"

funders = data['-> funder'].strip().split('\r\n')

if funders[0] == "_No response_":
    try:
        funders = publication_record['funder']
        parse_log += "_Funder list taken from associated publication_ \n"
    except:
        parse_log += "- Warning: No funders provided or found in publication. \n"
else:
    print("Still need to code this bit")
    funders = []
    # for funder in funders:
    #   funder_list.append({"@type": "Organization", "name": funder})

parse_log += "\n"
parse_log += "The following funder(s) were found successfully:\n"
for funder in funders:
    parse_log += f"- {funder['name']} \n"
parse_log += "\n"


# Identify uploaded files
parse_log += "**File Manifest**\n"
parse_log += "The files listed in the table below require descriptions. Please edit this comment to insert them into the table. \n"
parse_log += "\n"
parse_log += "Filename | File Description \n"
parse_log += "---|--- \n"

regex = r"\[(?P<filename>.*?)\]\((?P<url>.*?)\)"
file_matches = re.findall(regex, issue.body)

# Hack to recognise SVG files
# Need to tidy this up, and are there any other files that filetype doesn't natively recognise?
class Svg(filetype.Type):
    MIME = 'image/svg+xml'
    EXTENSION = 'svg'

    def __init__(self):
        super(Svg, self).__init__(
            mime = Svg.MIME,
            extension = Svg.EXTENSION
            )

    def match(self, buf):
        return False

filetype.add_type(Svg())

filenames = []
# Download files and move them to the correct location in the repo
for filename, url in file_matches:
    response = requests.get(url)

    # Image file extensions are left out, infer what they should be
    if response.headers.get('Content-Type')[0:5] == 'image':
        filename += '.'+filetype.get_type(mime=response.headers.get('Content-Type')).extension

    # repo.create_file("pages/models/"+slug+"/"+filename,"add "+filename,response.content)
    parse_log += filename + " | \n"
    filenames.append(filename)

# Test making a comment - could this be edited later for the uploader to give file descriptions?

parse_log += "\n"
parse_log += "When you have finished adding file descriptions and fixing any identified errors, please add a 'Review Requested' label to this issue."

issue.create_comment(parse_log)

print(issue.body)