# Digitale Collectie ErfGeo Enrichment service

The 'Digitale Collectie ErfGeo Enrichment service' takes metadata records from selected collections in [Digitale Collectie](http://digitalecollectie.nl) and attempts to enrich them with geo-coordinates (if not present already), using the [HistoGraph.io](http://histograph.io) API. These enrichments (OpenAnnotation in rdf/xml) are accessible through OAI-PMH and can be queried through a JSON(-LD) search API. These APIs are described at http://erfgeo.data.digitalecollectie.nl

## Installation

A version of this service is running at http://erfgeo.data.digitalecollectie.nl.

For that purpose it was packaged to be installed on the RHEL 6 server on which Digitale Collectie itself runs, which is located at the Netherlands Institute for Sound and Vision. The [`deps.txt`](https://github.com/seecr/dc-erfgeo-enrich/blob/master/deps.txt) file lists the packages (including required versions) this service depends on. The source code for all of these packages is freely available, much of it at http://github.com/seecr
