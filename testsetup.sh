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
# Copyright (C) 2011-2013, 2015 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2011-2013, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

set -e
mydir=$(cd $(dirname $0); pwd)

rm -rf tmp build

python2.6 setup.py install --root tmp
cp -r test tmp/test
find tmp -type f -exec sed -e \
    "/DO_NOT_DISTRIBUTE/d;
    s,^natagPackageDir\s\?=.*$,natagPackageDir = '$mydir/tmp/usr/lib/python2.6/site-packages/natag',;
    s,^documentationDir\s\?=.*$,documentationDir = '$mydir/tmp/usr/share/doc/natag',;
    s,binDir\s\?=.*$,binDir = '$mydir/tmp/usr/bin',;
    s,^usrShareDir\s\?=.*$,usrShareDir = '$mydir/tmp/usr/share/natag',;
    s,^usrSharePath\s\?=.*$,usrSharePath = '$mydir/tmp/usr/share/natag',;
    " -i {} \;

export PYTHONPATH=`pwd`/tmp/usr/lib/python2.6/site-packages
teststorun=$1
if [ -z "$teststorun" ]; then
    teststorun="alltests.sh integrationtest.sh"
else
    shift
fi

echo "Will now run the tests:"
for f in $teststorun; do
    echo "- $f"
done
echo "Press [ENTER] to continue"
read

for testtorun in $teststorun; do
    (
    cd tmp/test
    ./$testtorun "$@"
    )
    echo "Finished $testtorun, press [ENTER] to continue"
    read
done

rm -rf tmp build
