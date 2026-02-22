#!/usr/bin/env python3

import sys
import os
from pathlib import Path
import argparse
import textwrap
import yaml


def get_absolute_path(string: str, topdir: Path) -> Path:
    p = Path(string)
    if not p.is_absolute():
        p = topdir/p

    return p


def create_project_dir(cfg: dict):

    # Get toplevel working directory
    if "MYOMCPATH" not in os.environ:
        raise EnvironmentError("\nMYOMCPATH not set. Did you run 'env.sh'?\nAbort")
    topdir = os.environ.get("MYOMCPATH")
    cfg["topdir"] = Path(topdir)

    # Create project directory TOPDIR/SAMPLES/SAMPLE
    projectdir = Path(f"{topdir}/samples")
    projectdir.mkdir(parents=True, exist_ok=True)
    projectdir = projectdir/cfg["sample"]
    if projectdir.exists():
        raise FileExistsError(
            f"\nProject directory already exists: {projectdir}\nAborting"
        )
    projectdir.mkdir()
    cfg["projectdir"] = projectdir
    

def init_directories(cfg: dict):

    # Create project directory
    create_project_dir(cfg)

    # Set other paths
    cfg["campaigndir"] = cfg["topdir"]/Path("campaigns")/Path(cfg["campaign"])
    
    # List of all paths and files
    path_keys = ["topdir", "projectdir", "campaigndir", "gridpack", "fragment_lhe_producer", "fragment_shower"]
    file_keys = path_keys[3:]
    
    # Make file names absolute path objects
    for key in path_keys:
        cfg[key] = get_absolute_path( cfg[key], cfg["topdir"] )
    # Check if paths exist
    for key in path_keys:
        if not cfg[key].exists():
            raise FileExistsError(
                f"\n{cfg[key]} does not exist\nAborting"
            )
    # Check if files are regular files
    for key in file_keys:
        if not cfg[key].is_file():
            raise FileExistsError(
                f"\n{cfg[key]} is not a regular file\nAborting"
            )


def get_run_script_local(cfg: dict) -> str:
    projectdir = cfg["projectdir"]
    exe        = cfg["campaigndir"]/"run.sh"
    fragment   = cfg["fragment"]
    stub       = cfg["sample"]
    pufile     = cfg["campaigndir"]/"pileupinput.dat"

    script = f'echo "Changing to {projectdir}"\n'
    script = script+f"cd {projectdir}\n"
    script = script+f"{exe} {stub} {fragment} 10 1 1 {pufile}\n"
    
    return script


def get_run_script_condor(cfg: dict) -> str:
    projectdir  = cfg["projectdir"]
    exe         = "crun.py"
    stub        = cfg["sample"]
    fragment    = cfg["fragment"]
    campaign    = cfg["campaign"]
    mem         = cfg["mem"]
    job_flavour = cfg["job_flavour"]
    nevents     = cfg["nevents"]
    nevents_job = cfg["nevents_job"]
    njobs_chunk = cfg["njobs_chunk"]
    nevents_chunk = nevents_job*njobs_chunk
    nchunks     = int( nevents / nevents_chunk )
    if nchunks==0:
        nchunks=1

    script = f"TOPDIR=$PWD\n"
    script = script+f'echo "Changing to {projectdir}"\n'
    script = script+f"cd {projectdir}\n"
    for i in range(nchunks):
        seed_offset = i*njobs_chunk
        if i>0:
            script = script+f"sleep 5\n"
        script = script+f"{exe} {stub} {fragment} {campaign} --nevents_job {nevents_job} --njobs {njobs_chunk} --seed_offset {seed_offset} --keepNANO --env --mem {mem} --max_nthreads 1 --job_flavour {job_flavour}\n"
    script = script+"cd $TOPDIR\n"
    
    return script


def store_config(cfg: dict):
    """ Store configuration as yaml file"""
    with open(cfg["projectdir"]/"config.yaml", "w") as f:
        cfg_out = {}
        for key,val in cfg.items():
            if type(val) is str or type(val) is int:
                cfg_out[key] = val
            else:
                cfg_out[key] = str(val)
        yaml.safe_dump(cfg_out, f)



def pprint(text: str, is_list_item: bool=False):
    indent1 = "- " if is_list_item else ""
    indent2 = "  " if is_list_item else ""
    wrapped = textwrap.fill(
        text, width=100,
        initial_indent=indent1,
        subsequent_indent=indent2,
        replace_whitespace=False,
        break_long_words=True,    # force breaking long words
        break_on_hyphens=True     # allow breaking on hyphens
    )
    print(wrapped)


