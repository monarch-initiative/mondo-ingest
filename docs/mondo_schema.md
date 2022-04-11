# Mondo schema for sources

## Ontology

0. rdf:type owl:Ontology
1. license (optional)
2. version IRI (optional)

## Terms

1. Label: rdf:label `{string}`
2. Definition: IAO:0000115 `{string}`
3. Synonyms: oboInOwl:has*Synonym `{string}`
4. Named parents: rdf:subClassOf `{IRI}`
5. Simple relations: rdf:subClassOf `{R} some {IRI}`, where R is one of:
   - BFO:0000050
   - BFO:0000051
