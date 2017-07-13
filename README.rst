.. image:: https://img.shields.io/docker/build/jrottenberg/ffmpeg.svg?style=flat-square   :target: https://hub.docker.com/r/fnndsc/pl-pacsretrieve/

 
docker run --rm -v $(pwd)/../pl-pacsquery/out2:/in -v $(pwd)/out:/out fnndsc/pl-pacsretrieve pacsretrieve.py --aet CHIPS --aec ORTHANC --aetListener CHIPS --seriesUIDS 0 --dataLocation /incoming