"""Analyze possible set diffs NCIT subclass relations in mondo-edit and filtered (neoplasm) classes in mondo-ingest"""
import pandas as pd

mondo_df = pd.read_csv('ncit-xrefs-and-subclass-evidence.tsv', sep='\t')
mondo_xrefs = set(mondo_df['?xref'])
mondo_subclass_sources = set(mondo_df['?subClassOf_source'])

# TODO: mirror?
mondo_ingest_df = pd.read_csv('reports/component_signature-ncit.tsv', sep='\t')
mondo_ingest_df['?term'] = mondo_ingest_df['?term']\
    .str.replace('<http://purl.obolibrary.org/obo/NCIT_', 'NCIT:', regex=False).str.replace('>', '', regex=False)

mondo_ingest_terms = set(mondo_ingest_df['?term'])

non_neoplasm_in_mondo__xrefs = mondo_xrefs.difference(mondo_ingest_terms)
non_neoplasm_in_mondo__sources = mondo_subclass_sources.difference(mondo_ingest_terms)
print(f"\nNon-neoplasm subclass source evidence (n) in mondo-edit: {len(non_neoplasm_in_mondo__sources)}")
if non_neoplasm_in_mondo__sources:
    for term in non_neoplasm_in_mondo__sources:
        print(term)
print(f"\nNon-neoplasm xrefs (n) in mondo-edit: {len(non_neoplasm_in_mondo__xrefs)}")
if non_neoplasm_in_mondo__xrefs:
    for term in non_neoplasm_in_mondo__xrefs:
        print(term)
    df = mondo_df[mondo_df['?xref'].isin(non_neoplasm_in_mondo__xrefs)].rename(columns={'?label': '?mondo_label'})
    print(df[['?xref', '?mondo_label']])
    df.to_csv('~/Desktop/non-neoplasm-xrefs-in-mondo-edit.tsv', index=False, sep='\t')

print()
