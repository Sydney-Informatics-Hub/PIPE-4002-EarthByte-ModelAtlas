import json
from ro_crate_utils import *
from crosswalk_mappings import *

def dict_to_report(issue_dict):

    #############
    # Section 1
    #############
    report = "## Section 1: Summary of your model \n"
    # creator/contributor
    report += "**Creator/Contributor**\n"
    report += f"Creator/contributor is {issue_dict['creator']['givenName']} {issue_dict['creator']['familyName']} "
    if "@id" in issue_dict['creator']:
        report += f"([{issue_dict['creator']['@id'].split('/')[-1]}]({issue_dict['creator']['@id']}))"
    report += "\n\n"

    # slug
    report += "**Model Repository Slug**\n"
    report += f"Model repo will be created with name `{issue_dict['slug']}` \n\n"

    # FoR codes
    report += "**Field of Research (FoR) Codes**\n"
    for for_code in issue_dict["for_codes"]:
        report += f"- `{for_code['@id']}`: {for_code['name']} \n"
    report += "\n"

    # license
    report += "**License**\n"
    if "url" in issue_dict["license"]:
        report += f"[{issue_dict['license']['name']}]({issue_dict['license']['url']})\n\n"
    else:
        report += f"{issue_dict['license']['name']}\n\n"

    # model category
    report += "**Model Category**\n"
    for category in issue_dict["model_category"]:
        report += f"- {category} \n"
    report += "\n"

    # associated publication DOI
    if "@id" in issue_dict["publication"]:
        report += "**Associated Publication**\n"
        report += f"Found publication: _[{issue_dict['publication']['name']}]({issue_dict['publication']['@id']})_ \n\n"

    # title
    report += "**Title**\n"
    report += issue_dict["title"] + "\n\n"

    # description
    report += "**Description**\n"
    report += issue_dict["description"] + "\n\n"

    # model authors
    report += "**Model Authors**\n"
    for author in issue_dict["authors"]:
        report += f"- {author['givenName']} {author['familyName']} "
        if "@id" in author:
            report += f"([{author['@id'].split('/')[-1]}]({author['@id']}))"
        report += "\n"
    report += "\n"

    # scientific keywords
    if issue_dict["keywords"]:
        report += "**Scientific Keywords**\n"
        for keyword in issue_dict["keywords"]:
            report += f"- {keyword} \n"
        report += "\n"

    # funder
    report += "**Funder**\n"
    for funder in issue_dict["funder"]:
        report += f"- {funder['name']} "
        if "@id" in funder:
            report += f"({funder['@id']})"
        elif "url" in funder:
            report += f"({funder['url']})"
        report += "\n"
    report += "\n"


    #############
    # Section 2
    #############
    report += "## Section 2: your model code, output data \n"
    # include model code
    if "include_model_code" in issue_dict:
        report += "**Include model code?** \n"
        report += f"{str(issue_dict['include_model_code'])} \n\n"

    # model code URI/DOI
    if "model_code_uri" in issue_dict:
        report += "**Model code URI/DOI** \n"
        report += f"{issue_dict['model_code_uri']} \n\n"

    # include model output data
    if "include_model_output" in issue_dict:
        report += "**Include model output data?** \n"
        report += f"{str(issue_dict['include_model_output'])} \n\n"

    # model output URI/DOI
    if "model_output_uri" in issue_dict:
        report += "**Model output URI/DOI** \n"
        report += f"{issue_dict['model_output_uri']} \n\n"

    #############
    # Section 3
    #############
    report += "## Section 3: software framework and compute details \n"
    # software framework DOI/URI
    if "@id" in issue_dict["software"]:
        report += "**Software Framework DOI/URI**\n"
        report += f"Found software: _[{issue_dict['software']['name']}]({issue_dict['software']['@id']})_ \n\n"

    # software framework source repository
    if "codeRepository" in issue_dict["software"]:
        report += "**Software Repository** \n"
        report += f"{issue_dict['software']['codeRepository']} \n\n"

    # name of primary software framework
    if "name" in issue_dict["software"]:
        report += "**Name of primary software framework**\n"
        report += f"{issue_dict['software']['name']} \n\n"

    # software framework authors
    if "author" in issue_dict["software"]:
        report += "**Software framework authors**\n"
        for author in issue_dict["software"]["author"]:
            if "givenName" in author:
                report += f"- {author['givenName']} {author['familyName']} "
            elif "name" in author:
                report += f"- {author['name']} "
            if "@id" in author:
                report += f"([{author['@id'].split('/')[-1]}]({author['@id']}))"
            report += "\n"
        report += "\n"

    # software & algorithm keywords
    if "keywords" in issue_dict["software"]:
        report += "**Software & algorithm keywords**\n"
        for keyword in issue_dict["software"]["keywords"]:
            report += f"- {keyword} \n"
        report += "\n"

    # computer URI/DOI
    if "computer_uri" in issue_dict:
        report += "**Computer URI/DOI** \n"
        report += f"{issue_dict['computer_uri']} \n\n"

    #############
    # Section 4
    #############
    report += "## Section 4: web material (for mate.science) \n"
    # landing page image and caption
    if "landing_image" in issue_dict:
        report += "**Landing page image**\n"
        if "filename" in issue_dict["landing_image"]:
            report += f"Filename: [{issue_dict['landing_image']['filename']}]({issue_dict['landing_image']['url']})\n"
        if "caption" in issue_dict["landing_image"]:
            report += f"Caption: {issue_dict['landing_image']['caption']}\n"
        report += '\n'

    # animation
    if "animation" in issue_dict:
        report += "**Animation**\n"
        if "filename" in issue_dict["animation"]:
            report += f"Filename: [{issue_dict['animation']['filename']}]({issue_dict['animation']['url']})\n"
        if "caption" in issue_dict["animation"]:
            report += f"Caption: {issue_dict['animation']['caption']}\n"
        report += '\n'

    # graphic abstract
    if "graphic_abstract" in issue_dict:
        report += "**Graphic abstract**\n"
        if "filename" in issue_dict["graphic_abstract"]:
            report += f"Filename: [{issue_dict['graphic_abstract']['filename']}]({issue_dict['graphic_abstract']['url']})\n"
        if "caption" in issue_dict["graphic_abstract"]:
            report += f"Caption: {issue_dict['graphic_abstract']['caption']}\n"
        report += '\n'

    # model setup figure
    if "model_setup_figure" in issue_dict:
        report += "**Model setup figure**\n"
        if "filename" in issue_dict["model_setup_figure"]:
            report += f"Filename: [{issue_dict['model_setup_figure']['filename']}]({issue_dict['model_setup_figure']['url']})\n"
        if "caption" in issue_dict["model_setup_figure"]:
            report += f"Caption: {issue_dict['model_setup_figure']['caption']}\n"
        report += '\n'

    # description
    if "model_setup_description" in issue_dict:
        report += "**Model setup description**\n"
        report += f"{issue_dict['model_setup_description']}\n\n"

    report += "\n ** Dumping dictionary during testing **\n"
    report += str(issue_dict)

    return report
    

