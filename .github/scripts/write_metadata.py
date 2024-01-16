import os
from github import Github, Auth
from parse_utils import parse_issue, dict_to_metadata

# Environment variables
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

# Parse issue
data, error_log = parse_issue(issue)

# Convert dictionary to metadata json
metadata = dict_to_metadata(data)

# Move files to repo
model_repo.create_file(".metadata/mate.json","add mate.json",metadata)

# Report creation of repository
issue.create_comment(f"Model repository created at https://github.com/{model_owner}/{model_repo_name}")