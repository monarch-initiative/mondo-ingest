prefix owl: <http://www.w3.org/2002/07/owl#>
prefix BFO: <http://purl.obolibrary.org/obo/BFO_>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>

DELETE {
  ?x rdfs:subClassOf ?super .
   ?super a owl:Restriction ;
   owl:onProperty BFO:0000050 ;
   owl:someValuesFrom ?y
}
INSERT {
  ?x rdfs:subClassOf ?y
}
WHERE {
  ?x rdfs:subClassOf ?super .
   ?super a owl:Restriction ;
   owl:onProperty BFO:0000050 ;
   owl:someValuesFrom ?y
}
