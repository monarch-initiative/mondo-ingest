# MONDO - ICD11FOUNDATION Alignment

**Source name:** International Classification of Diseases 11th Revision

**Source description:** The International Classification of Diseases (ICD) provides a common language that allows health professionals to  share standardized information across the world. The eleventh revision contains around 17 000 unique codes, more than  120 000 codable terms and is now entirely digital.Feb 11, 2022
This data source in particular is the ICD11 foundation, not one of its linearizations.


**Homepage:** https://icd.who.int/

**Comments about this source:** 
Because the existing logical equivalence class axioms led to equivalence cliques (groups of distinct disease identifiers
that inferred to he semantically identical) we decided to strip out all equivalence class axiom from the foundation 
prior to processing it in the ingest.





The data pipeline that generates the source is implemented in `make`, in this source file: [src/ontology/mondo-ingest.Makefile](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/ontology/mondo-ingest.Makefile).

You can make issues or ask questions about this source [here](https://github.com/monarch-initiative/mondo-ingest/issues).
