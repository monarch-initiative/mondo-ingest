# Mapping progress report
| Ontology                                         | Tot terms   | Tot excluded   | Tot deprecated   | Tot deprecated unmapped   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-------------------------------------------------|:------------|:---------------|:-----------------|:--------------------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md)               | 12,542      | 0              | 0                | 0                         | 12,542                                    | 18                        | 12,524                      | 99.9%                     |
| [ICD10CM](./unmapped_icd10cm.md)                 | 95,847      | 15,452         | 0                | 0                         | 80,395                                    | 1,163                     | 79,232                      | 98.6%                     |
| [ICD11FOUNDATION](./unmapped_icd11foundation.md) | 57,713      | 0              | 5,594            | 5,594                     | 52,119                                    | 4,107                     | 48,012                      | 92.1%                     |
| [NCIT](./unmapped_ncit.md)                       | 191,123     | 169,937        | 5,221            | 5,216                     | 15,965                                    | 3,675                     | 12,290                      | 77.0%                     |
| [GARD](./unmapped_gard.md)                       | 12,004      | 0              | 0                | 0                         | 12,004                                    | 0                         | 12,004                      | 100.0%                    |
| [ORDO](./unmapped_ordo.md)                       | 15,561      | 6,270          | 1,424            | 1,257                     | 9,291                                     | 9,133                     | 158                         | 1.7%                      |
| [DOID](./unmapped_doid.md)                       | 14,096      | 2,656          | 2,484            | 2,474                     | 11,438                                    | 11,390                    | 48                          | 0.4%                      |
| [OMIM](./unmapped_omim.md)                       | 29,424      | 19,306         | 1,366            | 1,322                     | 8,753                                     | 8,752                     | 1                           | 0.0%                      |

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