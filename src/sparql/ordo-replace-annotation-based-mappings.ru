prefix skos: <http://www.w3.org/2004/02/skos/core#>
prefix ECO: <http://purl.obolibrary.org/obo/ECO_>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
prefix sssom: <https://mapping-commons.github.io/sssom/purl/>


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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- NTBT (ORPHA code's Narrower Term maps to a Broader Term).\n- Inclusion term (The ORPHA code is included under a ICD10 category and has not its own code)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- NTBT (ORPHA code's Narrower Term maps to a Broader Term).\n- Attributed (The ICD10 code is attributed by Orphanet)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "NTBT (ORPHA code's Narrower Term maps to a Broader Term)"))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- NTBT (ORPHA code's Narrower Term maps to a Broader Term).\n- Index term (The ORPHA code is listed in the ICD10 Index)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- NTBT (ORPHA code's Narrower Term maps to a Broader Term).\n- Specific code (The ORPHA code has its own code in the ICD10)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "E (Exact mapping: the two concepts are equivalent)"))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- E (Exact mapping: the two concepts are equivalent).\n- Specific code (The ORPHA code has its own code in the ICD10)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- E (Exact mapping: the two concepts are equivalent).\n- Index term (The ORPHA code is listed in the ICD10 Index)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- E (Exact mapping: the two concepts are equivalent).\n- Inclusion term (The ORPHA code is included under a ICD10 category and has not its own code)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "BTNT (ORPHA code's Broader Term maps to a Narrower Term)"))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- BTNT (ORPHA code's Broader Term maps to a Narrower Term).\n- Specific code (The ORPHA code has its own code in the ICD10)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- BTNT (ORPHA code's Broader Term maps to a Narrower Term).\n- Attributed (The ICD10 code is attributed by Orphanet)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- BTNT (ORPHA code's Broader Term maps to a Narrower Term).\n- Inclusion term (The ORPHA code is included under a ICD10 category and has not its own code)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- BTNT (ORPHA code's Broader Term maps to a Narrower Term).\n- Index term (The ORPHA code is listed in the ICD10 Index)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "W (Wrong mapping: the two concepts are different)"))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- ND (not yet decided/unable to decide).\n- Attributed (The ICD10 code is attributed by Orphanet)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "ND (not yet decided/unable to decide)"))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- ND (not yet decided/unable to decide).\n- Index term (The ORPHA code is listed in the ICD10 Index)."))
};

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

  FILTER(STRSTARTS(STR(?mapping_precision_string), "- ND (not yet decided/unable to decide).\n- Specific code (The ORPHA code has its own code in the ICD10)."))
};
