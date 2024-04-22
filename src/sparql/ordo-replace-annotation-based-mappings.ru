# TODO: were some exampoles (E, BTNT, W) that did not have '- ' at the beginning. is seems possible that some mapping
# strings don't start with '- '? given that, can I do an OR clause for 2 variations of strstarts? or should i use
# 'contains' instead?
prefix skos: <http://www.w3.org/2004/02/skos/core#>
prefix ECO: <http://purl.obolibrary.org/obo/ECO_>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
prefix sssom: <https://w3id.org/sssom/>


# NTBT (ORPHA code's Narrower Term maps to a Broader Term)
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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- NTBT ("))
};

# E (Exact mapping: the two concepts are equivalent)
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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- E ("))
};

# BTNT (ORPHA code's Broader Term maps to a Narrower Term)
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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- BTNT"))
};

# W (Wrong mapping: the two concepts are different)
# TODO: is 'notExactMatch' correct for this type of mapping predicate?
DELETE {
  ?xref_anno a owl:Axiom ;
    ECO:0000218 ?mapping_precision_string .
} INSERT {
  ?cls a owl:Class;
      sssom:notExactMatch ?value .
} WHERE {
  VALUES ?mapping { oboInOwl:hasDbXref }

  ?cls a owl:Class;
    ?mapping ?value .

  ?xref_anno a owl:Axiom ;
    owl:annotatedSource ?cls ;
    owl:annotatedProperty ?mapping ;
    owl:annotatedTarget ?value ;
    ECO:0000218 ?mapping_precision_string .

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- W ("))
};

# ND (not yet decided/unable to decide)
DELETE {
  ?xref_anno a owl:Axiom ;
    ECO:0000218 ?mapping_precision_string .
} INSERT {
  ?cls a owl:Class;
      oboInOwl:hasDbXref ?value .
} WHERE {
  VALUES ?mapping { oboInOwl:hasDbXref }

  ?cls a owl:Class;
    ?mapping ?value .

  ?xref_anno a owl:Axiom ;
    owl:annotatedSource ?cls ;
    owl:annotatedProperty ?mapping ;
    owl:annotatedTarget ?value ;
    ECO:0000218 ?mapping_precision_string .

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- ND ("))
};
