import requests
import string
import json

def recursively_filter_key(obj, entity_template):
    
    """
    Recursively filters keys in a nested data structure (dictionaries, lists, tuples) 
    based on a specified entity template. The function retains keys in each dictionary 
    that match a set of allowed keys defined for the dictionary's '@type' in the entity 
    template. Other keys are removed.

    Parameters:
    obj (dict | list | tuple): The nested data structure to be filtered. It can be a 
                               dictionary, a list, a tuple, or a combination of these.
    entity_template (dict): A dictionary defining which keys to retain for each '@type' 
                            in the nested dictionaries. The keys in this dictionary are 
                            '@type' values, and the values are lists of keys to retain 
                            in the dictionaries that have the corresponding '@type'.

    Returns:
    None: The function modifies the input object (obj) in place and does not return a value.


    Note:
    The function modifies the 'obj' argument in place. After execution, 'obj' will only 
    contain the keys allowed by the 'entity_template' for each dictionary's '@type'. 
    Elements of lists and tuples within 'obj' are also recursively filtered.
    """
    
    if isinstance(obj, dict):
        if '@type' in obj.keys():
            if obj['@type'] in entity_template.keys():
                #these are the keys we want to filter on
                type_keys = entity_template[obj['@type']]
                [obj.pop(k) for k in list(obj.keys()) if k not in type_keys]

            pass
        for key, value in obj.items():
            recursively_filter_key(value, entity_template)
            
    # If it's a list or a tuple, iterate over its elements
    elif isinstance(obj, (list, tuple)):
        for index, value in enumerate(obj):
            recursively_filter_key(value, entity_template)
    


def get_random_string(length=9):
    """
    Generates a random string of characters, with a hash prepended,
    """
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    result_str = '#' + result_str
    return result_str 


def check_for_id(json_dict):
    """
    Checks if the @id key exists in a json_dict (a Python dictionary)
    """
    if '@id' in json_dict.keys():
        return True
    else:
        return False
    
    
def top_level_id(crate):
    
    """
    Gets a list of @id values for the top level of teh @graph array
    """
    id_list = []
    for json_dict in crate['@graph']:
        id_list.append(json_dict['@id'])
        
    return id_list    

def is_array(var):
    return isinstance(var, (list, tuple))

def replace_blank_null_id(entity):

    """
    Fills blank '@id' key in an RO-Crate entity dictionary.

    This function examines an RO-Crate entity, represented as a dictionary, 
    for the presence and value of the '@id' key. 
    If '@id' is absent or its value is None, the function assigns a new value to '@id'. 
    The new value is determined in the following order of preference:
    
    1. If 'uri' key exists in the entity, its value is used.
    2. If 'url' key exists, its value is used.
    3. If neither 'uri' nor 'url' is present, a randomly generated string is assigned.

    Args:
        entity (dict): The dictionary representing an RO-Crate entity.

    Returns:
        dict: The modified entity dictionary with an updated '@id' value.

    Note:
        The function modifies the 'entity' dictionary in-place and also returns it.
    """
    replace_string = get_random_string()
    
    if 'uri' in entity.keys():
        replace_string =entity['uri']
    if 'url' in entity.keys():
        replace_string =entity['url']
    
    #print(entity)
    
    #if not @id is no present or or is None, make new_id.
    if '@id' not in entity.keys():
        entity.update({'@id': replace_string })
    if '@id' in entity.keys() is True and entity['@id'] is None:
        entity.update({'@id': replace_string })
        
    #return entity

def search_replace_blank_node_ids(crate, graph_index):
    
    """
    This function retrieves a node (entity dictionary) from the '@graph' array of a 
    given RO-Crate object (represented as a python dictionary) using the provided graph_index. 
    It iterates through the values in the entity dictionary. 
    If any of these values are nested json entities (i.e dictionaries), 
    the function verifies whether these nested entities have an '@id' key. 
    If an '@id' key is missing or blank for a nested entity, 
    the function generates and assigns a random '@id' to that entity.

    Args:
        ro_crate (dict): The RO-Crate object, represented as a python dictionary.
        graph_index (int): The index of the entity in the '@graph' array to be extracted.

    Returns:
        None: The function modifies the ro_crate object in-place by adding '@id's to nested entities if required.
    """
    
    #grab the entity out of the crate as a dictionary
    json_dict = crate['@graph'][graph_index]
    #print(json_dict)
    #print(json_dict.keys())
    for key in json_dict.keys():    
        entity = json_dict[key]
        #print(entity)
        if isinstance(entity, dict):
            #print(entity)
            #this should replace in place!
            replace_blank_null_id(entity)
            crate['@graph'][graph_index][key] = entity
                
    
