# Migratable terms
| Ontology                                        | Tot   |
|:------------------------------------------------|:------|
| [ICD11FOUNDATION](./migrate_icd11foundation.md) | 4,587 |
| [ICD10CM](./migrate_icd10cm.md)                 | 3,696 |
| [DOID](./migrate_doid.md)                       | 256   |
| [NCIT](./migrate_ncit.md)                       | 2,250 |
| [OMIM](./migrate_omim.md)                       | 14    |
| [ICD10WHO](./migrate_icd10who.md)               | 119   |
| [ORDO](./migrate_ordo.md)                       | 10    |

### Codebook
`Ontology`: Name of ontology    
`Tot`: Total terms migratable

### Definitions
**Migratable term**: A term owned by the given ontology but unmapped in Mondo, which has either no parents, or if it has 
parents, all of its parents have already been mapped in Mondo.

### Workflows
To run the workflow that creates this data, refer to the [workflows documentation](../developer/workflows.md).