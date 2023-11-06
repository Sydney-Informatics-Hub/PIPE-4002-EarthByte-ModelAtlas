import os
from github import Github, Auth

token = os.environ.get("GITHUB_TOKEN")
issue_number = os.environ.get("ISSUE_NUMBER")

print("ISSUE_NUMBER:", issue_number)

auth = Auth.Token(token)

g = Github(auth=auth)

repo = g.get_repo('Sydney-Informatics-Hub/PIPE-4002-EarthByte-ModelAtlas')

print(repo.name)

issue = repo.get_issue(number = issue_number)

print(issue.body)