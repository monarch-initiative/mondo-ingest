# MONDO ingest lexical mapping pipeline.
## Content of directories:
* mondo-only: Positive mappings in MONDO not caught by the lexical mapping pipeline
* split-mapping-set: Unmapped mappings broken down by predicate_id
## Summary of mappings:
 * Number of mappings in [`unmapped_doid_lex`](unmapped_doid_lex.tsv): 80
 * Number of mappings in [`unmapped_doid_lex_exact`](unmapped_doid_lex.tsv): 54
 * Number of mappings in [`unmapped_doid_mondo`](mondo-only/unmapped_doid_mondo.tsv): 30
 * Number of mappings in [`unmapped_doid_mondo_exact`](mondo-only/unmapped_doid_mondo.tsv): 30
 * Number of mappings in [`unmapped_icd10cm_lex`](unmapped_icd10cm_lex.tsv): 2376
 * Number of mappings in [`unmapped_icd10cm_lex_exact`](unmapped_icd10cm_lex.tsv): 1973
 * Number of mappings in [`unmapped_icd10cm_mondo`](mondo-only/unmapped_icd10cm_mondo.tsv): 3
 * Number of mappings in [`unmapped_icd10cm_mondo_exact`](mondo-only/unmapped_icd10cm_mondo.tsv): 3
 * Number of mappings in [`unmapped_icd10who_lex`](unmapped_icd10who_lex.tsv): 1651
 * Number of mappings in [`unmapped_icd10who_lex_exact`](unmapped_icd10who_lex.tsv): 907
 * Number of mappings in [`unmapped_icd10who_mondo`](mondo-only/unmapped_icd10who_mondo.tsv): 2
 * Number of mappings in [`unmapped_icd10who_mondo_exact`](mondo-only/unmapped_icd10who_mondo.tsv): 2
 * Number of mappings in [`unmapped_icd11foundation_lex`](unmapped_icd11foundation_lex.tsv): 5840
 * Number of mappings in [`unmapped_icd11foundation_lex_exact`](unmapped_icd11foundation_lex.tsv): 5825
 * Number of mappings in [`unmapped_icd11foundation_mondo`](mondo-only/unmapped_icd11foundation_mondo.tsv): 42
 * Number of mappings in [`unmapped_icd11foundation_mondo_exact`](mondo-only/unmapped_icd11foundation_mondo.tsv): 42
 * Number of mappings in [`unmapped_ncit_lex`](unmapped_ncit_lex.tsv): 698
 * Number of mappings in [`unmapped_ncit_lex_exact`](unmapped_ncit_lex.tsv): 613
 * Number of mappings in [`unmapped_ncit_mondo`](mondo-only/unmapped_ncit_mondo.tsv): 13
 * Number of mappings in [`unmapped_ncit_mondo_exact`](mondo-only/unmapped_ncit_mondo.tsv): 13
 * Number of mappings in [`unmapped_omim_lex`](unmapped_omim_lex.tsv): 4
 * Number of mappings in [`unmapped_omim_lex_exact`](unmapped_omim_lex.tsv): 3
 * Number of mappings in [`unmapped_omim_mondo`](mondo-only/unmapped_omim_mondo.tsv): 134
 * Number of mappings in [`unmapped_omim_mondo_exact`](mondo-only/unmapped_omim_mondo.tsv): 134
 * Number of mappings in [`unmapped_ordo_lex`](unmapped_ordo_lex.tsv): 1
 * Number of mappings in [`unmapped_ordo_lex_exact`](unmapped_ordo_lex.tsv): 1
 * Number of mappings in [`unmapped_ordo_mondo`](mondo-only/unmapped_ordo_mondo.tsv): 870
 * Number of mappings in [`unmapped_ordo_mondo_exact`](mondo-only/unmapped_ordo_mondo.tsv): 870
## mondo_XXXXmatch_ontology
 * Number of mappings in [`mondo_exactmatch_icd10who`](split-mapping-set/mondo_exactmatch_icd10who.tsv): 1651
 * Number of mappings in [`mondo_narrowmatch_icd10who`](split-mapping-set/mondo_narrowmatch_icd10who.tsv): 221
 * Number of mappings in [`mondo_broadmatch_icd10who`](split-mapping-set/mondo_broadmatch_icd10who.tsv): 62
 * Number of mappings in [`mondo_closematch_icd10who`](split-mapping-set/mondo_closematch_icd10who.tsv): 328
 * Number of mappings in [`mondo_exactmatch_icd10cm`](split-mapping-set/mondo_exactmatch_icd10cm.tsv): 2377
 * Number of mappings in [`mondo_narrowmatch_icd10cm`](split-mapping-set/mondo_narrowmatch_icd10cm.tsv): 463
 * Number of mappings in [`mondo_broadmatch_icd10cm`](split-mapping-set/mondo_broadmatch_icd10cm.tsv): 114
 * Number of mappings in [`mondo_closematch_icd10cm`](split-mapping-set/mondo_closematch_icd10cm.tsv): 6233
 * Number of mappings in [`mondo_exactmatch_icd11.foundation`](split-mapping-set/mondo_exactmatch_icd11.foundation.tsv): 6086
 * Number of mappings in [`mondo_broadmatch_icd11.foundation`](split-mapping-set/mondo_broadmatch_icd11.foundation.tsv): 163
 * Number of mappings in [`mondo_closematch_icd11.foundation`](split-mapping-set/mondo_closematch_icd11.foundation.tsv): 1710
 * Number of mappings in [`mondo_exactmatch_omimps`](split-mapping-set/mondo_exactmatch_omimps.tsv): 8
 * Number of mappings in [`mondo_closematch_omimps`](split-mapping-set/mondo_closematch_omimps.tsv): 2
 * Number of mappings in [`mondo_exactmatch_orphanet`](split-mapping-set/mondo_exactmatch_orphanet.tsv): 869
 * Number of mappings in [`mondo_closematch_orphanet`](split-mapping-set/mondo_closematch_orphanet.tsv): 14
 * Number of mappings in [`mondo_exactmatch_doid`](split-mapping-set/mondo_exactmatch_doid.tsv): 108
 * Number of mappings in [`mondo_narrowmatch_doid`](split-mapping-set/mondo_narrowmatch_doid.tsv): 4
 * Number of mappings in [`mondo_broadmatch_doid`](split-mapping-set/mondo_broadmatch_doid.tsv): 1
 * Number of mappings in [`mondo_closematch_doid`](split-mapping-set/mondo_closematch_doid.tsv): 359
 * Number of mappings in [`mondo_exactmatch_omim`](split-mapping-set/mondo_exactmatch_omim.tsv): 128
 * Number of mappings in [`mondo_closematch_omim`](split-mapping-set/mondo_closematch_omim.tsv): 2
 * Number of mappings in [`mondo_exactmatch_ncit`](split-mapping-set/mondo_exactmatch_ncit.tsv): 712
 * Number of mappings in [`mondo_broadmatch_ncit`](split-mapping-set/mondo_broadmatch_ncit.tsv): 82
 * Number of mappings in [`mondo_closematch_ncit`](split-mapping-set/mondo_closematch_ncit.tsv): 385
