import os
import re
import filetype
from filetypes import Svg
import requests
from github import Github, Auth

token = os.environ.get("GITHUB_TOKEN")
issue_number = int(os.environ.get("ISSUE_NUMBER"))
model_owner = os.environ.get("OWNER")
model_repo_name = os.environ.get("REPO")

# Get issue
auth = Auth.Token(token)
g = Github(auth=auth)
primary_repo = g.get_repo('hvidy/PIPE-4002-EarthByte-ModelAtlas')
issue = primary_repo.get_issue(number = issue_number)

# Get model repo
model_repo = g.get_repo(f"{model_owner}/{model_repo_name}")


regex = r"\[(?P<filename>.*?)\]\((?P<url>.*?)\)"
file_matches = re.findall(regex, issue.body)

# Ensure SVG files can be recognised
filetype.add_type(Svg())

filenames = []
# Download files and move them to the correct location in the repo
for filename, url in file_matches:
	response = requests.get(url)

	# Image file extensions are left out, infer what they should be
	if response.headers.get('Content-Type')[0:5] == 'image':
		filename += '.'+filetype.get_type(mime=response.headers.get('Content-Type')).extension

	model_repo.create_file("website_files/"+filename,"add "+filename,response.content)
	# parse_log += filename + " | \n"
	# filenames.append(filename)