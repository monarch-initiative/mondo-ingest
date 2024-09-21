PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>

DELETE {
  ?axiom oboInOwl:hasSynonymType <http://purl.obolibrary.org/obo/OMO_0003000> .
}
INSERT {
  ?axiom oboInOwl:hasSynonymType <http://purl.obolibrary.org/obo/mondo#ABBREVIATION> .

  <http://purl.obolibrary.org/obo/mondo#ABBREVIATION> a owl:AnnotationProperty ;
    rdfs:subPropertyOf oboInOwl:SynonymTypeProperty .
}
WHERE {
  ?axiom a owl:Axiom ;
         oboInOwl:hasSynonymType <http://purl.obolibrary.org/obo/OMO_0003000> .
}