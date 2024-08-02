# Create an exact synonym copy for all labels
PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

INSERT {
  ?cls oboInOwl:hasExactSynonym ?label .
} WHERE {
  ?cls rdfs:label ?label .
  FILTER NOT EXISTS { ?cls owl:deprecated ?deprecated . }
}
