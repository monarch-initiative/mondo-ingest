# Mapping progress report
| Ontology                           | Tot terms   | Tot excluded   | Tot deprecated   | Tot deprecated unmapped   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-----------------------------------|:------------|:---------------|:-----------------|:--------------------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md) | 12,542      | 0              | 0                | 0                         | 12,542                                    | 18                        | 12,524                      | 99.9%                     |
| [ICD10CM](./unmapped_icd10cm.md)   | 95,847      | 15,452         | 0                | 0                         | 80,395                                    | 1,161                     | 79,234                      | 98.6%                     |
| [NCIT](./unmapped_ncit.md)         | 174,300     | 154,519        | 5,055            | 5,052                     | 14,726                                    | 3,681                     | 11,045                      | 75.0%                     |
| [GARD](./unmapped_gard.md)         | 12,004      | 0              | 0                | 0                         | 12,004                                    | 0                         | 12,004                      | 100.0%                    |
| [OMIM](./unmapped_omim.md)         | 28,890      | 19,021         | 1,358            | 1,314                     | 8,512                                     | 8,433                     | 79                          | 0.9%                      |
| [ORDO](./unmapped_ordo.md)         | 10,866      | 1,773          | 1,418            | 1,305                     | 9,093                                     | 9,029                     | 64                          | 0.7%                      |
| [DOID](./unmapped_doid.md)         | 13,791      | 2,643          | 2,477            | 2,473                     | 11,147                                    | 11,098                    | 49                          | 0.4%                      |

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