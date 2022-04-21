# MONDO - ICD10CM Alignment

**Source name:** ICD10CM

**Source description:** For ICD10CM we use the Bioportal serialisation.


**Homepage:** https://bioportal.bioontology.org/ontologies/ICD10CM

**Comments about this source:** None


## Preprocessing:
* **EntityRemoval**: Some properties like skos:notation are redundant and  result in illegal punning, that is why they are removed as a whole.

    * skos:notation




The data pipeline that generates the source is implemented in `make`, in this source file: [src/ontology/mondo-ingest.Makefile](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/ontology/mondo-ingest.Makefile).

You can make issues or ask questions about this source [here](https://github.com/monarch-initiative/mondo-ingest/issues).
