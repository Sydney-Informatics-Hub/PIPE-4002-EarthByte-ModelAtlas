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
        log += "Error: unable to parse author metadata. \n"
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
        log += "Error: unable to parse organization metadata. \n"
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
            # Other keywords to be crosswalked
        }

        author_list = []

        for author in metadata["metadata"]["creators"]:
            author_record = {"@type": "Person"}
            if "orcid" in author:
                author_record["@id"] = author["orcid"]
            if "givenName" in author:
                author_record["givenName"] = author["given"]
                author_record["familyName"] = author["family"]
            elif "name" in author:
                author_record["name"] = author["name"]
            if "affiliation" in author:
                author_record["affiliation"] = author["affiliation"]
    
            author_list.append(author_record)

        if author_list:
            software_record["author"] = author_list


    except Exception as err:
        log += "Error: unable to parse software metadata. \n"
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
            "name": metadata["title"][0],
            }

        if "issue" in metadata:
            publication_issue = {
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

            publication_record["isPartOf"] = publication_issue
        else:
            if metadata["published"]:
                publication_record["datePublished"] = '-'.join(map(str,metadata["published"]["date-parts"][0]))
            if metadata["publisher"]:
                publication_record["publisher"] = metadata["publisher"]

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
        log += "Error: unable to parse publication metadata. \n"
        log += f"`{err}`\n"

    return publication_record, log


