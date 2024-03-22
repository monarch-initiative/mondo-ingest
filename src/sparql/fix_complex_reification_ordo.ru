prefix oio: <http://www.geneontology.org/formats/oboInOwl#>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
prefix xref: <http://www.geneontology.org/formats/oboInOwl#hasDbXref>
prefix efo: <http://www.ebi.ac.uk/efo/>
prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
prefix skos: <http://www.w3.org/2004/02/skos/core#>
prefix obo: <http://purl.obolibrary.org/obo/>


#<owl:Axiom>
#    <owl:annotatedSource>
#        <owl:Axiom>
#            <owl:annotatedSource rdf:resource="http://www.orpha.net/ORDO/Orphanet_10"/>
#            <owl:annotatedProperty rdf:resource="&oboInOwl;hasDbXref"/>
#            <owl:annotatedTarget rdf:datatype="&xsd;string">ICD-10:Q98.8</owl:annotatedTarget>
#            <obo:ECO_0000218 xml:lang="en">Attributed (The ICD10 code is attributed by Orphanet)</obo:ECO_0000218>
#        </owl:Axiom>
#    </owl:annotatedSource>
#    <owl:annotatedProperty rdf:resource="&obo;ECO_0000218"/>
#    <owl:annotatedTarget xml:lang="en">Attributed (The ICD10 code is attributed by Orphanet)</owl:annotatedTarget>
#    <obo:ECO_0000218 xml:lang="en">NTBT (ORPHA code&apos;s Narrower Term maps to a Broader Term)</obo:ECO_0000218>
#</owl:Axiom>

DELETE {
  ?anno rdf:type owl:Annotation ;
     owl:annotatedSource ?nested ;
     owl:annotatedProperty <http://purl.obolibrary.org/obo/ECO_0000218> ;
     owl:annotatedTarget ?target ;
     <http://purl.obolibrary.org/obo/ECO_0000218> ?precision_value .
    
    ?nested rdf:type owl:Axiom ;
       owl:annotatedSource ?entity ;
       owl:annotatedProperty <http://www.geneontology.org/formats/oboInOwl#hasDbXref> ;
       owl:annotatedTarget ?xref ;
       <http://purl.obolibrary.org/obo/ECO_0000218> ?attribution .
}
INSERT {
   [ a owl:Axiom ;
   owl:annotatedSource ?entity ;
   owl:annotatedProperty ?property ;
   owl:annotatedTarget ?xref ;
   obo:ECO_0000218 ?precision_value ]
}
WHERE 
{
  ?anno rdf:type owl:Annotation ;
     owl:annotatedSource ?nested ;
     owl:annotatedProperty <http://purl.obolibrary.org/obo/ECO_0000218> ;
     owl:annotatedTarget ?target ;
     <http://purl.obolibrary.org/obo/ECO_0000218> ?precision_value .
    
    ?nested rdf:type owl:Axiom ;
       owl:annotatedSource ?entity ;
       owl:annotatedProperty <http://www.geneontology.org/formats/oboInOwl#hasDbXref> ;
       owl:annotatedTarget ?xref ;
       <http://purl.obolibrary.org/obo/ECO_0000218> ?attribution .
  
  FILTER (isIRI(?entity) && (regex(str(?entity), "http://www.orpha.net/ORDO/")))
  BIND(IF(STRSTARTS(str(?precision_value), "NTBT"), skos:narrowMatch, IF(STRSTARTS(str(?precision_value), "BTNT"), skos:broadMatch, oboInOwl:hasDbXref)) as ?property)
}
