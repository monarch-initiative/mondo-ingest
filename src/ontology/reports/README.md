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

### 3b. `excluded_terms.txt`
A concatentation of all `<ONTOLOGY_NAME>_term_exclusions.txt`. Similarly, is a simple list of terms with no column 
header.

Created by running `cd src/ontology; sh run.sh make reports/excluded_terms.txt`.

### 4a. `<ONTOLOGY_NAME>_exclusion_reasons.robot.template.tsv`
A variation of `<ONTOLOGY_NAME>_term_exclusions.txt` with additional information. The final list of terms to exclude 
from Mondo for the given ontology. 
- `term_id` (`curie`): Can be (a) a CURIE for a term, or (b) empty; should only be empty if `term_label` is a regular 
  expression. 
- `term_label` (`str`): Can be (a) the literal text of the label, or (b) a regular expression, of the format 
  `REGEX:<expression>`. `<expression>` should be a syntactically correct regular expression. The `<expression>` will get
  passed to SPARQL like so: `FILTER (REGEX(?term_label, "{{ <expression> }}"))`.

Created by running `cd src/ontology; sh run.sh make <ONTOLOGY_NAME>_term_exclusions.txt`.

### 4b. `exclusion_reasons.robot.template.tsv`
A concatentation of all `<ONTOLOGY_NAME>_exclusion_reasons.robot.template.tsv`. Has the same fields as those files.

Created by running `cd src/ontology; sh run.sh make reports/exclusion_reasons.robot.template.tsv`.

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

### 5b. `excluded_terms_in_mondo_xrefs.tsv.`
A concatentation of all `<ONTOLOGY_NAME>_excluded_terms_in_mondo_xrefs.tsv`. Has the same fields as those files.

Created by running `cd src/ontology; sh run.sh make reports/excluded_terms_in_mondo_xrefs.tsv`.

### 6. `<ONTOLOGY_NAME>_excluded_terms_in_mondo_xrefs_summary.tsv.`
Summary statistics for excluded terms that still have cross-references in Mondo.
- `n_in1_notIn2_in3` (`integer`): Number of terms that still have cross-references in Mondo.
- `pct_in1_notIn2_in3__over_in1` (`float`): Percentage of terms that still have cross-references in Mondo.

Created by running `cd src/ontology; sh run.sh make reports/<ONTOLOGY_NAME>_excluded_terms_in_mondo_xrefs.tsv`.

### 7. `reports/sync-synonym/review-qc-duplicate-exact-synonym-no-abbrev.tsv`
**What this file represents**
This file shows cases that were filtered out of the synonym sync because they caused conflicts, identified by qc-duplicate-exact-synonym-no-abbrev.sparql.

**Columns**
- `synonym`
- `mondo_id`: The Mondo term that is getting affected by an -added or -updated synonym change. If the 'case' for the row 
is -confirmed or -unconfirmed, then this synonym already exists in that Mondo term.
- `source_id`: The source term ID that the synonym is coming from. In the case that a synonym appears in multiple 
sources, there will be multiple rows.
- `case`: 'added' or 'updated', this is a new synonym or changed synonym scope which is coming in through the synonym 
sync. If confirmed or unconfirmed, this is an existing synonym in Mondo, and no change is coming in for this synonym 
through the sync. In the case of confirmed, this synonym is also corroborated by a mapped source term. In case of 
unconfirmed, it exists in Mondo, but was not found as a synonym for any of the mapped source terms.
- `synonym_type`: This is left here mainly as a sanity check to ensure that no cases of MONDO:ABBREVIATION slipped in. 
It is allowable for there to be duplicative synonyms for abbreviations.
- `filtered_because_this_mondo_id_already_has_this_synonym_as_its_label`: This column will be empty in the case of 
exactSynonym-exactSynonym collisions (cases where an exact synonym on one Mondo term is the same as one on another 
mondo term). However, label-synonym is another possible case; that is, a case where there is a new/updated exactSynonym 
coming in through the synonym sync, for which that synonym exists as the label of a separate Mondo term. For those 
cases, there will only be 1 row for the synonym, with 1 or more Mondo IDs in this column.

**Different kinds of conflicts**
_Example 1: exactSynonym-exactSynonym conflict_
You don't want to review just 1 row in isolation. You want to review 1 at a time all of the rows for a given synonym.

For example:
| synonym | mondo_id | source_id | case |
| --- | --- | --- | --- |
| 3C syndrome | MONDO:0009073 | OMIM:220210 | updated |
| 3C syndrome | MONDO:0019078 | GARD:0005666 | confirmed |
| 3C syndrome | MONDO:0019078 | Orphanet:7 | confirmed |

The conflict here is in the first of these rows. The synonym sync wants to update the synonym scope on MONDO:0009073, as evidenced by OMIM:220210. However, in changing it to exactSynonym, there would be a conflict, because that synonym already exists on MONDO:0019078, where it is evidenced by GARD:0005666 and Orphanet:7.

_Example 2: exactSynonym-label conflict_
| synonym | mondo_id | source_id | case | filtered_because_this_mondo_id_already_has_this_synonym_as_its_label |
| --- | --- | --- | --- | --- |
| A20 haploinsufficiency | MONDO:0800045 | DOID:0080944 | added | MONDO:0100222 |

In this case, the synonym sync wants to add a new exactSynonym to MONDO:0800045. However, that synonym exists as a label on a different Mondo term: MONDO:0100222.

**How to review**
Look at these conflict cases and make a recommended action. You can add a note to the 'action' column.
Possible actions (may not be a full list):
a. Disallow the suggested change from the synonym sync.
b. Allow the suggested change from the synonym sync, but remove the conflicting exactSynonym or label within Mondo. Then, the next time the synonym sync runs, it will detect no conflict, and these synonym updates will go through.
c. Allow the suggested change from the synonym sync AND allow a conflict?
