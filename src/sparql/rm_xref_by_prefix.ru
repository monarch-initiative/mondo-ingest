PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>

DELETE {
  ?x oboInOwl:hasDbXref ?xref .
}
WHERE {
  ?x oboInOwl:hasDbXref ?xref .
  OPTIONAL { 
    ?x a owl:Axiom ;
    owl:annotatedSource ?cls ;
    owl:annotatedProperty ?pred ;
    owl:annotatedTarget ?obj ;
    oboInOwl:hasDbXref ?xref ;
    ?p1 ?o2 .
  }
  FILTER( STRSTARTS(str(?xref), "UMLS_ICD9CM_2005_AUI:") || STRSTARTS(str(?xref), "SNOMEDCT_US_") || STRSTARTS(str(?xref), "IMDRF:") || STRSTARTS(str(?xref), "url:") )
}