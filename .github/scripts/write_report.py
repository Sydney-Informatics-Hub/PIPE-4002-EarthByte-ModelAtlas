import os
from github import Github, Auth
from parse_issue import parse_issue
from crosswalks import dict_to_report

# Environment variables
token = os.environ.get("GITHUB_TOKEN")
issue_number = int(os.environ.get("ISSUE_NUMBER"))

# Get issue
auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo("hvidy/PIPE-4002-EarthByte-ModelAtlas")
issue = repo.get_issue(number = issue_number)

# Parse issue
data, error_log = parse_issue(issue)

# Write report
report = "Thank you for submitting. Please check the output below, and fix any errors, etc.\n\n"

report += "# Errors and Warnings \n"
report += error_log + "\n\n"

report += "# Parsed data \n"
report += dict_to_report(data)

# Post report to issue as a comment
issue.create_comment(report)