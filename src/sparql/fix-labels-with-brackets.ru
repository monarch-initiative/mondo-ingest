PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
PREFIX obo: <http://purl.obolibrary.org/obo/>


INSERT {
  <http://purl.obolibrary.org/obo/mondo#GENERATED> rdf:type owl:AnnotationProperty .
  <http://www.geneontology.org/formats/oboInOwl#hasSynonymType> rdf:type owl:AnnotationProperty .
  <http://purl.obolibrary.org/obo/mondo#GENERATED> rdfs:subPropertyOf <http://www.geneontology.org/formats/oboInOwl#SynonymTypeProperty>  .
	
  ?phenotype oboInOwl:hasExactSynonym ?synonym .
	
  	[ 	rdf:type owl:Axiom ;
				owl:annotatedSource ?phenotype ;
           owl:annotatedProperty oboInOwl:hasExactSynonym ;
           owl:annotatedTarget ?synonym ;
        oboInOwl:hasSynonymType <http://purl.obolibrary.org/obo/mondo#GENERATED> ].
}

WHERE {
  VALUES ?property {
    obo:IAO_0000118
    oboInOwl:hasExactSynonym
    rdfs:label
  }
  ?phenotype ?property ?label .
  FILTER(regex(str(?label),"[\\])]$"))
  BIND(REPLACE(lcase(STR(?label)),
      " [\\[(].*[)\\]]$", "") as ?synonym)
}