def dict_to_metadata(issue_dict, mapping_list=default_issue_entity_mapping_list, filter_entities=True, flat_compact_crate=True):
    
    """
    Converts an issue dictionary into a standardized metadata format using Research Object Crate (RO-Crate) structure,
    applying entity simplification and mappings based on predefined templates and rules.

    The function performs several key operations:
    - Filters and simplifies entities within the issue dictionary based on a specified template if `filter_entities` is True.
    - Loads a base RO-Crate template and applies direct mappings from the issue dictionary to the RO-Crate structure using `mapping_list`.
    - Allows for custom modifications to the RO-Crate based on specific data within the issue dictionary.
    - Optionally flattens the RO-Crate structure for a more compact representation if `flat_compact_crate` is True.

    Parameters:
    - issue_dict (dict): The issue dictionary containing data that needs to be converted into metadata.
    - mapping_list (list): A list of mappings that define how elements in the issue dictionary correspond to elements in the RO-Crate structure.
    - filter_entities (bool, optional): If True, simplifies entities in the issue dictionary using predefined templates. Defaults to True.
    - flat_compact_crate (bool, optional): If True, flattens the RO-Crate structure to bring nested entities to the top level. Defaults to True.

    Returns:
    - str: A JSON string representing the metadata in the RO-Crate format.

    Note:
    The function relies on external functions to load entity templates, apply mappings, and customize the RO-Crate. These functions need to be defined separately.
    """
    
    
    #this takes the issue_dict and simplifies entities (e.g. @Type=Person) using templates defined at:
    #https://github.com/ModelAtlasofTheEarth/metadata_schema/blob/main/mate_ro_crate/type_templates.json
    if filter_entities is True:
        entity_template = load_entity_template()
        recursively_filter_key(issue_dict, entity_template)
    
    #load the RO-Crate template
    ro_crate = load_crate_template()
    
    #Apply direct mappings between the issue_dict and the RO-Crate
    dict_to_ro_crate_mapping(ro_crate, issue_dict,  mapping_list)
    
    #Add any further direct chnages to the RO-Crate based on issue_dict
    customise_ro_crate(issue_dict, ro_crate)
    
    
    #flatten the crate (brings nested entities to the top level)
    if flat_compact_crate is True:
        flatten_crate(ro_crate)

    metadata_out = json.dumps(ro_crate)

    return metadata_out

def dict_to_yaml(issue_dict):

    #To Do: crosswalk issue dictionary to yaml format for mate.science

    metadata = json.dumps(issue_dict)

    return metadata
