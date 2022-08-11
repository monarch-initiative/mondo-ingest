## Codebook: `src/ontology/config/`
### 1. `<ONTOLOGY_NAME>_exclusions.tsv`
An intensional list of terms that were previously included in Mondo (e.g. because they are diseases), but have now been excluded.
- `term_id` (`curie`): Can be (a) a CURIE for a term, or (b) empty; should only be empty if `term_label` is a regular expression. 
- `term_label` (`str`): Can be (a) the literal text of the label, or (b) a regular expression, of the format `REGEX:<expression>`. `<expression>` should be a syntactically correct regular expression. The `<expression>` will get passed to SPARQL like so: `FILTER (REGEX(?term_label, "{{ <expression> }}"))`. 
- `exclusion_reason` (`curie`): CURIE for [Mondo exclusion reason](https://mondo.readthedocs.io/en/latest/editors-guide/exclusion-reasons/). 
- `exclude_children` (`bool`): If `FALSE`, will only exclude the term itself. If `TRUE`, will also expand the children of this term and add to exclusion table.  

Created manually. Used in the creation of more comprehensive exclusion tables downstream. See `src/ontology/reports/README.md` for more information.
