# Mapping progress report
| Ontology                           | Tot terms   | Tot excluded   | Tot deprecated   | Tot deprecated unmapped   | Tot mappable _(!excluded, !deprecated)_   | Tot mapped _(mappable)_   | Tot unmapped _(mappable)_   | % unmapped _(mappable)_   |
|:-----------------------------------|:------------|:---------------|:-----------------|:--------------------------|:------------------------------------------|:--------------------------|:----------------------------|:--------------------------|
| [ICD10WHO](./unmapped_icd10who.md) | 12,542      | 0              | 0                | 0                         | 12,542                                    | 18                        | 12,524                      | 99.9%                     |
| [ICD10CM](./unmapped_icd10cm.md)   | 95,847      | 15,452         | 0                | 0                         | 80,395                                    | 1,161                     | 79,234                      | 98.6%                     |
| [NCIT](./unmapped_ncit.md)         | 174,300     | 148,488        | 5,055            | 5,022                     | 20,757                                    | 7,033                     | 13,724                      | 66.1%                     |
| [DOID](./unmapped_doid.md)         | 13,699      | 2,628          | 2,475            | 2,447                     | 11,070                                    | 10,518                    | 552                         | 5.0%                      |
| [ORDO](./unmapped_ordo.md)         | 10,866      | 1,718          | 1,418            | 844                       | 9,148                                     | 9,024                     | 124                         | 1.4%                      |
| [OMIM](./unmapped_omim.md)         | 28,750      | 18,958         | 1,353            | 1,309                     | 8,439                                     | 8,433                     | 6                           | 0.1%                      |

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