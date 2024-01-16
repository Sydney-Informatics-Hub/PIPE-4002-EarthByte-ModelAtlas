import re
import json

from metadata_utils import get_record, parse_author, is_orcid_format

def parse_name_or_orcid(name_or_orcid):
    error_log = ""

    if is_orcid_format(name_or_orcid):
        orcid_record, log1 = get_record("author", name_or_orcid)
        creator_record, log2 = parse_author(orcid_record)
        if log1 or log2:
            error_log += log1 + log2
    else:
        try:
            familyName, givenName = name_or_orcid.split(",")
            creator_record = {
                "@type": "Person",
                "givenName": givenName,
                "familyName": familyName,
            }
        except:
            error_log += f"- Error: name `{name_or_orcid}` in unexpected format. Expected `last name(s), first name(s)` or ORCID. \n"

    return creator_record, error_log

def parse_issue(issue):
    error_log = ""

    # Parse issue body
    # Identify headings and subsequent text
    regex = r"### *(?P<key>.*?)\s*[\r\n]+(?P<value>[\s\S]*?)(?=###|$)"
    data = dict(re.findall(regex, issue.body))

    data_dict = {}

    #############
    # Section 1
    #############
    # creator/contributor
    creator = data["-> creator/contributor ORCID (or name)"].strip()
    creator_record, log = parse_name_or_orcid(creator)
    data_dict["creator"] = creator_record
    if log:
        error_log += "**Creator/Contributor**\n" + log +"\n"

    # slug

    # FoR codes

    # license

    # model category

    # associated publication DOI

    # title

    # description

    # model authors

    # scientific keywords

    # funder


    #############
    # Section 2
    #############
    # include model code

    # model code URI/DOI

    # include model output data

    # model output URI/DOI


    #############
    # Section 3
    #############
    # software framework DOI/URI

    # software framework source repository

    # name of primary software framework

    # software framework authors

    # software & algorithm keywords

    # computer URI/DOI


    #############
    # Section 4
    #############
    # landing page image and caption

    # animation

    # graphic abstract

    # model setup figure

    # description



    return data, error_log

def dict_to_report(issue_dict):

    report = str(issue_dict)

    return report

def dict_to_metadata(issue_dict):

    metadata = json.dumps(issue_dict)

    return metadata