prefix oio: <http://www.geneontology.org/formats/oboInOwl#>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
prefix xref: <http://www.geneontology.org/formats/oboInOwl#hasDbXref>
prefix efo: <http://www.ebi.ac.uk/efo/>
prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>


INSERT {
  ?entity rdf:type owl:Class .
  ?entity owl:deprecated "true"^^xsd:boolean .
}
WHERE 
{
  ?entity efo:reason_for_obsolescence ?value .
  FILTER (isIRI(?entity) && (regex(str(?entity), "http://www.orpha.net/ORDO/")))
}