def search_replace_sub_dict(crate, graph_index):
    
    """
    Extracts a nested entity from within an RO-Crate's entity and relocates it to the top level of the 
    '@graph' array. This makes the json flattened and compacted.

    This function takes an RO-Crate object and a specified index, 
    retrieves an entity dictionary (a node in the '@graph' array), and iterates through its values. 
    If it finds any nested entities within this dictionary, it extracts these entities  
    and places them at the top level of the '@graph' array. The original position of the nested entity 
    within the parent entity is then replaced with the nested entity's '@id'.
    

    Args:
        ro_crate (dict): The RO-Crate object, represented as a python dictionary.
        graph_index (int): The index of the entity in the '@graph' array to be examined for nested entities.

    Returns:
        None: The function modifies the ro_crate object in-place, relocating nested entities and updating references.
    """
    
    
    #grab the entity out of the crate as a dictionary
    json_dict = crate['@graph'][graph_index]
    
    for key in json_dict.keys():
        
        
        current_ids = top_level_id(crate)
        if isinstance(json_dict[key], dict):
            try:
                at_id = json_dict[key]['@id']
            except:
                replace_blank_null_id(json_dict[key])
                at_id = json_dict[key]['@id']
            if len(json_dict[key].keys()) > 1:
                if at_id not in current_ids:
                    crate['@graph'].append(json_dict[key])
                    
                #replace local dict with @id
                [json_dict[key].pop(k) for k in list(json_dict[key].keys()) if k != '@id']
        
        #recurse through any lists or tuples and check if they contain sub dictionaries.
        #a true recursive approach is not used here due to difficulties with how the function needs
        #to modfy both the ro-crate and the entity
    
        
        elif is_array(json_dict[key]):
            for j in range(len(json_dict[key])):
                #print(key, j)
                if isinstance(json_dict[key][j], dict):
                    try:
                        at_id = json_dict[key][j]['@id']
                    except:
                        replace_blank_null_id(json_dict[key][j])
                        at_id = json_dict[key][j]['@id']
                    if len(json_dict[key][j].keys()) > 1:                
                        if at_id not in current_ids:
                            crate['@graph'].append(json_dict[key][j])
                    #replace local dict with @id
                    [json_dict[key][j].pop(k) for k in list(json_dict[key][j].keys()) if k != '@id']
            
        else:
            pass



def apply_entity_mapping(metadata, mapping, issue_dict, graph_index):
    
    """
    apply a mapping from the issue dictionary into the entity dictionary stored at the node of the 
    @graph array given by graph_index
    """
    
    for key in mapping.keys():
        if mapping[key] is None:
            pass

        else:
            metadata['@graph'][graph_index][key] = issue_dict[mapping[key]]







def load_crate_template(metadata_template_url="https://raw.githubusercontent.com/ModelAtlasofTheEarth/metadata_schema/main/mate_ro_crate/ro-crate-metadata.json"):
    
    """
    Downloads the M@TE RO-Crate metadata template from a specified URL and returns it as a dictionary.

    Parameters:
    - metadata_template_url (str): URL to the JSON-LD metadata template.

    Returns:
    - dict: The loaded metadata template as a dictionary, or None if an error occurs.
    """
    
    try:
        response = requests.get(metadata_template_url)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        crate = json.loads(response.text)
        print("JSON-LD data loaded successfully.")
        return crate
    except requests.exceptions.RequestException as e:
        print(f"Failed to download the file. Error: {e}")
        return None
    
    

def load_entity_template(entity_template_url="https://raw.githubusercontent.com/ModelAtlasofTheEarth/metadata_schema/main/mate_ro_crate/type_templates.json"):
    """
    Downloads a JSON-LD entity template from the specified URL and returns it as a dictionary.

    Parameters:
    - entity_template_url (str): URL to the JSON-LD entity template.

    Returns:
    - dict: The loaded entity template as a dictionary, or None if an error occurs.
    """
    
    try:
        response = requests.get(entity_template_url)
        response.raise_for_status()  # Raises an HTTPError for bad HTTP responses
        entity_template = json.loads(response.text)
        print("JSON-LD data loaded successfully.")
        return entity_template
    except requests.exceptions.RequestException as e:
        print(f"Failed to download the file. Error: {e}")
        return None
  
