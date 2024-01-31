import os
from github import Github, Auth
from parse_issue import parse_issue
from crosswalks import dict_to_metadata
from copy_files import copy_files

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

#FOR TESTING - print out dictionary as a comment
issue.create_comment("# M@TE crate \n"+str(metadata))

# Move files to repo
model_repo.create_file(".metadata/mate.json","add mate.json",metadata)

# Copy web material to repo
copy_files(model_repo, "website_files/", data)

# Report creation of repository
issue.create_comment(f"Model repository created at https://github.com/{model_owner}/{model_repo_name}")