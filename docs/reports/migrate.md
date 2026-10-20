# Migratable terms
| Ontology                                        | Tot   |
|:------------------------------------------------|:------|
| [ICD10WHO](./migrate_icd10who.md)               | 984   |
| [OMIM](./migrate_omim.md)                       | 63    |
| [ICD11FOUNDATION](./migrate_icd11foundation.md) | 5,452 |
| [ICD10CM](./migrate_icd10cm.md)                 | 3,914 |
| [ORDO](./migrate_ordo.md)                       | 266   |
| [DOID](./migrate_doid.md)                       | 233   |
| [NCIT](./migrate_ncit.md)                       | 2,382 |

### Codebook
`Ontology`: Name of ontology    
`Tot`: Total terms migratable

### Definitions
**Migratable term**: A term owned by the given ontology but unmapped in Mondo, which has either no parents, or if it has 
parents, all of its parents have already been mapped in Mondo.

### Workflows
To run the workflow that creates this data, refer to the [workflows documentation](../developer/workflows.md).