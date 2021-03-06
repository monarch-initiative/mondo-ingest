prefix oio: <http://www.geneontology.org/formats/oboInOwl#>
prefix phenome: <http://www.orpha.net/ORDO/Orphanet_C001>
prefix ms: <http://purl.obolibrary.org/obo/mondo#>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix BFO: <http://purl.obolibrary.org/obo/BFO_>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>

INSERT {
  ?cls oio:inSubset ?subset
}
WHERE {
  ?category rdfs:subClassOf phenome: .
  ?cls rdfs:subClassOf+ ?category .
  ?category rdfs:label ?categoryLabel .
  BIND( URI(CONCAT("http://purl.obolibrary.org/obo/mondo#ordo_", REPLACE(?categoryLabel, " ", "_"))) AS ?subset)
}
