import os
import re
import filetype
import requests
from github import Github, Auth

token = os.environ.get("GITHUB_TOKEN")
issue_number = int(os.environ.get("ISSUE_NUMBER"))

# Get issue
auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo('Sydney-Informatics-Hub/PIPE-4002-EarthByte-ModelAtlas')
issue = repo.get_issue(number = issue_number)

# Generate slug
slug = re.search(r"\<(?P<title>.*?)\>", issue.title).group('title').replace(" ","_")

# Parse issue body
# Identify headings and subsequent text
regex = r"### *(?P<key>.*?)\s*[\r\n]+(?P<value>[\s\S]*?)(?=###|$)"

data = dict(re.findall(regex, issue.body))


# Identify uploaded files
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

	repo.create_file("pages/models/"+slug+"/"+filename,"add "+filename,response.content)
	filenames.append(filename)

# Test making a comment - could this be edited later for the uploader to give file descriptions?
issue.create_comment(str(filenames))

print(issue.body)

