# Cloudmesh ee

A general purpose HPC Template and Experiment management system


## Background

Hyper Performance Computation Clusters (HPCs) are designed around a
timesharing principle and are powered by queue-based execution
ecosystems such as SchedMD's
[SLURM](https://slurm.schedmd.com/overview.html) and IBM's Platform
Load Sharing Facility
([LSF](https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=overview-lsf-introduction)).
While these ecosystems provide a great deal of control and extension
for planning, scheduling, and batching jobs, they are limited in their
ability to support parameterization in a scheduled task.  While there
are facilities in place to execute jobs on an Array, the ability to do
permutation based experments are limited to what you integrate into
your own batch script.  Even then, parameterization of values are only
made availabile as environment variables, which can be limited
depending on your OS or selected programming language.  In many cases
limitations set by the deployment trhough the compute center also
hinder optimal use while restrictions are placed on duration and
number of parallel accessible resources. In some cases these
restrictions are soo established that removing them is impractical and
takes weks to implement on temporary basis.

Cloudmesh Experiment Executor (ee) is a framework that wraps the SLURM 
batch processor into a templated framework such that experiments can 
be generated based on configuration files focusing on the livecycle 
of generating many permutations of experiments with standard tooling, 
so that you can focus more on modeling your experiments than how to 
orchestrate them with tools.  A number of batch scripts can be 
generated that than can be executed according to center policies.

## Dependencies

When you install cloudmesh-ee, you will also be installing a
minimum baseline of the `cms` command (as part of the Cloudmesh
ecosystem).  For more details on Cloudmesh, see its documentation on
[read the docs](https://cloudmesh.github.io/cloudmesh-manual/). However
all instalation can be done thorugh pip. After instalation, you will
need to initialize cloudmesh with the command

```bash
$ cms help
```

While SLURM is not needed to run the `cloudmesh ee` command, the
generated output will not execute unless your system has slurm installed
and you are able to run jobs via the `slurm sbatch` command.

## Documentation

### Running Cloudmesh ee

The `cloudmesh ee` command takes one of two forms of execution.  It is started with 

```bash
$ cms ee <command> <parameters>
```

Where the command invokes a partiuclar action and parameters include a
number of parameters for the command These commands allow you to
inspect the generated output to confirm your parameterization
functions as expected and as intended.

In general, configuration arguments that appear in multiple locations are
prioritized in the following order (highest priority first)

1. CLI Arguments with `cms ee`
2. Configuration Files
3. Preset values

### Generating Experiments with the CLI

The `generate` command is used to generate your experiments based upon either a passed
configuration file, or via CLI arguments.  You can issue the command using
either of the below forms:

```text
cms ee generate SOURCE --name=NAME [--verbose] [--mode=MODE] [--config=CONFIG] [--attributes=PARAMS] [--out=DESTINATION] [--dryrun] [--noos] [--nocm] [--dir=DIR] [--experiment=EXPERIMENT]
cms ee generate --setup=FILE [SOURCE] [--verbose] [--mode=MODE]  [--config=CONFIG] [--attributes=PARAMS] [--out=DESTINATION] [--dryrun] [--noos] [--nocm] [--dir=DIR] [--experiment=EXPERIMENT] [--name=NAME]
```

If you have prepared a configuration file that conforms to the schema
defined in [Setup Config](#setup-config), then you can use the second
form which overrides the default values.

* `--name=NAME` - Supplies a name for this experiment.  Note that the name
  must not match any existing files or directories where you are currently
  executing the command
* `--verbose` - Enables additional logging useful when troubleshooting the
  program.
* `--mode=MODE` - specifies how the output should be generated.  One of: f,h,d.
  * `f` or `flat` - specifies a "flat" mode, where slurm scripts are generated in a flattened structure, all in one directory.
  * `h` or `hierarchical` - specifies a "hierarchical" mode, where experiments are nested into unique directories from each other.
  * `d` or `debug` - instructs the command to not generate any output.
* `--config=CONFIG` - specifies key-value pairs to be used across all files for substitution.  This can be a python, yaml, or json file.
* `--attributes=PARAMS` - specifies key-value pairs that can be listed at the command line and used as substitution across all experiments.  Note this command leverages [cloudmesh's parameter expansion specification](https://cloudmesh.github.io/cloudmesh-manual/autoapi/cloudmeshcommon/cloudmesh/common/parameter/index.html) for different types of expansion rules.
* `--out=DESTINATION` - specifies the directory to write the generated scripts out to.
* `--dryrun` - Runs the command without performing any operations
* `--noos` - Prevents the interleaving of OS environemnt variables into the subsitution logic
* `--dir=DIR` - specifies the directory to write the generated scripts out to.
* `--experiment=EXPERIMENT` - specifies a listing of key-value parameters that establish a unique experiment for each combination of values (a cartisian product across all values for each key).

* `--setup=FILE` - provides all the above configuration options within a configuration
  file to simplify executions.

### Form 2 - Generating Submission Scripts

```text
ee generate submit --name=NAME [--verbose]
```

This command uses the output of the
[generate command](#command-1---generating-experiments) and generates
a shell script that can be used to submit your previously generated
outputs to SLURM as a sequence of sbatch commands.

* `--name=NAME` - specifies the name used in the
  [generate command](#command-1---generating-experiments).
  The generate command will inspect the `<NAME>.json` file and build the
  necessary commands to run all permutations that the cloudmesh ee
  command generated.

Note that this command only generates the script, and you must run the
outputted file in your shell for the commands to be issued to SLURM and
run your jobs.


**Sample YAML File**

This command requires a YAML file which is configured for the host and gpu.
The YAML file also points to the desired slurm template.

```yaml
slurm_template: 'slurm_template.slurm'

ee_setup:
  <hostname>-<gpu>:
    - card_name: "a100"
    - time: "05:00:00"
    - num_cpus: 6
    - num_gpus: 1

  rivanna-v100:
    - card_name: "v100"
    - time: "06:00:00"
    - num_cpus: 6
    - num_gpus: 1

```

example:

```
cms ee slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a=1,b=4  --noos --dir=example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\"
ee slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --noos --dir=example --experiment="epoch=[1-3] x=[1,4] y=[10,11]"
# ERROR: Importing python not yet implemented
epoch=1 x=1 y=10  sbatch example/slurm.sh
epoch=1 x=1 y=11  sbatch example/slurm.sh
epoch=1 x=4 y=10  sbatch example/slurm.sh
epoch=1 x=4 y=11  sbatch example/slurm.sh
epoch=2 x=1 y=10  sbatch example/slurm.sh
epoch=2 x=1 y=11  sbatch example/slurm.sh
epoch=2 x=4 y=10  sbatch example/slurm.sh
epoch=2 x=4 y=11  sbatch example/slurm.sh
epoch=3 x=1 y=10  sbatch example/slurm.sh
epoch=3 x=1 y=11  sbatch example/slurm.sh
epoch=3 x=4 y=10  sbatch example/slurm.sh
epoch=3 x=4 y=11  sbatch example/slurm.sh
Timer: 0.0022s Load: 0.0013s ee slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --noos --dir=example --experiment="epoch=[1-3] x=[1,4] y=[10,11]"
```

## Slurm on a single computer ubuntu 20.04

### Install 

see https://drtailor.medium.com/how-to-setup-slurm-on-ubuntu-20-04-for-single-node-work-scheduling-6cc909574365

32 Processors (threads)

```bash
sudo apt update -y
sudo apt install slurmd slurmctld -y

sudo chmod 777 /etc/slurm-llnl

# make sure to use the HOSTNAME

sudo cat << EOF > /etc/slurm-llnl/slurm.conf
# slurm.conf file generated by configurator.html.
# Put this file on all nodes of your cluster.
# See the slurm.conf man page for more information.
#
ClusterName=localcluster
SlurmctldHost=$HOSTNAME
MpiDefault=none
ProctrackType=proctrack/linuxproc
ReturnToService=2
SlurmctldPidFile=/var/run/slurmctld.pid
SlurmctldPort=6817
SlurmdPidFile=/var/run/slurmd.pid
SlurmdPort=6818
SlurmdSpoolDir=/var/lib/slurm-llnl/slurmd
SlurmUser=slurm
StateSaveLocation=/var/lib/slurm-llnl/slurmctld
SwitchType=switch/none
TaskPlugin=task/none
#
# TIMERS
InactiveLimit=0
KillWait=30
MinJobAge=300
SlurmctldTimeout=120
SlurmdTimeout=300
Waittime=0
# SCHEDULING
SchedulerType=sched/backfill
SelectType=select/cons_tres
SelectTypeParameters=CR_Core
#
#AccountingStoragePort=
AccountingStorageType=accounting_storage/none
JobCompType=jobcomp/none
JobAcctGatherFrequency=30
JobAcctGatherType=jobacct_gather/none
SlurmctldDebug=info
SlurmctldLogFile=/var/log/slurm-llnl/slurmctld.log
SlurmdDebug=info
SlurmdLogFile=/var/log/slurm-llnl/slurmd.log
#
# COMPUTE NODES # THis machine has 128GB main memory
NodeName=$HOSTNAME CPUs=32 RealMemory==128762 State=UNKNOWN
PartitionName=local Nodes=ALL Default=YES MaxTime=INFINITE State=UP
EOF

sudo chmod 755 /etc/slurm-llnl/
```

### Start
```
sudo systemctl start slurmctld
sudo systemctl start slurmd
# sudo scontrol update nodename=$HOSTNAME state=idle
sudo scontrol update nodename=$HOSTNAME state=resume
```

### Stop

```
sudo systemctl stop slurmd
sudo systemctl stop slurmctld
```

### Info

```
sinfo
sinfo -R
sinfo -a
```

### Job

save into gregor.slurm

```
#!/bin/bash

#SBATCH --job-name=gregors_test          # Job name
#SBATCH --mail-type=END,FAIL             # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --mail-user=laszewski@gmail.com  # Where to send mail	
#SBATCH --ntasks=1                       # Run on a single CPU
####  XBATCH --mem=1gb                        # Job memory request
#SBATCH --time=00:05:00                  # Time limit hrs:min:sec
#SBATCH --output=sgregors_test_%j.log    # Standard output and error log

pwd; hostname; date

echo "Gregors Test"
date
sleep(30)
date
```

Run with 

```
sbatch gregor.slurm
watch -n 1 squeue
```

BUG

```
JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
                 2    LocalQ gregors_    green PD       0:00      1 (Nodes required for job are DOWN, DRAINED or reserved for jobs in higher priority partitions)

```

### sbatch slurm management commands for localhost

start slurm daemons

```bash
cms ee slurm start
```

stop surm deamons

```bash
cms ee slurm stop
```

BUG:

```bash
srun gregor.slurm

srun: Required node not available (down, drained or reserved)
srun: job 7 queued and waiting for resources
```

```
sudo scontrol update nodename=localhost state=POWER_UP

Valid states are: NoResp DRAIN FAIL FUTURE RESUME POWER_DOWN POWER_UP UNDRAIN

```

### Cheatsheet

* <https://slurm.schedmd.com/pdfs/summary.pdf>

## Acknowledgements

Continued work was in part funded by the NSF
CyberTraining: CIC: CyberTraining for Students and Technologies
from Generation Z with the awadrd numbers 1829704 and 2200409.



## Manual Page

<!-- START-MANUAL -->
```
Command ee
==========

::

  Usage:
        ee generate submit --name=NAME [--job_type=JOB_TYPE] [--verbose]
        ee generate --source=SOURCE --name=NAME
                        [--out=OUT]
                        [--verbose]
                        [--mode=MODE]
                        [--config=CONFIG]
                        [--attributes=PARAMS]
                        [--output_dir=OUTPUT_DIR]
                        [--dryrun]
                        [--noos]
                        [--os=OS]
                        [--nocm]
                        [--source_dir=SOURCE_DIR]
                        [--experiment=EXPERIMENT]
                        [--flat]
                        [--copycode=CODE]
        ee list [DIRECTORY]
        ee slurm start
        ee slurm stop
        ee slurm info
        ee seq --yaml=YAML|--json=JSON

  Expermine Executor (ee) allows the creation of parameterized batch
  scripts. The initial support includes slurm, but we intend
  also to support LSF. Parameters can be specified on the
  commandline or in configuration files. Configuration files
  can be formulated as json,yaml, python, or jupyter
  notebooks.

  Parameters defined in this file are then used in the slurm
  batch script and substituted with their values. A special
  parameter called experiment defines a number of variables
  that are permuted on when used allowing multiple batch
  scripts to be defined easily to conduct parameter studies.

  Please note that the setup flag is deprecated and is in
  future versions fully covered while just using the config
  file.

  Arguments:
      FILENAME       name of a slurm script generated with ee
      CONFIG_FILE    yaml file with configuration
      ACCOUNT        account name for host system
      SOURCE         name for input script slurm.in.sh, lsf.in.sh,
                     script.in.sh or similar
      PARAMS         parameter lists for experimentation
      GPU            name of gpu

  Options:
      -h                        help
      --copycode=CODE           a list including files and directories to be copied into the destination dir
      --config=CONFIG...        a list of comma seperated configuration files in yaml or json format.
                                The endings must be .json or .yaml
      --type=JOB_TYPE           The method to generate submission scripts.
                                One of slurm, lsf. [default: slurm]
      --attributes=PARAMS       a list of coma separated attribute value pairs
                                to set parameters that are used. [default: None]
      --output_dir=OUTPUT_DIR   The directory where the result is written to
      --source_dir=SOURCE_DIR   location of the input directory [default: .]
      --account=ACCOUNT         TBD
      --gpu=GPU                 The name of the GPU. Tyoically k80, v100, a100, rtx3090, rtx3080
      --noos                    ignores environment variable substitution from the shell. This
                                can be helpfull when debugging as the list is quite lareg
      --nocm                    cloudmesh as a variable dictionary build in. Any vaiable referred to
                                by cloudmesh. and its name is replaced from the
                                cloudmesh variables
      --experiment=EXPERIMENT   This specifies all parameters that are used to create
                                permutations of them.
                                They are comma separated key value pairs
      --mode=MODE               one of "debug", "hierachical". One can also just
                                use "d", "h" [default: h]
      --name=NAME               Name of the experiment configuration file
      --os=OS                   Selected OS variables
      --flat                    produce flatdict
      --dryrun                  flag to do a dryrun and not create files and
                                directories [default: False]
      --verbose                 Print more information when executing [default: False]

  Description:

    > Examples:
    >
    > cms ee generate slurm.in.sh --verbose \\
    >     --config=a.py,b.json,c.yaml \\
    >     --attributes=a=1,b=4 \\
    >     --dryrun --noos --input_dir=example \\
    >     --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" \\
    >     --name=a --mode=h
    >
    > cms ee generate slurm.in.sh \\
    >    --config=a.py,b.json,c.yaml \\
    >    --attributes=a=1,b=4 \\
    >    --noos \\
    >    --input_dir=example \\
    >    --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" \\
    >    --name=a \\
    >    --mode=h
    >            >
    > cms ee generate slurm.in.sh --experiments-file=experiments.yaml --name=a
    >
    > cms ee generate submit --name=a

```
<!-- STOP-MANUAL -->