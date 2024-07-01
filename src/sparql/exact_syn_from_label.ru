# Create an exact synonym copy for all labels
prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

INSERT {
  ?cls oboInOwl:hasExactSynonym ?label .
}
WHERE 
{
  ?cls rdfs:label ?label .
}
