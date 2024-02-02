# Mapping progress report
| Ontology                           | Tot terms   | Tot excluded   | Tot deprecated   | Tot deprecated unmapped   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-----------------------------------|:------------|:---------------|:-----------------|:--------------------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md) | 12,542      | 0              | 0                | 0                         | 12,542                                    | 18                        | 12,524                      | 99.9%                     |
| [ICD10CM](./unmapped_icd10cm.md)   | 95,847      | 15,452         | 0                | 0                         | 80,395                                    | 1,161                     | 79,234                      | 98.6%                     |
| [NCIT](./unmapped_ncit.md)         | 187,170     | 166,382        | 5,166            | 5,154                     | 15,622                                    | 3,682                     | 11,940                      | 76.4%                     |
| [DOID](./unmapped_doid.md)         | 13,982      | 2,646          | 2,481            | 2,468                     | 11,334                                    | 11,084                    | 250                         | 2.2%                      |
| [GARD](./unmapped_gard.md)         | 12,004      | 0              | 0                | 0                         | 12,004                                    | 0                         | 12,004                      | 100.0%                    |
| [ORDO](./unmapped_ordo.md)         | 10,915      | 1,724          | 1,391            | 1,166                     | 9,191                                     | 9,025                     | 166                         | 1.8%                      |
| [OMIM](./unmapped_omim.md)         | 29,176      | 19,174         | 1,359            | 1,316                     | 8,644                                     | 8,611                     | 33                          | 0.4%                      |

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