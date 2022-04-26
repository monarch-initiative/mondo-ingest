PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX RO: <http://purl.obolibrary.org/obo/RO_>

DELETE {
  ?cls ?pred ?obj .
  ?pred rdf:type owl:AnnotationProperty .
}

INSERT {
  ?pred rdf:type owl:ObjectProperty .
  ?cls rdfs:subClassOf [
               owl:onProperty ?pred ;
               owl:someValuesFrom ?obj ] 
}
WHERE {
  VALUES ?pred { RO:0002200 RO:0002525 RO:0003303 }
  ?cls ?pred ?obj .
  ?pred rdf:type owl:AnnotationProperty .
}