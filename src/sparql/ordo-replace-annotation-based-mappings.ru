prefix skos: <http://www.w3.org/2004/02/skos/core#>
prefix ECO: <http://purl.obolibrary.org/obo/ECO_>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
prefix sssom: <https://w3id.org/sssom/>


## Capture broad matches

DELETE {
  ?xref_anno a owl:Axiom ;
    ECO:0000218 ?mapping_precision_string .
} INSERT {
  ?cls a owl:Class;
      skos:broadMatch ?value .
} WHERE {
  VALUES ?mapping { oboInOwl:hasDbXref }

  ?cls a owl:Class;
    ?mapping ?value .

  ?xref_anno a owl:Axiom ;
    owl:annotatedSource ?cls ;
    owl:annotatedProperty ?mapping ;
    owl:annotatedTarget ?value ;
    ECO:0000218 ?mapping_precision_string .

  FILTER(
    STRSTARTS(STR(?mapping_precision_string), "- NTBT") || 
    STRSTARTS(STR(?mapping_precision_string), "NTBT"))
};

## Capture exact matches

DELETE {
  ?xref_anno a owl:Axiom ;
    ECO:0000218 ?mapping_precision_string .
} INSERT {
  ?cls a owl:Class;
      skos:exactMatch ?value .
} WHERE {
  VALUES ?mapping { oboInOwl:hasDbXref }

  ?cls a owl:Class;
    ?mapping ?value .

  ?xref_anno a owl:Axiom ;
    owl:annotatedSource ?cls ;
    owl:annotatedProperty ?mapping ;
    owl:annotatedTarget ?value ;
    ECO:0000218 ?mapping_precision_string .

  FILTER(STRSTARTS(STR(?mapping_precision_string), "E (Exact "))
};

## Capture narrow matches

DELETE {
  ?xref_anno a owl:Axiom ;
    ECO:0000218 ?mapping_precision_string .
} INSERT {
  ?cls a owl:Class;
      skos:narrowMatch ?value .
} WHERE {
  VALUES ?mapping { oboInOwl:hasDbXref }

  ?cls a owl:Class;
    ?mapping ?value .

  ?xref_anno a owl:Axiom ;
    owl:annotatedSource ?cls ;
    owl:annotatedProperty ?mapping ;
    owl:annotatedTarget ?value ;
    ECO:0000218 ?mapping_precision_string .

  FILTER(
    STRSTARTS(STR(?mapping_precision_string), "BTNT") || 
    STRSTARTS(STR(?mapping_precision_string), "- BTNT")
  )
};

### Remove wrong / not useful mappings

DELETE {
  ?xref_anno a owl:Axiom ;
    ECO:0000218 ?mapping_precision_string .
} WHERE {
  VALUES ?mapping { oboInOwl:hasDbXref }

  ?cls a owl:Class;
    ?mapping ?value .

  ?xref_anno a owl:Axiom ;
    owl:annotatedSource ?cls ;
    owl:annotatedProperty ?mapping ;
    owl:annotatedTarget ?value ;
    ECO:0000218 ?mapping_precision_string .

  FILTER(
    STRSTARTS(STR(?mapping_precision_string), "W (Wrong mapping") ||
    STRSTARTS(STR(?mapping_precision_string), "- ND (not") ||
    STRSTARTS(STR(?mapping_precision_string), "ND (not")
  )
};
