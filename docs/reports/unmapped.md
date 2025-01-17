# Mapping progress report
| Ontology                                         | Tot terms   | Tot excluded   | Tot deprecated   | Tot deprecated unmapped   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-------------------------------------------------|:------------|:---------------|:-----------------|:--------------------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md)               | 12,542      | 0              | 0                | 0                         | 12,542                                    | 18                        | 12,524                      | 99.9%                     |
| [ICD10CM](./unmapped_icd10cm.md)                 | 95,847      | 15,452         | 0                | 0                         | 80,395                                    | 1,166                     | 79,229                      | 98.5%                     |
| [ICD11FOUNDATION](./unmapped_icd11foundation.md) | 57,713      | 0              | 5,594            | 5,594                     | 52,119                                    | 4,108                     | 48,011                      | 92.1%                     |
| [NCIT](./unmapped_ncit.md)                       | 191,123     | 169,937        | 5,221            | 5,216                     | 15,965                                    | 3,839                     | 12,126                      | 76.0%                     |
| [ORDO](./unmapped_ordo.md)                       | 15,632      | 6,310          | 1,444            | 1,273                     | 9,322                                     | 9,195                     | 127                         | 1.4%                      |
| [DOID](./unmapped_doid.md)                       | 14,220      | 2,661          | 2,489            | 2,478                     | 11,557                                    | 11,455                    | 102                         | 0.9%                      |
| [OMIM](./unmapped_omim.md)                       | 29,596      | 19,414         | 1,370            | 1,325                     | 8,813                                     | 8,759                     | 54                          | 0.6%                      |

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