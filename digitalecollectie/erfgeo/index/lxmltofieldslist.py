## begin license ##
#
# "Digitale Collectie ErfGeo Enrichment" is a service that attempts to automatically create
# geographical enrichments for records in "Digitale Collectie" (http://digitalecollectie.nl)
# by querying the ErfGeo search API (https://erfgeo.nl/search).
# "Digitale Collectie ErfGeo Enrichment" is developed for Stichting DEN (http://www.den.nl)
# and the Netherlands Institute for Sound and Vision (http://instituut.beeldengeluid.nl/)
# by Seecr (http://seecr.nl).
# The project is based on the open source project Meresco (http://meresco.org).
#
# Copyright (C) 2015 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015 Stichting DEN http://www.den.nl
#
# This file is part of "Digitale Collectie ErfGeo Enrichment"
#
# "Digitale Collectie ErfGeo Enrichment" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Digitale Collectie ErfGeo Enrichment" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Digitale Collectie ErfGeo Enrichment"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from lxml.etree import _ElementTree

from weightless.core import asList
from meresco.core import Observable

from digitalecollectie.erfgeo.namespaces import namespaces, curieToTag, tagToCurie


class LxmlToFieldsList(Observable):
    def add(self, lxmlNode, **kwargs):
        if type(lxmlNode) is _ElementTree:
            lxmlNode = lxmlNode.getroot()
        fieldslist = asList(fieldsFromAnnotation(lxmlNode))
        yield self.all.add(fieldslist=fieldslist, **kwargs)


def fieldsFromAnnotation(lxmlNode):
    for annotation in lxmlNode.getchildren():
        if annotation.tag == curieToTag('oa:Annotation'):
            for child in annotation.iterchildren():
                fieldname = tagToCurie(child.tag)
                if child.tag != HAS_BODY:
                    yield fieldname + ".uri", child.attrib.get(RDF_RESOURCE)
                else:
                    bodyNode = child.getchildren()[0]
                    for bodyChildNode in bodyNode.iterchildren():
                        yield _yieldField(bodyChildNode)

def _yieldField(node, parent=''):
    fieldname = namespaces.tagToCurie(node.tag)
    if fieldname != 'rdf:Description' and fieldname != 'rdf:type':
        if parent:
            parent += "."
        fieldname = parent + fieldname
    else:
        fieldname = parent

    for postfix, value in (
            ('.uri', node.attrib.get(RDF_RESOURCE)),
            ('.uri', node.attrib.get(RDF_ABOUT)),
            ('', node.text)
        ):
        if value is None or value.strip() == '':
            continue
        yield fieldname + postfix, value
    for child in node.iterchildren():
        yield _yieldField(child, parent=fieldname)


RDF_RESOURCE = namespaces.curieToTag('rdf:resource')
RDF_ABOUT = namespaces.curieToTag('rdf:about')
IS_FORMAT_OF = namespaces.curieToTag('dcterms:isFormatOf')
MOTIVATED_BY = namespaces.curieToTag('oa:motivatedBy')
HAS_TARGET = namespaces.curieToTag('oa:hasTarget')
HAS_BODY = namespaces.curieToTag('oa:hasBody')
