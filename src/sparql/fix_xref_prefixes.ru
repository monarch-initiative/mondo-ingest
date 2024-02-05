prefix oio: <http://www.geneontology.org/formats/oboInOwl#>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
prefix xref: <http://www.geneontology.org/formats/oboInOwl#hasDbXref>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>


DELETE {
  ?entity xref: ?value .
  ?ax a owl:Axiom ;
         owl:annotatedSource ?entity ;
         owl:annotatedProperty xref: ;
         owl:annotatedTarget ?value ;
         <http://purl.obolibrary.org/obo/ECO_0000218> ?v .
}
INSERT {
  ?entity xref: ?value_fixed .
  [] rdf:type owl:Axiom ;
    owl:annotatedSource ?entity ;
    owl:annotatedProperty xref: ;
    owl:annotatedTarget ?value_fixed ;
    <http://purl.obolibrary.org/obo/ECO_0000218> ?v .
}
WHERE 
{
  ?entity xref: ?value .
  OPTIONAL {
    ?ax a owl:Axiom ;
           owl:annotatedSource ?entity ;
           owl:annotatedProperty xref: ;
           owl:annotatedTarget ?value ;
           <http://purl.obolibrary.org/obo/ECO_0000218> ?v .
  }
  FILTER (isIRI(?entity))
  BIND(
    REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(?value, 
        "\u00A0", "", "i"), 
        "ICD-11:", "ICD11:", "i"), 
        "ICD-10:", "ICD10:", "i"), 
        "MeSH:", "MESH:", "i"), 
        "OMIM:PS", "OMIMPS:", "i") AS ?value_fixed)
}
