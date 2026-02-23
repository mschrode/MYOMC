# Make your own MC

This repository provides scripts to run private MC generation. It consists of the exact same cmsDriver.py commands used in central production (...painstaking copied by hand from MCM). It is a fork from [gabhijith's fork](https://github.com/gabhijith/MYOMC) of [DryRun's MYOMC](https://github.com/DryRun/MYOMC).

Setup instructions:
```
git clone git@github.com:mschrode/MYOMC.git
cd MYOMC
source firsttime.sh
# For future sessions, run env.sh
```

Run a test job locally
```
cd MYOMC/test
source run_test_local.sh
```
or submit to the CERN batch system
```
cd MYOMC/test
source run_test_condor.sh
```
See the test scripts for syntax examples.


Prepare a larger sample campaign:
```
python3 prepare_sample_production.py --config configs/example_config.yaml
```
or with multiple gridpacks and otherwise same settings (e.g. for different signal parameter settings)
```
python3 prepare_sample_production.py --config configs/example_config.yaml --gridpacks configs/example_multigridpack_config.yaml
```
See the examples in `configs` for the configuration options.