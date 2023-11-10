# Mapping progress report
| Ontology                           | Tot terms   | Tot excluded   | Tot deprecated   | Tot deprecated unmapped   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-----------------------------------|:------------|:---------------|:-----------------|:--------------------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md) | 12,542      | 0              | 0                | 0                         | 12,542                                    | 18                        | 12,524                      | 99.9%                     |
| [ICD10CM](./unmapped_icd10cm.md)   | 95,847      | 15,452         | 0                | 0                         | 80,395                                    | 1,160                     | 79,235                      | 98.6%                     |
| [NCIT](./unmapped_ncit.md)         | 187,170     | 166,382        | 5,166            | 5,155                     | 15,622                                    | 3,680                     | 11,942                      | 76.4%                     |
| [GARD](./unmapped_gard.md)         | 12,004      | 0              | 0                | 0                         | 12,004                                    | 0                         | 12,004                      | 100.0%                    |
| [ORDO](./unmapped_ordo.md)         | 11,001      | 1,827          | 1,470            | 1,470                     | 9,174                                     | 0                         | 9,174                       | 100.0%                    |
| [DOID](./unmapped_doid.md)         | 13,863      | 2,642          | 2,477            | 2,469                     | 11,219                                    | 11,088                    | 131                         | 1.2%                      |
| [OMIM](./unmapped_omim.md)         | 29,054      | 19,096         | 1,359            | 1,314                     | 8,600                                     | 8,518                     | 82                          | 1.0%                      |

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