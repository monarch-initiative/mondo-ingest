PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
prefix IAO: <http://purl.obolibrary.org/obo/IAO_>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix oio: <http://www.geneontology.org/formats/oboInOwl#>
prefix def: <http://purl.obolibrary.org/obo/IAO_0000115>
prefix owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>

INSERT {
  ?cls skos:exactMatch ?iri .
}

WHERE 
{  
  ?cls a owl:Class; 
     	oboInOwl:hasDbXref ?value .
  
  FILTER NOT EXISTS {
  	?cls owl:deprecated ?deprecated .
  }
  
  # Only make the "exactMatch" assumption of 1:1.
  FILTER NOT EXISTS {
  	?cls oboInOwl:hasDbXref ?value2 .
    FILTER( STRSTARTS(str(?value2), "MIM"))
    FILTER(?value!=?value2)
  }
  
  FILTER( STRSTARTS(str(?value), "MIM"))
  FILTER( !isBlank(?cls) && STRSTARTS(str(?cls), "http://purl.obolibrary.org/obo/DOID_"))
  BIND(IRI(REPLACE(REPLACE(STR(?value), "MIMPS:", "https://omim.org/phenotypicSeries/PS"), "MIM:", "https://omim.org/entry/")) as ?iri)

}
