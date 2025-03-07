PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>

# Fix synonym formatting for ICD11 where (MIM ######) or (OMIM ######) is appended to the synonym

DELETE {
  ?class oboInOwl:hasExactSynonym ?exactSynonym .
}

INSERT {
  ?class oboInOwl:hasExactSynonym ?updatedSynonym .
}

WHERE {
  # Match exact synonyms containing "(MIM ######)" or "(OMIM ###)"
  ?class oboInOwl:hasExactSynonym ?exactSynonym .
  FILTER(regex(str(?exactSynonym), "\\((MIM \\d{6}|OMIM\\s+#\\d{6})\\)"))

  # Remove the "(MIM ######)" or "(OMIM ###)" part
  BIND(REPLACE(STR(?exactSynonym), "\\s*\\((MIM \\d{6}|OMIM\\s+#\\d{6})\\)", "") AS ?updatedSynonym)
  
  # Ensure the updated synonym is different
  FILTER(?exactSynonym != ?updatedSynonym)
}

