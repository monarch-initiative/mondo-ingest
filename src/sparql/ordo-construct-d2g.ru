prefix owl: <http://www.w3.org/2002/07/owl#>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix Orphanet: <http://www.orpha.net/ORDO/Orphanet_>
prefix symbol: <http://www.orpha.net/ORDO/Orphanet_#symbol>
prefix RO: <http://purl.obolibrary.org/obo/RO_>
prefix oio: <http://www.geneontology.org/formats/oboInOwl#>

INSERT {
  ?hgncGene a owl:Class ;
            rdfs:label ?symbol .
  ?disease
     rdfs:subClassOf
      [
          a owl:Restriction ;
          owl:onProperty ?oboRel ;
          owl:someValuesFrom ?hgncGene
      ]
}
WHERE {
  ?gene rdfs:subClassOf [
               owl:onProperty ?ordoRel ;
               owl:someValuesFrom ?disease ] ;
        rdfs:label ?geneLabel ;
        oio:hasDbXref ?xref ;
        rdfs:subClassOf+ Orphanet:C010 .
  ?disease rdfs:label ?diseaseLabel ;
           rdfs:subClassOf+ Orphanet:C001 .
  OPTIONAL { ?gene symbol: ?symbol }
  FILTER( STRSTARTS(STR(?xref), "HGNC:") )
  BIND( IRI(REPLACE(?xref, "HGNC:", "http://identifiers.org/hgnc/")) AS ?hgncGene)

  VALUES (?ordoRel ?oboRel) {
    ( Orphanet:410295 RO:0004001 )
    ( Orphanet:410296 RO:0004001 )
    ( Orphanet:317343 RO:0004003 )
    ( Orphanet:317344 RO:0004004 )
  }
}