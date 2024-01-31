import requests

def copy_files(repo, directory, issue_dict):
	file_keys = ["landing_image", "animation", "graphic_abstract", "model_setup_figure"]

	for file_key in file_keys:
		if file_key in issue_dict:
			response = requests.get(issue_dict[file_key]["url"])
			repo.create_file(directory+issue_dict[file_key]["filename"], "add "+issue_dict[file_key]["filename"], response.content)
