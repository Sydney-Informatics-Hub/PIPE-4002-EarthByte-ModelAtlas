import os
import re
from habanero import Crossref
import orcid
import requests

base_urls = {
    "publication": "https://api.crossref.org/works/",
    "software": "https://zenodo.org/api/records/",
    "organization": "https://api.ror.org/organizations/",
    "author": "https://pub.orcid.org/v3.0/"
}

def get_record(record_type,record_id):
	log = ""
	metadata = {}

    assert (record_type in ["publication","software","organization","author"]), f"Record type `{record_type}` not supported"

    url = base_urls[record_type] + record_id
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse JSON response
        metadata = response.json()

    except requests.exceptions.RequestException as e:
        log += f"- Error fetching metadata: {e} \n"

    return metadata, log

def parse_author(metadata):
    log = ""
    author_record = {}
    
    try:
        author_record = {
            "@type": "Person",
            "@id": metadata["orcid-identifier"]["uri"],
            "givenName": metadata['person']['name']['given-names']['value'],
			"familyName": metadata['person']['name']['family-name']['value'],
        }
        
        affiliation_list = []
        for affiliation in metadata["activities-summary"]["employments"]["affiliation-group"]:
            summary = affiliation["summaries"][0]["employment-summary"]
            if summary["end-date"] is None:
                affiliation_list.append({"@type": "Organization", "name": summary["organization"]["name"]})

        if affiliation_list:
            author_record["affiliation"] = affiliation_list

    except Exception as err:
        log += "- Error: unable to parse author metadata. \n"
        log += f"`{err}`\n"

    return author_record, log

def parse_organization(metadata):
    log = ""
    org_record = {}

    try:
       org_record = {
           "@type": "Organization",
           "@id": metadata["id"],
           "name": metadata["name"],
       }

    except Exception as err:
        log += "- Error: unable to parse organization metadata. \n"
        log += f"`{err}`\n"

    return org_record, log


def parse_software(metadata):
    log = ""
    software_record = {}

    try:
        software_record = {
            "@type": "SoftwareApplication", # and/or SoftwareSourceCode?
            "@id": metadata["doi_url"],
            "name": metadata["title"],
            "softwareVersion": metadata["metadata"]["version"]
            # Other keywords to be corsswalked
        }

    except Exception as err:
        log += "- Error: unable to parse software metadata. \n"
        log += f"`{err}`\n"

    return software_record, log

def parse_publication(metadata):
    log = ""
    publication_record = {}

    metadata = metadata['message']

    try:
        publication_record = {
            "@type": "ScholarlyArticle",
            "@id": metadata["URL"],
            "isPartOf": {
                "@type": "PublicationIssue",
                "issueNumber": metadata["issue"],
                "datePublished": '-'.join(map(str,metadata["published"]["date-parts"][0])),
                "isPartOf": {
                    "@type": [
                        "PublicationVolume",
                        "Periodical"
                    ],
                    "name": metadata["container-title"],
                    "issn": metadata["ISSN"],
                    "volumeNumber": metadata["volume"],
                    "publisher": metadata["publisher"]
                },
            },
            "name": metadata["title"][0],
        }

        author_list = []

        for author in metadata["author"]:
            author_record = {"@type": "Person"}
            if "ORCID" in author:
                author_record["@id"] = author["ORCID"]
            author_record["givenName"] = author["given"]
            author_record["familyName"] = author["family"]
    
            affiliation_list = []
            for affiliation in author["affiliation"]:
                affiliation_list.append({"@type": "Organization", "name": affiliation["name"]})
                
            if affiliation_list:
                author_record["affiliation"] = affiliation_list
    
            author_list.append(author_record)

        if author_list:
            publication_record["author"] = author_list

        if "abstract" in metadata:
            publication_record["abstract"] = metadata["abstract"].split('<jats:p>')[1].split('</jats:p>')[0]
    
        if "page" in metadata:
            publication_record["pagination"] = metadata["page"]
    
        if "alternative-id" in metadata:
            publication_record["identifier"] = metadata["alternative-id"]
    
        if "funder" in metadata:
            funder_list = []
            for funder in metadata["funder"]:
                funder_list.append({"@type": "Organization", "name": funder["name"]})
            publication_record["funder"] = funder_list

    except Exception as err:
        log += "- Error: unable to parse publication metadata. \n"
        log += f"`{err}`\n"

    return publication_record, log


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
		"name": output["title"][0],
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
				log += f"- Error: author name `{author}` in unexpected format. Expected `last name(s), first name(s)`. \n"

	return authors, log