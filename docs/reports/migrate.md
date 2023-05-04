# Migratable terms
| Ontology                          | Tot   |
|:----------------------------------|:------|
| [ORDO](./migrate_ordo.md)         | 7     |
| [DOID](./migrate_doid.md)         | 473   |
| [NCIT](./migrate_ncit.md)         | 4,034 |
| [OMIM](./migrate_omim.md)         | 3     |
| [ICD10WHO](./migrate_icd10who.md) | 117   |
| [ICD10CM](./migrate_icd10cm.md)   | 1,847 |

### Codebook
`Ontology`: Name of ontology    
`Tot`: Total terms migratable

### Definitions
**Migratable term**: A term owned by the given ontology but unmapped in Mondo, which has either no parents, or if it has 
parents, all of its parents have already been mapped in Mondo.

### Workflows
To run the workflow that creates this data, refer to the [workflows documentation](../developer/workflows.md).