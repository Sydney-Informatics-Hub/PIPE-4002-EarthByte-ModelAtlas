# PIPE-4002-EarthByte-ModelAtlas
SIH repo for work on PIPE-4002


### Checklist

- [x] New model issue
  - [ ] Build drop down lists from existing resources, e.g. FOR Codes, file format vocabs.
- [x] extract markdown from the issue body? 
  - [ ] Apply additional formatting, generating formatted blocks like tables
- [ ] Set up model repo based on slug
  - [ ] need a template repository
  - [ ] Add licence file based on dropdown list

- [ ]  Handling drag-and-dropped files, and putting them somewhere sensible (building appropriate sub. directories)
- [ ] Build a manifest from these files. 

- [ ] Error checking. Have Python do basic checking for things like DOIs/ ORCIDs 

  - [ ] Elementary checking to make sure the address resolves

  - [ ] More advanced checking involves actually tyring to parse the DOI metadata, but this can be tricky?

- [ ] Building the website YAML from the validated issue.
- [ ] Create a metadata file (json, file) for, e.g. NCI 
- [ ] Provide flexibility for editing the markdown later. 
  - [ ] Requires a rebuild manifest, tables, webfiles, metadata