def run(cfg: dict):
    """Prepare single sample"""

    # Validate that all config parameters are set
    for key in ["sample", "campaign", "nevents", "nevents_job", "njobs_chunk", "mem", "job_flavour", "gridpack_placeholder_str", "gridpack", "fragment_lhe_producer", "fragment_shower"]:
        if key not in cfg.keys():
            raise KeyError(
                f"Config parameter '{key}' missing. Aborting"
            )
    
    # Initialize
    pprint(f"Preparing sample production for '{cfg['sample']}'")
    init_directories(cfg)
    pprint(f"sample     : {cfg['sample']}", is_list_item=True)
    pprint(f"campaign   : {cfg['campaign']}", is_list_item=True)
    pprint(f"gridpack   : {cfg['gridpack']}", is_list_item=True)
    pprint(f"shower     : {cfg['fragment_shower']}", is_list_item=True)
    
    # Prepare fragment
    # Read in templates as text and set gridpack location
    str_fragment_lhe_producer = cfg["fragment_lhe_producer"].read_text(encoding="utf-8")
    str_fragment_lhe_producer = str_fragment_lhe_producer.replace(
        cfg["gridpack_placeholder_str"],
        f'"{str(cfg["gridpack"])}"'
    )
    str_fragment_shower = cfg["fragment_shower"].read_text(encoding="utf-8")
    # Combine to full fragment as text
    str_fragment = str_fragment_lhe_producer + "\n\n" + str_fragment_shower
    # Store fragment in output file and path to fragment in cfg
    fragment = cfg["projectdir"]/"fragment.py"
    fragment.write_text(str_fragment, encoding="utf-8")
    cfg["fragment"] = fragment
    
    # Write local run script
    run_script_local = cfg["projectdir"]/"run_local.sh"
    run_script_local.write_text( get_run_script_local(cfg) )
    # Write condor run script
    run_script_condor = cfg["projectdir"]/"run_condor.sh"
    run_script_condor.write_text( get_run_script_condor(cfg) )

    # Store configuration
    store_config(cfg)
    
    # End
    pprint("\nDone")
    pprint(f"Prepared project directory '{cfg['projectdir'].relative_to(cfg['topdir'])}'")
    pprint(f"Execute test job with 'source {run_script_local.relative_to(cfg['topdir'])}'  (You may need to start first a Singularity session with the appropriate architecture, e.g. 'cmssw-el8' for Run3 samples)", is_list_item=True)
    pprint(f"Submit production to condor with 'source {run_script_condor.relative_to(cfg['topdir'])}'", is_list_item=True)
    print("")

    

def main():
    
    parser = argparse.ArgumentParser(
        description="Prepare sample production scripts."
    )
    parser.add_argument(
        "--config", type=str,
        help="YAML config file"
    )
    parser.add_argument(
        "--gridpacks", type=str,
        help="YAML file with list of 'sample: gridpack' pairs for multi-sample project"
    )
    parser.add_argument(
        "--sample", type=str,
        help="Name of the sample to prepare"
    )
    parser.add_argument(
        "--gridpack", type=str,
        help="Name of gridpack"
    )
    parser.add_argument(
        "--fragment", type=str,
        help="Name of shower fragment"
    )
    parser.add_argument(
        "--nevents", type=int,
        help="Number of events"
    )
    args = parser.parse_args()

    # Base config
    if args.config:
        # load config file
        with open(Path(args.config), "r") as f:
            cfg = yaml.safe_load(f)
    else:
        # create default config
        cfg = {
            "sample": "test",
            "campaign": "Run3Summer24wmLHEGS",
            "nevents": 10000,
            "nevents_job": 500,
            "njobs_chunk": 1000,
            "mem": 1250,
            "job_flavour": "workday",
            "gridpack_placeholder_str": "GRIDPACK",
            "gridpack": "/afs/cern.ch/user/m/mschrode/work/MYOMC__/test/GF_HHH_c3_0_d4_0_el8_amd64_gcc10_CMSSW_12_4_8_tarball.tar.xz",
            "fragment_lhe_producer": "fragments/fragment_lhe_producer.py",
            "fragment_shower": "fragments/fragment_Run3Summer24wmLHEGS_hhh_dl_c3_0_d4_0.py",
        }

    # Set (or overwrite) further config arguments if specified
    def set_cfg_argument(cfg, key, value):
        if value is not None:
            cfg[key] = value
    set_cfg_argument(cfg, "sample", args.sample)
    set_cfg_argument(cfg, "gridpack", args.gridpack)
    set_cfg_argument(cfg, "fragment_shower", args.fragment)
    set_cfg_argument(cfg, "nevents", args.nevents)

    # Run
    if args.gridpacks:
        # set up multi-sample config
        with open(Path(args.gridpacks), "r") as f:
            samples = yaml.safe_load(f)
            print("Preparing sample production for multiple gridpacks\n")
            for sample,gridpack in samples.items():
                cfg["sample"] = sample
                cfg["gridpack"] = gridpack
                run(cfg)
    else:
        # process config for single sample
        run(cfg)
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except EnvironmentError as e:
        print(e, file=sys.stderr)
        exit_code = 1
    except FileExistsError as e:
        print(e, file=sys.stderr)
        exit_code = 1
    except KeyError as e:
        print(e, file=sys.stderr)
        exit_code = 1
    sys.exit(exit_code)
