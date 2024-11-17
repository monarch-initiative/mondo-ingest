# Mapping progress report
| Ontology                                         | Tot terms   | Tot excluded   | Tot deprecated   | Tot deprecated unmapped   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-------------------------------------------------|:------------|:---------------|:-----------------|:--------------------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md)               | 12,542      | 0              | 0                | 0                         | 12,542                                    | 18                        | 12,524                      | 99.9%                     |
| [ICD10CM](./unmapped_icd10cm.md)                 | 95,847      | 15,452         | 0                | 0                         | 80,395                                    | 1,166                     | 79,229                      | 98.5%                     |
| [ICD11FOUNDATION](./unmapped_icd11foundation.md) | 57,713      | 0              | 5,594            | 5,594                     | 52,119                                    | 4,108                     | 48,011                      | 92.1%                     |
| [NCIT](./unmapped_ncit.md)                       | 191,123     | 169,937        | 5,221            | 5,216                     | 15,965                                    | 3,676                     | 12,289                      | 77.0%                     |
| [GARD](./unmapped_gard.md)                       | 12,004      | 0              | 0                | 0                         | 12,004                                    | 0                         | 12,004                      | 100.0%                    |
| [ORDO](./unmapped_ordo.md)                       | 15,561      | 6,270          | 1,424            | 1,255                     | 9,291                                     | 9,214                     | 77                          | 0.8%                      |
| [DOID](./unmapped_doid.md)                       | 14,172      | 2,660          | 2,488            | 2,477                     | 11,510                                    | 11,457                    | 53                          | 0.5%                      |
| [OMIM](./unmapped_omim.md)                       | 29,537      | 19,376         | 1,367            | 1,322                     | 8,795                                     | 8,758                     | 37                          | 0.4%                      |

`Ontology`: Name of ontology  
`Tot terms`: Total terms in ontology  
`Tot excluded`: Total terms Mondo has excluded from mapping / integrating  
`Tot deprecated`: Total terms that the ontology source itself has deprecated  
`Tot mappable (!excluded, !deprecated)`: Total mappable candidates for Mondo; all terms that are not excluded or 
deprecated.  
`Tot mapped (mappable)`: Total mapped terms (that are mappable in Mondo). Includes exact, broad, and narrow mappings.  
`Tot unmapped (mappable)`: Total unmapped terms (that are mappable in Mondo)  
`% unmapped (mappable)`: % unmapped terms (that are mappable in Mondo)

To run the workflow that creates this data, refer to the [workflows documentation](../developer/workflows.md).