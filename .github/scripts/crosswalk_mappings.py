#provides a mapping between keys in metadata and keys in issue dictionary (which are the values in the mapping)
#None value indicate default values or properties which we not attempt to automatically fill 

root_node_mapping = {"@id":None,
            "@type":None,
            "name":"slug",
            "description":"description",
            "creator":"creator",
            "contributors":"authors",
            "citation":"publication",
            "publisher":None,
            "license":"license",
            "keywords":"keywords",
            "about":"for_codes",
            "funder":"funder",
            "Dataset version":None,
            "Temporal extents":None,
            "Spatial extents":None,
            "Dataset lineage information":None,
            "Dataset format":None,
            "Dataset status":None,
            "hasPart":None
            }
        

model_inputs_node_mapping = {"@id":None,
            "@type":None,
            "description":None,
            "creator":"creator",
            "author":None,
            "version":None,
            "programmingLanguage":None,
            "owl:sameAs":"model_code_uri",
            "keywords":None,
            "runtimePlatform":None,
            "memoryRequirements":None,
            "processorRequirements":None,
            "storageRequirements":None}


model_outputs_node_mapping = {"@id":None,
            "@id":None,
            "@type":None,
            "description":None,
            "creator":"creator",
            "author":None,
            "version":None,
            "programmingLanguage":None,
            "owl:sameAs":None,
            "keywords":None,
            "runtimePlatform":None,
            "memoryRequirements":None,
            "processorRequirements":None,
            "storageRequirements":None,
            }



dataset_creation_node_mapping = {"@id":None,
            "@type":None,
            "agent":"creator",
            "description":None,
            "endTime":None,
            "endTime":None,
            "instrument":"computer_uri",
            "object":None,
            "result":None}

default_issue_entity_mapping_list = [root_node_mapping,
                model_inputs_node_mapping,
                model_inputs_node_mapping,
                dataset_creation_node_mapping]

