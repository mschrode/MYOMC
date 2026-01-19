#!/bin/bash

STARTDIR=$PWD
mkdir testjob
cd testjob
source "$STARTDIR/../campaigns/Run3Summer23wmLHE/run.sh" test "$STARTDIR/fragment.py" 10 1 1 "$STARTDIR/../campaigns/Run3Summer23wmLHE/pileupinput.dat"
# Args are: name fragment_path nevents random_seed nthreads pileup_filelist
cd $STARTDIR
