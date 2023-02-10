# Mapping progress report
| Ontology                           | Tot terms   | Tot excluded   | Tot deprecated   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-----------------------------------|:------------|:---------------|:-----------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md) | 12,542      | 0              | 0                | 12,542                                    | 18                        | 12,524                      | 99.9%                     |
| [ICD10CM](./unmapped_icd10cm.md)   | 95,847      | 15,452         | 0                | 80,395                                    | 1,160                     | 79,235                      | 98.6%                     |
| [NCIT](./unmapped_ncit.md)         | 174,300     | 155,232        | 5,055            | 19,068                                    | 6,734                     | 12,334                      | 64.7%                     |
| [OMIM](./unmapped_omim.md)         | 28,659      | 17,286         | 1,345            | 10,028                                    | 9,779                     | 249                         | 2.5%                      |
| [ORDO](./unmapped_ordo.md)         | 9,448       | 292            | 0                | 9,156                                     | 8,934                     | 222                         | 2.4%                      |
| [DOID](./unmapped_doid.md)         | 13,648      | 2,599          | 2,467            | 11,048                                    | 9,748                     | 1,300                       | 11.8%                     |

`Ontology`: Name of ontology  
`Tot terms`: Total terms in ontology  
`Tot excluded`: Total terms Mondo has excluded from mapping / integrating  
`Tot deprecated`: Total terms that the ontology source itself has deprecated  
`Tot mappable (!excluded, !deprecated)`: Total mappable candidates for Mondo; all terms that are not excluded or 
deprecated.  
`Tot mapped (mappable)`: Total mapped terms (that are mappable in Mondo). Includes exact, broad, and narrow mappings.  
`Tot unmapped (mappable)`: Total unmapped terms (that are mappable in Mondo)  
`% unmapped (mappable)`: % unmapped terms (that are mappable in Mondo)  