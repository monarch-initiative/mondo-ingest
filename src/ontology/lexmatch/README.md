# MONDO ingest lexical mapping pipeline.
## Content of directories:
* mondo-only: Positive mappings in MONDO not caught by the lexical mapping pipeline
* split-mapping-set: Unmapped mappings broken down by predicate_id
## Summary of mappings:
 * Number of mappings in [`unmapped_doid_lex`](unmapped_doid_lex.tsv): 109
 * Number of mappings in [`unmapped_doid_lex_exact`](unmapped_doid_lex.tsv): 67
 * Number of mappings in [`unmapped_doid_mondo`](mondo-only/unmapped_doid_mondo.tsv): 34
 * Number of mappings in [`unmapped_doid_mondo_exact`](mondo-only/unmapped_doid_mondo.tsv): 34
 * Number of mappings in [`unmapped_icd10cm_lex`](unmapped_icd10cm_lex.tsv): 1047
 * Number of mappings in [`unmapped_icd10cm_lex_exact`](unmapped_icd10cm_lex.tsv): 999
 * Number of mappings in [`unmapped_icd10cm_mondo`](mondo-only/unmapped_icd10cm_mondo.tsv): 6
 * Number of mappings in [`unmapped_icd10cm_mondo_exact`](mondo-only/unmapped_icd10cm_mondo.tsv): 6
 * Number of mappings in [`unmapped_icd10who_lex`](unmapped_icd10who_lex.tsv): 1467
 * Number of mappings in [`unmapped_icd10who_lex_exact`](unmapped_icd10who_lex.tsv): 918
 * Number of mappings in [`unmapped_icd10who_mondo`](mondo-only/unmapped_icd10who_mondo.tsv): 2
 * Number of mappings in [`unmapped_icd10who_mondo_exact`](mondo-only/unmapped_icd10who_mondo.tsv): 2
 * Number of mappings in [`unmapped_icd11foundation_lex`](unmapped_icd11foundation_lex.tsv): 4792
 * Number of mappings in [`unmapped_icd11foundation_lex_exact`](unmapped_icd11foundation_lex.tsv): 4779
 * Number of mappings in [`unmapped_icd11foundation_mondo`](mondo-only/unmapped_icd11foundation_mondo.tsv): 45
 * Number of mappings in [`unmapped_icd11foundation_mondo_exact`](mondo-only/unmapped_icd11foundation_mondo.tsv): 43
 * Number of mappings in [`unmapped_ncit_lex`](unmapped_ncit_lex.tsv): 650
 * Number of mappings in [`unmapped_ncit_lex_exact`](unmapped_ncit_lex.tsv): 597
 * Number of mappings in [`unmapped_ncit_mondo`](mondo-only/unmapped_ncit_mondo.tsv): 13
 * Number of mappings in [`unmapped_ncit_mondo_exact`](mondo-only/unmapped_ncit_mondo.tsv): 13
 * Number of mappings in [`unmapped_omim_lex`](unmapped_omim_lex.tsv): 3
 * Number of mappings in [`unmapped_omim_lex_exact`](unmapped_omim_lex.tsv): 1
 * Number of mappings in [`unmapped_omim_mondo`](mondo-only/unmapped_omim_mondo.tsv): 107
 * Number of mappings in [`unmapped_omim_mondo_exact`](mondo-only/unmapped_omim_mondo.tsv): 107
 * Number of mappings in [`unmapped_ordo_lex`](unmapped_ordo_lex.tsv): 5
 * Number of mappings in [`unmapped_ordo_lex_exact`](unmapped_ordo_lex.tsv): 5
 * Number of mappings in [`unmapped_ordo_mondo`](mondo-only/unmapped_ordo_mondo.tsv): 867
 * Number of mappings in [`unmapped_ordo_mondo_exact`](mondo-only/unmapped_ordo_mondo.tsv): 867
## mondo_XXXXmatch_ontology
 * Number of mappings in [`mondo_broadmatch_icd11.foundation`](split-mapping-set/mondo_broadmatch_icd11.foundation.tsv): 138
 * Number of mappings in [`mondo_exactmatch_icd11.foundation`](split-mapping-set/mondo_exactmatch_icd11.foundation.tsv): 5006
 * Number of mappings in [`mondo_closematch_icd11.foundation`](split-mapping-set/mondo_closematch_icd11.foundation.tsv): 1576
 * Number of mappings in [`mondo_broadmatch_icd10who`](split-mapping-set/mondo_broadmatch_icd10who.tsv): 56
 * Number of mappings in [`mondo_exactmatch_icd10who`](split-mapping-set/mondo_exactmatch_icd10who.tsv): 1467
 * Number of mappings in [`mondo_closematch_icd10who`](split-mapping-set/mondo_closematch_icd10who.tsv): 304
 * Number of mappings in [`mondo_narrowmatch_icd10who`](split-mapping-set/mondo_narrowmatch_icd10who.tsv): 214
 * Number of mappings in [`mondo_broadmatch_ncit`](split-mapping-set/mondo_broadmatch_ncit.tsv): 80
 * Number of mappings in [`mondo_exactmatch_ncit`](split-mapping-set/mondo_exactmatch_ncit.tsv): 666
 * Number of mappings in [`mondo_closematch_ncit`](split-mapping-set/mondo_closematch_ncit.tsv): 347
 * Number of mappings in [`mondo_exactmatch_orphanet`](split-mapping-set/mondo_exactmatch_orphanet.tsv): 870
 * Number of mappings in [`mondo_closematch_orphanet`](split-mapping-set/mondo_closematch_orphanet.tsv): 27
 * Number of mappings in [`mondo_broadmatch_icd10cm`](split-mapping-set/mondo_broadmatch_icd10cm.tsv): 98
 * Number of mappings in [`mondo_exactmatch_icd10cm`](split-mapping-set/mondo_exactmatch_icd10cm.tsv): 1051
 * Number of mappings in [`mondo_closematch_icd10cm`](split-mapping-set/mondo_closematch_icd10cm.tsv): 4869
 * Number of mappings in [`mondo_narrowmatch_icd10cm`](split-mapping-set/mondo_narrowmatch_icd10cm.tsv): 464
 * Number of mappings in [`mondo_exactmatch_omimps`](split-mapping-set/mondo_exactmatch_omimps.tsv): 8
 * Number of mappings in [`mondo_closematch_omimps`](split-mapping-set/mondo_closematch_omimps.tsv): 8
 * Number of mappings in [`mondo_broadmatch_doid`](split-mapping-set/mondo_broadmatch_doid.tsv): 4
 * Number of mappings in [`mondo_exactmatch_doid`](split-mapping-set/mondo_exactmatch_doid.tsv): 141
 * Number of mappings in [`mondo_closematch_doid`](split-mapping-set/mondo_closematch_doid.tsv): 382
 * Number of mappings in [`mondo_narrowmatch_doid`](split-mapping-set/mondo_narrowmatch_doid.tsv): 2
 * Number of mappings in [`mondo_exactmatch_omim`](split-mapping-set/mondo_exactmatch_omim.tsv): 100
