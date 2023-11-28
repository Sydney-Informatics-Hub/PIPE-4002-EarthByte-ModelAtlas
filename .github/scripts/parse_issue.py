import os
import re
import filetype
import requests
import subprocess
from github import Github, Auth

token = os.environ.get("GITHUB_TOKEN")
issue_number = int(os.environ.get("ISSUE_NUMBER"))

parse_log = ""

# Get issue
auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo('hvidy/PIPE-4002-EarthByte-ModelAtlas')
issue = repo.get_issue(number = issue_number)

# Verify repo name can be created
os.environ['ISSUE_NAME'] = issue.title
cmd = "python3 .github/scripts/generate_identifier.py"
try:
	slug = subprocess.check_output(cmd, shell=True, stderr=open(os.devnull))
	parse_log += "Model repo will try be created with name "+slug
except Exception as err:
	parse_log += "Unable to create valid repo name... \n"
	parse_log += f"Unexpected {err=}, {type(err)=}"


# Parse issue body
# Identify headings and subsequent text
regex = r"### *(?P<key>.*?)\s*[\r\n]+(?P<value>[\s\S]*?)(?=###|$)"

data = dict(re.findall(regex, issue.body))


# Identify uploaded files

parse_log += "\n"
parse_log += "**File manifest**\n"
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
	parse_log += filename + "| \n"
	filenames.append(filename)

# Test making a comment - could this be edited later for the uploader to give file descriptions?

parse_log += "\n"
parse_log += "When you have finished adding file descriptions and fixing any identified errors, please add a 'Review Requested' label to this issue."

issue.create_comment(parse_log)

print(issue.body)