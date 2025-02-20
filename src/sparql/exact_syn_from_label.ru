PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

# Create an exact synonym copy for all labels

INSERT {
  <http://purl.obolibrary.org/obo/mondo#GENERATED_FROM_LABEL> rdf:type owl:AnnotationProperty .
  <http://www.geneontology.org/formats/oboInOwl#hasSynonymType> rdf:type owl:AnnotationProperty .
  <http://purl.obolibrary.org/obo/mondo#GENERATED_FROM_LABEL> rdfs:subPropertyOf <http://www.geneontology.org/formats/oboInOwl#SynonymTypeProperty>  .

  ?cls oboInOwl:hasExactSynonym ?label .
	
  	[ 	rdf:type owl:Axiom ;
				owl:annotatedSource ?cls ;
           owl:annotatedProperty oboInOwl:hasExactSynonym ;
           owl:annotatedTarget ?label ;
        oboInOwl:hasSynonymType <http://purl.obolibrary.org/obo/mondo#GENERATED_FROM_LABEL> ].
} WHERE {

  ?cls rdfs:label ?label .

  FILTER NOT EXISTS { ?cls owl:deprecated ?deprecated . }
}
