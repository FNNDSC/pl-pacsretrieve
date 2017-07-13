#############
pl-pacsretrieve
#############

.. image:: https://img.shields.io/docker/build/jrottenberg/ffmpeg.svg?style=flat-square   :target: https://hub.docker.com/r/fnndsc/pl-pacsretrieve/



Abstract
========

A CUBE 'ds' plugin to retrieve DICOM data from a remote PACS.

A "preview.jpg" is added in each series directory for quick preview of the data.

Preconditions
=============

`fnndsc/dck-dicom-listener` to pre-process data from the PACS. See https://github.com/FNNDSC/ChRIS_ultron_backEnd/blob/master/docker-compose.yml#l62-L70 for more details.


Run
===
Using ``docker run``
--------------------

.. code-block:: bash

  docker run -t--rm
    -v $(pwd)/../pl-pacsquery/out:/input \
    -v $(pwd)/output:/output             \
    fnndsc/pl-pacsretrieve pacsretrieve.py
    --aet CHIPS --aec ORTHANC --aetListener CHIPS \
    --seriesUIDS 0 --dataLocation /incoming
    /input /output
