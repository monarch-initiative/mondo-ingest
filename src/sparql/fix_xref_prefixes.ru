prefix oio: <http://www.geneontology.org/formats/oboInOwl#>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
prefix xref: <http://www.geneontology.org/formats/oboInOwl#hasDbXref>

DELETE {
  ?entity xref: ?value .
  ?ax a owl:Axiom ;
         owl:annotatedSource ?entity ;
         owl:annotatedProperty xref: ;
         owl:annotatedTarget ?value ;
         ?p ?v .
}
INSERT {
  ?entity xref: ?value_fixed .
  ?ax a owl:Axiom ;
         owl:annotatedSource ?entity ;
         owl:annotatedProperty xref: ;
         owl:annotatedTarget ?value_fixed ;
         ?p ?v .
}
WHERE 
{
  ?entity xref: ?value .
  OPTIONAL {
    ?ax a owl:Axiom ;
           owl:annotatedSource ?entity ;
           owl:annotatedProperty xref: ;
           owl:annotatedTarget ?value ;
           ?p ?v .
  }
  FILTER (isIRI(?entity))
  BIND(REPLACE(REPLACE(REPLACE(REPLACE(?value, "ICD-11:", "ICD11:", "i"), "ICD-10:", "ICD10:", "i"), "MeSH:", "MESH:", "i"), "OMIM:PS", "OMIMPS:", "i") AS ?value_fixed)
}
