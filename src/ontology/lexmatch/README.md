# MONDO ingest lexical mapping pipeline.
## Content of directories:
* mondo-only: Positive mappings in MONDO not caught by the lexical mapping pipeline
* split-mapping-set: Unmapped mappings broken down by predicate_id
## Summary of mappings:
 * Number of mappings in [`unmapped_doid_lex`](unmapped_doid_lex.tsv): 192
 * Number of mappings in [`unmapped_doid_lex_exact`](unmapped_doid_lex.tsv): 87
 * Number of mappings in [`unmapped_doid_mondo`](mondo-only/unmapped_doid_mondo.tsv): 35
 * Number of mappings in [`unmapped_doid_mondo_exact`](mondo-only/unmapped_doid_mondo.tsv): 35
 * Number of mappings in [`unmapped_icd10cm_lex`](unmapped_icd10cm_lex.tsv): 900
 * Number of mappings in [`unmapped_icd10cm_lex_exact`](unmapped_icd10cm_lex.tsv): 851
 * Number of mappings in [`unmapped_icd10cm_mondo`](mondo-only/unmapped_icd10cm_mondo.tsv): 6
 * Number of mappings in [`unmapped_icd10cm_mondo_exact`](mondo-only/unmapped_icd10cm_mondo.tsv): 6
 * Number of mappings in [`unmapped_icd10who_lex`](unmapped_icd10who_lex.tsv): 1357
 * Number of mappings in [`unmapped_icd10who_lex_exact`](unmapped_icd10who_lex.tsv): 803
 * Number of mappings in [`unmapped_icd10who_mondo`](mondo-only/unmapped_icd10who_mondo.tsv): 2
 * Number of mappings in [`unmapped_icd10who_mondo_exact`](mondo-only/unmapped_icd10who_mondo.tsv): 2
 * Number of mappings in [`unmapped_icd11foundation_lex`](unmapped_icd11foundation_lex.tsv): 4215
 * Number of mappings in [`unmapped_icd11foundation_lex_exact`](unmapped_icd11foundation_lex.tsv): 4191
 * Number of mappings in [`unmapped_icd11foundation_mondo`](mondo-only/unmapped_icd11foundation_mondo.tsv): 45
 * Number of mappings in [`unmapped_icd11foundation_mondo_exact`](mondo-only/unmapped_icd11foundation_mondo.tsv): 43
 * Number of mappings in [`unmapped_ncit_lex`](unmapped_ncit_lex.tsv): 547
 * Number of mappings in [`unmapped_ncit_lex_exact`](unmapped_ncit_lex.tsv): 488
 * Number of mappings in [`unmapped_ncit_mondo`](mondo-only/unmapped_ncit_mondo.tsv): 13
 * Number of mappings in [`unmapped_ncit_mondo_exact`](mondo-only/unmapped_ncit_mondo.tsv): 13
 * Number of mappings in [`unmapped_omim_lex`](unmapped_omim_lex.tsv): 22
 * Number of mappings in [`unmapped_omim_lex_exact`](unmapped_omim_lex.tsv): 19
 * Number of mappings in [`unmapped_omim_mondo`](mondo-only/unmapped_omim_mondo.tsv): 109
 * Number of mappings in [`unmapped_omim_mondo_exact`](mondo-only/unmapped_omim_mondo.tsv): 109
 * Number of mappings in [`unmapped_ordo_lex`](unmapped_ordo_lex.tsv): 7
 * Number of mappings in [`unmapped_ordo_lex_exact`](unmapped_ordo_lex.tsv): 4
 * Number of mappings in [`unmapped_ordo_mondo`](mondo-only/unmapped_ordo_mondo.tsv): 868
 * Number of mappings in [`unmapped_ordo_mondo_exact`](mondo-only/unmapped_ordo_mondo.tsv): 868
## mondo_XXXXmatch_ontology
 * Number of mappings in [`mondo_closematch_ncit`](split-mapping-set/mondo_closematch_ncit.tsv): 195
 * Number of mappings in [`mondo_exactmatch_ncit`](split-mapping-set/mondo_exactmatch_ncit.tsv): 561
 * Number of mappings in [`mondo_broadmatch_ncit`](split-mapping-set/mondo_broadmatch_ncit.tsv): 88
 * Number of mappings in [`mondo_closematch_orphanet`](split-mapping-set/mondo_closematch_orphanet.tsv): 49
 * Number of mappings in [`mondo_exactmatch_orphanet`](split-mapping-set/mondo_exactmatch_orphanet.tsv): 873
 * Number of mappings in [`mondo_broadmatch_orphanet`](split-mapping-set/mondo_broadmatch_orphanet.tsv): 3
 * Number of mappings in [`mondo_closematch_icd11.foundation`](split-mapping-set/mondo_closematch_icd11.foundation.tsv): 877
 * Number of mappings in [`mondo_exactmatch_icd11.foundation`](split-mapping-set/mondo_exactmatch_icd11.foundation.tsv): 4362
 * Number of mappings in [`mondo_broadmatch_icd11.foundation`](split-mapping-set/mondo_broadmatch_icd11.foundation.tsv): 135
 * Number of mappings in [`mondo_closematch_icd10who`](split-mapping-set/mondo_closematch_icd10who.tsv): 122
 * Number of mappings in [`mondo_exactmatch_icd10who`](split-mapping-set/mondo_exactmatch_icd10who.tsv): 1357
 * Number of mappings in [`mondo_narrowmatch_icd10who`](split-mapping-set/mondo_narrowmatch_icd10who.tsv): 204
 * Number of mappings in [`mondo_broadmatch_icd10who`](split-mapping-set/mondo_broadmatch_icd10who.tsv): 58
 * Number of mappings in [`mondo_closematch_doid`](split-mapping-set/mondo_closematch_doid.tsv): 919
 * Number of mappings in [`mondo_exactmatch_doid`](split-mapping-set/mondo_exactmatch_doid.tsv): 225
 * Number of mappings in [`mondo_narrowmatch_doid`](split-mapping-set/mondo_narrowmatch_doid.tsv): 5
 * Number of mappings in [`mondo_closematch_omim`](split-mapping-set/mondo_closematch_omim.tsv): 32
 * Number of mappings in [`mondo_exactmatch_omim`](split-mapping-set/mondo_exactmatch_omim.tsv): 121
 * Number of mappings in [`mondo_closematch_icd10cm`](split-mapping-set/mondo_closematch_icd10cm.tsv): 4302
 * Number of mappings in [`mondo_exactmatch_icd10cm`](split-mapping-set/mondo_exactmatch_icd10cm.tsv): 904
 * Number of mappings in [`mondo_narrowmatch_icd10cm`](split-mapping-set/mondo_narrowmatch_icd10cm.tsv): 455
 * Number of mappings in [`mondo_broadmatch_icd10cm`](split-mapping-set/mondo_broadmatch_icd10cm.tsv): 97
 * Number of mappings in [`mondo_closematch_omimps`](split-mapping-set/mondo_closematch_omimps.tsv): 2
 * Number of mappings in [`mondo_exactmatch_omimps`](split-mapping-set/mondo_exactmatch_omimps.tsv): 8
