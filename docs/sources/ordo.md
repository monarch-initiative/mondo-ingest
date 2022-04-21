# MONDO - ORDO Alignment

**Source name:** Orphanet Rare Disease Ontology

**Source description:** "The Orphanet Rare Disease ontology (ORDO) was jointly developed by Orphanet and the EBI to provide a structured vocabulary for rare diseases capturing relationships between diseases, genes and other relevant features which will form a useful resource for the computational analysis of rare diseases (https://www.orphadata.org)."


**Homepage:** http://www.orphadata.org/

**Comments about this source:** ORDO is not really OWL in the strict sense. For example, disease 2 gene relationships follow the  'some, some' logic (a disease may have basis in the mutation of one of these),  while the OWL interpretation of these axioms is that the disease has basis in the mutation of  all of them. Example: ramona wartz disease can have a mutation in _any_ (not all) of the genes recorded in ORDO. This is why great care needs to be taking interpreting diesease 2 gene relationships during ingest!



## Preprocessing:
* EntityRemoval: 
  * Orphanet:317343
  * Orphanet:317344
  * Orphanet:317345
  * Orphanet:317346
  * Orphanet:317348
  * Orphanet:317349
  * Orphanet:327767
  * Orphanet:410295
  * Orphanet:410296
  * Orphanet:465410
  * Orphanet:C016
  * Orphanet:C017
  * Orphanet:C020
  * Orphanet:C022
  * Orphanet:C025
  * Orphanet:C026
* EntityRemoval: Removing information that are on obsolete Mondo terms (MONDO:ObsoleteEquivalent).
* Update: Updating the source with various SPARQL preprocessing steps
    * [MONDO_INGEST_QUERY:fix_deprecated.ru](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/sparql/fix_deprecated.ru)
    * [MONDO_INGEST_QUERY:fix_complex_reification.ru](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/sparql/fix_complex_reification.ru)
    * [MONDO_INGEST_QUERY:fix_xref_prefixes.ru](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/sparql/fix_xref_prefixes.ru)
    * [MONDO_INGEST_QUERY:ordo-construct-subclass-from-part-of.ru](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/sparql/ordo-construct-subclass-from-part-of.ru)
    * [MONDO_INGEST_QUERY:ordo-construct-subsets.ru](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/sparql/ordo-construct-subsets.ru)
    * [MONDO_INGEST_QUERY:ordo-construct-d2g.ru](https://github.com/monarch-initiative/mondo-ingest/blob/main/src/sparql/ordo-construct-d2g.ru)



## Curation Instructions

* For every orphanet class that is associated with more than a gene, we should check if that gene is associated with a subclass. If so, we could have a gap. We may want to use the d2g links for gap filling.
* ORDO d2g relations follow some-some logic rather than OWL's all-some semantics. It is important not to import them blindly, see comments.


You can make issues or ask questions about this source [here](https://github.com/monarch-initiative/mondo-ingest/issues).
