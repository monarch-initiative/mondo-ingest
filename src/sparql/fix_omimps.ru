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
  FILTER(STRSTARTS(str(?value), "MIM:PS"))
  FILTER (isIRI(?entity))
  BIND(REPLACE(?value, "MIM:PS", "MIMPS:", "i") AS ?value_fixed)
}
