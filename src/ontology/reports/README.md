## Codebook: `src/ontology/reports/`

### 1. `mirror_signature-<ONTOLOGY_NAME>.tsv`
A "mirror signature" file, which contains a list of class URIs from the unaltered source ontology.
- `?term` (`uri`): URI for class in ontology.   

Created by running `cd src/ontology; sh run.sh make reports/mirror_signature-<ONTOLOGY_NAME>.tsv`.

### 2. `component_signature-<ONTOLOGY_NAME>.tsv`
A "component signature" file, which contains a list of class URIs from Mondo's "alignment module" for the ontology. An 
alignment module is the list of classes we care about (e.g. all diseases).
- `?term` (`uri`): URI for class in ontology.

Created by running `cd src/ontology; sh run.sh make reports/component_signature-<ONTOLOGY_NAME>.tsv`.

### 3. `<ONTOLOGY_NAME>_term_exclusions.txt`
A simplified variation of `<ONTOLOGY_NAME>_exclusion_reasons.robot.template.tsv`. The final list of terms to exclude 
from Mondo for the given ontology. A simple, line-break-delimited list of terms, e.g. a single column with no column 
header. 

Created by running `cd src/ontology; sh run.sh make <ONTOLOGY_NAME>_term_exclusions.txt`.

### 4. `<ONTOLOGY_NAME>_exclusion_reasons.robot.template.tsv`
A variation of `<ONTOLOGY_NAME>_term_exclusions.txt` with additional information. The final list of terms to exclude 
from Mondo for the given ontology. 
- `term_id` (`curie`): Can be (a) a CURIE for a term, or (b) empty; should only be empty if `term_label` is a regular 
  expression. 
- `term_label` (`str`): Can be (a) the literal text of the label, or (b) a regular expression, of the format 
  `REGEX:<expression>`. `<expression>` should be a syntactically correct regular expression. The `<expression>` will get
  passed to SPARQL like so: `FILTER (REGEX(?term_label, "{{ <expression> }}"))`.

Created by running `cd src/ontology; sh run.sh make <ONTOLOGY_NAME>_term_exclusions.txt`.

### 5. `<ONTOLOGY_NAME>_excluded_terms_in_mondo_xrefs.tsv`
A list of excluded terms that still have cross-references in Mondo.
- `term_id` (`curie`): CURIE of the term.
- `term_label` (`string`): Label of the term.
- `1_in_mirror_tsv` (`boolean`): Is `true` if term is listed in the "mirror signature" file.
- `2_in_component_tsv` (`boolean`): Is `true` if term is listed in the "component signature" file.
- `3_in_mondo_xrefs` (`boolean`): Is `true` if term still has a cross-reference in Mondo.
- `in1_notIn2_in3` (`boolean`): Is `true` if term has been excluded but still has cross-reference in Mondo. Defined by 
  logic: `1_in_mirror_tsv` & !`3_in_mondo_xrefs` & `2_in_component_tsv`.

Created by running `cd src/ontology; sh run.sh make reports/<ONTOLOGY_NAME>_excluded_terms_in_mondo_xrefs.tsv`.

### 6. `<ONTOLOGY_NAME>_excluded_terms_in_mondo_xrefs_summary.tsv.`
Summary statistics for excluded terms that still have cross-references in Mondo.
- `n_in1_notIn2_in3` (`integer`): Number of terms that still have cross-references in Mondo.
- `pct_in1_notIn2_in3__over_in1` (`float`): Percentage of terms that still have cross-references in Mondo.

Created by running `cd src/ontology; sh run.sh make reports/<ONTOLOGY_NAME>_excluded_terms_in_mondo_xrefs.tsv`.

### 7. `excluded_terms_in_mondo_xrefs.tsv.`
A concatentation of all `<ONTOLOGY_NAME>_excluded_terms_in_mondo_xrefs.tsv`.
- `term_id` (`curie`): CURIE of the term.
- `term_label` (`string`): Label of the term.
- `1_in_mirror_tsv` (`boolean`): Is `true` if term is listed in the "mirror signature" file.
- `2_in_component_tsv` (`boolean`): Is `true` if term is listed in the "component signature" file.
- `3_in_mondo_xrefs` (`boolean`): Is `true` if term still has a cross-reference in Mondo.
- `in1_notIn2_in3` (`boolean`): Is `true` if term has been excluded but still has cross-reference in Mondo. Defined by 
  logic: `1_in_mirror_tsv` & !`3_in_mondo_xrefs` & `2_in_component_tsv`.

Created by running `cd src/ontology; sh run.sh make reports/excluded_terms_in_mondo_xrefs.tsv`.
