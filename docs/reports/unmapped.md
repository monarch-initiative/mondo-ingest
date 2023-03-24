# Mapping progress report
| Ontology                           | Tot terms   | Tot excluded   | Tot deprecated   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-----------------------------------|:------------|:---------------|:-----------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md) | 12,542      | 0              | 0                | 12,542                                    | 18                        | 12,524                      | 99.9%                     |
| [ICD10CM](./unmapped_icd10cm.md)   | 95,847      | 15,452         | 0                | 80,395                                    | 1,160                     | 79,235                      | 98.6%                     |
| [NCIT](./unmapped_ncit.md)         | 174,300     | 148,488        | 5,055            | 20,757                                    | 6,793                     | 13,964                      | 67.3%                     |
| [OMIM](./unmapped_omim.md)         | 28,154      | 18,928         | 1,230            | 7,996                                     | 7,622                     | 374                         | 4.7%                      |
| [ORDO](./unmapped_ordo.md)         | 10,866      | 1,718          | 1,418            | 9,148                                     | 8,934                     | 214                         | 2.3%                      |
| [DOID](./unmapped_doid.md)         | 13,689      | 2,626          | 2,473            | 11,062                                    | 9,727                     | 1,335                       | 12.1%                     |

`Ontology`: Name of ontology  
`Tot terms`: Total terms in ontology  
`Tot excluded`: Total terms Mondo has excluded from mapping / integrating  
`Tot deprecated`: Total terms that the ontology source itself has deprecated  
`Tot mappable (!excluded, !deprecated)`: Total mappable candidates for Mondo; all terms that are not excluded or 
deprecated.  
`Tot mapped (mappable)`: Total mapped terms (that are mappable in Mondo). Includes exact, broad, and narrow mappings.  
`Tot unmapped (mappable)`: Total unmapped terms (that are mappable in Mondo)  
`% unmapped (mappable)`: % unmapped terms (that are mappable in Mondo)  