###############
pl-pacsretrieve
###############

.. image:: https://img.shields.io/github/tag/fnndsc/pl-pacsretrieve.svg?style=flat-square   :target: https://github.com/FNNDSC/pl-pacsretrieve
.. image:: https://img.shields.io/docker/build/fnndsc/pl-pacsretrieve.svg?style=flat-square   :target: https://hub.docker.com/r/fnndsc/pl-pacsretrieve/


Abstract
========

A CUBE 'ds' plugin to retrieve DICOM data from a remote PACS.

A "preview.jpg" is added in each series directory for quick preview of the data.

Preconditions
=============

Data from the PACS must be pre-processed by ``pypx: listen``.


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
    --serverIP 192.168.1.40 --serverPort 4242 \
    --seriesUIDS 0 --dataLocation /incoming
    /input /output