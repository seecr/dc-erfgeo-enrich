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
# "Digitale Collectie ErfGeo Enrichment" is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# "Digitale Collectie ErfGeo Enrichment" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Digitale Collectie ErfGeo Enrichment".  If not, see <http://www.gnu.org/licenses/>.
#
## end license ##

from os import walk, listdir
from os.path import join, relpath
from distutils.core import setup


data_files = []
for path, dirs, files in walk('doc'):
    data_files.append((path.replace('doc', '/usr/share/doc/dc-erfgeo-enrich', 1), [join(path, f) for f in files if f != 'license.conf']))
for path, dirs, files in walk('sbin'):
    data_files.append((path.replace('sbin', '/sbin', 1), [join(path, f) for f in files]))

binScripts = [join('bin', f) for f in listdir('bin')]

version = '$Version: trunk$'[9:-1].strip()

def packageData(basedir):
    extensions = ['css', 'eot', 'gif', 'htc', 'html', 'jpg', 'js', 'json', 'owl', 'png', 'rdf', 'sf', 'svg', 'swf', 'ttf', 'txt', 'woff', 'xslt', 'xsd']
    result = []
    for path, subdirs, files in walk(basedir):
        result.extend(join(relpath(path, basedir), f) for f in files if f.rsplit('.', 1)[-1] in extensions)
    return result

setup(
    name='dc-erfgeo-enrich',
    packages = [
        'digitalecollectie',
        'digitalecollectie.erfgeo',
    ],
    scripts = binScripts,
    package_data = {
        'digitalecollectie.erfgeo': packageData('digitalecollectie/erfgeo'),
    },
    data_files=data_files,
    version=version,
    url='http://natag.dev.seecr.nl',
    author='Seecr',
    author_email='info@seecr.nl',
    maintainer='Seecr',
    maintainer_email='info@seecr.nl',
    description='Digitale Collectie ErfGeo Enrichment is a service that attempts to automatically create geographical enrichments for records in Digitale Collectie (http://digitalecollectie.nl) by querying the ErfGeo search API (https://erfgeo.nl/search)',
    long_description="Digitale Collectie ErfGeo Enrichment is a service that attempts to automatically create geographical enrichments for records in Digitale Collectie (http://digitalecollectie.nl) by querying the ErfGeo search API (https://erfgeo.nl/search). Digitale Collectie ErfGeo Enrichment is developed for Stichting DEN (http://www.den.nl) and the Netherlands Institute for Sound and Vision (http://instituut.beeldengeluid.nl/) by Seecr (http://seecr.nl). The project is based on the open source project Meresco (http://meresco.org).",
    license='GNU Public License',
    platforms='all',
)
