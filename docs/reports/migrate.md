# Migratable terms
| Ontology                                        | Tot    |
|:------------------------------------------------|:-------|
| [GARD](./migrate_gard.md)                       | 9,370  |
| [DOID](./migrate_doid.md)                       | 33     |
| [NCIT](./migrate_ncit.md)                       | 2,209  |
| [OMIM](./migrate_omim.md)                       | 2      |
| [ICD11FOUNDATION](./migrate_icd11foundation.md) | 12,409 |
| [ICD10WHO](./migrate_icd10who.md)               | 119    |
| [ICD10CM](./migrate_icd10cm.md)                 | 1,892  |
| [ORDO](./migrate_ordo.md)                       | 0      |

### Codebook
`Ontology`: Name of ontology    
`Tot`: Total terms migratable

### Definitions
**Migratable term**: A term owned by the given ontology but unmapped in Mondo, which has either no parents, or if it has 
parents, all of its parents have already been mapped in Mondo.

### Workflows
To run the workflow that creates this data, refer to the [workflows documentation](../developer/workflows.md).