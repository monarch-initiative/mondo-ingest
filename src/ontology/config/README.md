## Codebook: `src/ontology/config/`
### 1. `<ONTOLOGY_NAME>_exclusions.tsv`
An intensional list of terms that were previously included in Mondo (e.g. because they are diseases), but have now been excluded.
- `term_id` (`curie`): Can be (a) a CURIE for a term, or (b) empty; should only be empty if `term_label` is a regular expression. 
- `term_label` (`str`): Can be (a) the literal text of the label, or (b) a regular expression, of the format `REGEX:<expression>`. `<expression>` should be a syntactically correct regular expression. The `<expression>` will get passed to SPARQL like so: `FILTER (REGEX(?term_label, "{{ <expression> }}"))`. 
- `exclusion_reason` (`curie`): CURIE for [Mondo exclusion reason](https://mondo.readthedocs.io/en/latest/editors-guide/exclusion-reasons/). 
- `exclude_children` (`bool`): If `FALSE`, will only exclude the term itself. If `TRUE`, will also expand the children of this term and add to exclusion table.  

Created manually.

### 2. `<ONTOLOGY_NAME>_term_exclusions.txt`
A simplified variation of (3). The final list of terms to exclude from Mondo for the given ontology. A simple, line-break-delimited list of terms, e.g. a single column with no column header. 

Created by running `cd src/ontology; sh run.sh make <ONTOLOGY_NAME>_term_exclusions.txt`.

Shows a list of all the terms that should be excluded from Mondo.

### 3. `<ONTOLOGY_NAME>_exclusion_reasons.robot.template.tsv`
A variation of (2) with additional information. The final list of terms to exclude from Mondo for the given ontology. 
- `term_id` (`curie`): Can be (a) a CURIE for a term, or (b) empty; should only be empty if `term_label` is a regular expression. 
- `term_label` (`str`): Can be (a) the literal text of the label, or (b) a regular expression, of the format `REGEX:<expression>`. `<expression>` should be a syntactically correct regular expression. The `<expression>` will get passed to SPARQL like so: `FILTER (REGEX(?term_label, "{{ <expression> }}"))`.

Created by running `cd src/ontology; sh run.sh make <ONTOLOGY_NAME>_term_exclusions.txt`.
