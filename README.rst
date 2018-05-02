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
  docker run -t --rm
    -v /tmp:/tmp \
    fnndsc/pl-pacsretrieve pacsretrieve.py \
                  --pfdcm ${HOST_IP}:5015         \
                  --PACSservice orthanc           \
                  --pfurlQuiet                    \
                  --priorHitsTable results.json   \
                  --indexList 1,2,3               \
    /tmp/query /tmp/data
