PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

DELETE {
	?sub <http://www.orpha.net/ORDO/Orphanet_C021> ?obj .
}
INSERT {
	?sub rdfs:subClassOf ?iri .
}

WHERE {
  ?sub <http://www.orpha.net/ORDO/Orphanet_C021> ?obj .
  BIND(IRI(?obj) as ?iri) .
}