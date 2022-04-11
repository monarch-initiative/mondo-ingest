prefix oio: <http://www.geneontology.org/formats/oboInOwl#>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
prefix xref: <http://www.geneontology.org/formats/oboInOwl#hasDbXref>

#### https://github.com/monarch-initiative/omim/issues/45

DELETE {
  ?entity owl:equivalentClass ?value .
}
WHERE 
{
  VALUES ?entity {
    <http://omim.org/entry/146910>
    <http://omim.org/entry/147010>
    <http://omim.org/entry/147070>
    <http://omim.org/entry/300015>
    <http://omim.org/entry/300151>
    <http://omim.org/entry/300162>
    <http://omim.org/entry/300357>
    <http://omim.org/entry/306250>
    <http://omim.org/entry/308385>
    <http://omim.org/entry/312095>
    <http://omim.org/entry/312865>
    <http://omim.org/entry/313470>
    <http://omim.org/entry/400011>
    <http://omim.org/entry/400020>
    <http://omim.org/entry/400023>
    <http://omim.org/entry/402500>
    <http://omim.org/entry/403000>
    <http://omim.org/entry/425000>
    <http://omim.org/entry/430000>
    <http://omim.org/entry/450000>
    <http://omim.org/entry/465000>
    <http://omim.org/entry/609517>
    <http://omim.org/entry/610067>
  }
  ?entity owl:equivalentClass ?value .
  FILTER (isIRI(?value) && STRSTARTS(STR(?value),"https://www.ncbi.nlm.nih.gov/gene/"))
}
