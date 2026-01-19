#!/bin/bash

crun.py test $MYOMCPATH/test/fragment.py Run3Summer23wmLHE \
    --keepNANO \
    --nevents_job 10 \
    --njobs 2 \
    --env \
    --mem 1250 \
    --max_nthreads 1 \
    --job_flavour microcentury

# see `crun.py --help` for documentation of the options
