# MONDO - DO Alignment

**Source name:** DO

**Source description:** The Disease Ontology has been developed as a standardized ontology for  human disease with the purpose of providing the biomedical community  with consistent, reusable and sustainable descriptions of human disease terms,  phenotype characteristics and related medical vocabulary disease concepts  through collaborative efforts of biomedical researchers, coordinated by the  University of Maryland School of Medicine, Institute for Genome Sciences  (https://disease-ontology.org/).


**Homepage:** https://disease-ontology.org/

**Comments about this source:** None


## Preprocessing:
* **Update**: Updating the source with various SPARQL preprocessing steps
    * [MONDO_INGEST_QUERY:fix_make_omim_exact.ru](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/sparql/fix_make_omim_exact.ru)




The data pipeline that generates the source is implemented in `make`, in this source file: [src/ontology/mondo-ingest.Makefile](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/ontology/mondo-ingest.Makefile).

You can make issues or ask questions about this source [here](https://github.com/monarch-initiative/mondo-ingest/issues).
