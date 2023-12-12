import os
import re
import filetype
import requests
import subprocess
from github import Github, Auth

from metadata_utils import get_crossref_article, get_authors

token = os.environ.get("GITHUB_TOKEN")
issue_number = int(os.environ.get("ISSUE_NUMBER"))

parse_log = "Thank you for submitting. Please check the output below, and fix any errors, etc.\n\n"

# Get issue
auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo("hvidy/PIPE-4002-EarthByte-ModelAtlas")
issue = repo.get_issue(number = issue_number)


# Verify repo name can be created
parse_log += "**Model Repository**\n"

os.environ['ISSUE_NAME'] = issue.title
cmd = "python3 .github/scripts/generate_identifier.py"
try:
	slug = subprocess.check_output(cmd, shell=True, text=True, stderr=open(os.devnull)).strip()
	parse_log += f"Model repo will try be created with name `{slug}` \n"
except Exception as err:
	parse_log += "- Unable to create valid repo name... \n"
	parse_log += f"`{err}`\n"

parse_log += "\n"

# Parse issue body
# Identify headings and subsequent text
regex = r"### *(?P<key>.*?)\s*[\r\n]+(?P<value>[\s\S]*?)(?=###|$)"

data = dict(re.findall(regex, issue.body))

# Associated Publication
parse_log += "**Associated Publication**\n"

publication = data["Associated Publication DOI"].strip()

if publication == "_No response_":
	parse_log += "No DOI provided. \n"
else:
	try:
		publication_metadata = get_crossref_article(publication)
		parse_log += f"Found publication _{publication_metadata['name']}_. \n"

		author_list = publication_metadata["author"]
		if "funder" in publication_metadata:
			funder_list = publication_metadata["funder"]
		if "abstract" in publication_metadata:
			abstract = publication_metadata["abstract"]

	except Exception as err:
		parse_log += f"- Error: unable to obtain metadata for DOI {publication} \n"
		parse_log += f"`{err}`\n"

parse_log += "\n"


# Identify authors
parse_log += "**Author(s)**\n"

authors = data['Author(s)'].strip().split('\r\n')

if authors[0] == "_No response_":
	if author_list in locals():
		parse_log += "_Author list taken from associated publication_"
	else:
		parse_log += "- Error: no authors found"
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