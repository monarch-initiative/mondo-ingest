"""Verify that exclusions numbers are "correct" (do not include non-inclusions and are really 0 if so"""
import pandas as pd

exc_path = 'reports/icd11foundation_term_exclusions.txt'
mir_path = 'reports/mirror_signature-icd11foundation.tsv'
comp_path = 'reports/component_signature-icd11foundation.tsv'

exc_df = pd.read_csv(exc_path, sep='\t', header=None)
mir_df = pd.read_csv(mir_path, sep='\t')
mir_df['?term'] = mir_df['?term'].str.replace('<http://id.who.int/icd/entity/', 'icd11.foundation:')
mir_df['?term'] = mir_df['?term'].str.replace('>', '')
comp_df = pd.read_csv(comp_path, sep='\t')
comp_df['?term'] = comp_df['?term'].str.replace('<http://id.who.int/icd/entity/', 'icd11.foundation:').replace('>', '')
comp_df['?term'] = comp_df['?term'].str.replace('>', '')


exc = set(exc_df[0].tolist())
mir = set(mir_df['?term'].tolist())
comp = set(comp_df['?term'].tolist())

em = exc.intersection(mir)
ec = exc.intersection(comp)
unaccounted = exc - em - ec
print('Exclusions in mirror signature:', len(em))
print('Exclusions in component signature:', len(ec))
print('Unaccounted exclusions:', len(unaccounted))
for e in unaccounted:
    print(' - ', e)

print()
