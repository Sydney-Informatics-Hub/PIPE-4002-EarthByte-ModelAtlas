import os
import re
from habanero import Crossref
import orcid

def get_crossref_article(doi):
	'''
	Returns metadata from Crossref for a given doi

		Parameters:
			doi (string): Digital Object Identifier of a publication

		Returns:
			metadata (dict): dictionary of publication metadata

	'''

	cr = Crossref()

	output = cr.works(ids = doi)["message"]

	metadata = {
		"@type": "ScholarlyArticle",
		"isPartOf": {
			"@type": "PublicationIssue",
			"issueNumber": output["issue"],
			"datePublished": '-'.join(map(str,output["published"]["date-parts"][0])),
			"isPartOf": {
				"@type": [
					"PublicationVolume",
					"Periodical"
				],
				"name": output["container-title"],
				"issn": output["ISSN"],
				"volumeNumber": output["volume"],
				"publisher": output["publisher"]
			},
		},
		"sameAs": doi,
		"name": output["title"],
	}

	author_list = []

	for author in output["author"]:
		author_record = {"@type": "Person"}
		if "ORCID" in author:
			author_record["@id"] = author["ORCID"]
		author_record["givenName"] = author["given"]
		author_record["familyName"] = author["family"]

		affiliation_list = []
		for affiliation in author["affiliation"]:
			affiliation_list.append({"@type": "Organization", "name": affiliation["name"]})

		author_record["affiliation"] = affiliation_list

		author_list.append(author_record)

	metadata["author"] = author_list

	if "abstract" in output:
		metadata["abstract"] = output["abstract"]

	if "page" in output:
		metadata["pagination"] = output["page"]

	if "alternative-id" in output:
		metadata["identifier"] = output["alternative-id"]

	if "funder" in output:
		funder_list = []
		for funder in output["funder"]:
			funder_list.append({"@type": "Organization", "name": funder["name"]})
		metadata["funder"] = funder_list


	return metadata

def get_authors(author_list):
	'''
	Parses a list of author names or ORCID iDs and returns a list of dictionaries of schema.org Person type

		Parameters:
			author_list (list of strings): list of names in format Last Name(s), First Name(s) and/or ORCID iDs

		Returns:
			authors (list of dicts)
			log (string)

	'''

	log = ""

	orcid_id = os.environ.get("ORCID_ID")
	orcid_pw = os.environ.get("ORCID_PW")

	orcid_pattern = re.compile(r'\d{4}-\d{4}-\d{4}-\d{3}[0-9X]')
	name_pattern = re.compile(r'([\w\.\-\u00C0-\u017F]+(?: [\w\.\-\u00C0-\u017F]+)*), ([\w\.\-\u00C0-\u017F]+(?: [\w\.\-\u00C0-\u017F]+)*)')

	api = orcid.PublicAPI(orcid_id, orcid_pw, sandbox=False)
	search_token = api.get_search_token_from_orcid()

	authors = []

	for author in author_list:
		if orcid_pattern.fullmatch(author):
			try:
				record = api.read_record_public(author, 'record', search_token)
				author_record = {
					"@type": "Person",
					"@id": record['orcid-identifier']['path'],
					"givenName": record['person']['name']['given-names']['value'],
					"familyName": record['person']['name']['family-name']['value'],
					}
				authors.append(author_record)
			except Exception as err:
				log += "- Error: unable to find ORCID iD. Check you have entered it correctly. \n"
				log += f"`{err}`\n"
		else:
			try:
				familyName, givenName = author.split(",")
				author_record = {
					"@type": "Person",
					"givenName": givenName,
					"familyName": familyName,
				}
				authors.append(author_record)
			except:
				log += f"- Error: author name `{author}` in unexpected format. Excpected `last name(s), first name(s)`. \n"

	return authors, log