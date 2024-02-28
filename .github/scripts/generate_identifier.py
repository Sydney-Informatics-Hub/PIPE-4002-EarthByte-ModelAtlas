import json
import subprocess
import os
import re
from github import Github, Auth

def run_command_check_output(cmd):
	return subprocess.check_output(cmd, shell=True, stderr=open(os.devnull))

def encode(name, i):
	result_str = name
	if i > 0:
		result_str += "_"+str(i)
	return result_str


def exists(model_id):
	cmd = "curl https://api.github.com/repos/hvidy/{0}".format(model_id)
	output = json.loads(run_command_check_output(cmd))

	if "message" in output:
		if output["message"] == "Not Found":
			return False
		else:
			return True
	else:
		return True

def choice(name):
	i = 0
	while True:
		model_id = encode(name, i)
		if not exists(model_id):
			return model_id
		i += 1


if __name__ == "__main__":
	token = os.environ.get("GITHUB_TOKEN")
	issue_number = int(os.environ.get("ISSUE_NUMBER"))

	# Get issue
	auth = Auth.Token(token)
	g = Github(auth=auth)
	repo = g.get_repo("hvidy/PIPE-4002-EarthByte-ModelAtlas")
	issue = repo.get_issue(number = issue_number)

	# Parse issue body
	# Identify headings and subsequent text
	regex = r"### *(?P<key>.*?)\s*[\r\n]+(?P<value>[\s\S]*?)(?=###|$)"
	data = dict(re.findall(regex, issue.body))

	slug = data["-> slug"].strip()
	print(choice(slug))