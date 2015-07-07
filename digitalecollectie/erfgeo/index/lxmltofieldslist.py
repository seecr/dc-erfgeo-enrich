from lxml.etree import _ElementTree

from weightless.core import asList
from meresco.core import Observable

from digitalecollectie.erfgeo.namespaces import namespaces, curieToTag


class LxmlToFieldsList(Observable):
    def add(self, lxmlNode, **kwargs):
        if type(lxmlNode) is _ElementTree:
            lxmlNode = lxmlNode.getroot()
        fieldslist = asList(fieldsFromAnnotation(lxmlNode))
        yield self.all.add(fieldslist=fieldslist, **kwargs)


def fieldsFromAnnotation(lxmlNode):
    for annotation in lxmlNode.getchildren():
        if not annotation.tag == curieToTag('oa:Annotation'):
            break
        for child in annotation.iterchildren():
            fieldname = namespaces.tagToCurie(child.tag)
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

    for name, value in (
            ('.uri', node.attrib.get(RDF_RESOURCE)),
            ('.uri', node.attrib.get(RDF_ABOUT)),
            ('', node.text)
        ):
        if value is None or value.strip() == '':
            continue
        yield fieldname + name, value
    for child in node.iterchildren():
        yield _yieldField(child, parent=fieldname)


RDF_RESOURCE = namespaces.curieToTag('rdf:resource')
RDF_ABOUT = namespaces.curieToTag('rdf:about')
IS_FORMAT_OF = namespaces.curieToTag('dcterms:isFormatOf')
MOTIVATED_BY = namespaces.curieToTag('oa:motivatedBy')
HAS_TARGET = namespaces.curieToTag('oa:hasTarget')
HAS_BODY = namespaces.curieToTag('oa:hasBody')
