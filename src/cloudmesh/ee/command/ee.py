import pathlib

import cloudmesh.ee.tools.sequential_executor
from cloudmesh.common.Shell import Shell
from cloudmesh.common.console import Console
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.util import banner
from cloudmesh.ee.experimentexecutor import ExperimentExecutor
from cloudmesh.ee.slurm import Slurm
from cloudmesh.shell.command import PluginCommand
from cloudmesh.shell.command import command
from cloudmesh.shell.command import map_parameters
from cloudmesh.common.parameter import Parameter


class EeCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_ee(self, args, arguments):
        r"""
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

        """

        map_parameters(arguments,
                       "verbose",
                       "source",
                       "name",
                       "out",
                       "mode",
                       "config",
                       "attributes",
                       "output_dir",
                       "source_dir",
                       "experiment",
                       "account",
                       "yaml",
                       "json",
                       "filename",
                       "gpu",
                       "copycode",
                       "os",
                       "job_type",
                       "flat",
                       "dryrun")

        verbose = arguments["--verbose"]
        if verbose:
            banner("experiment batch generator")


        if arguments.seq or arguments.sequential:

            Console.warning("THIS IS JUST A NON FUNCTIONING EXAMPLE")

            yaml_file = args['--yaml']
            json_file = args['--json']

            from cloudmesh.ee.tools.sequential_executor import SequentialExecutor

            executor = SequentialExecutor()

            if yaml_file:
                executor.execute_with_yaml(yaml_file)

            if json_file:
                executor.execute_with_json(json_file)

            executor.execute()

        if arguments.slurm:
            if arguments.start:
                Slurm.start()
            elif arguments.stop:
                Slurm.stop()
            elif arguments.info:
                Slurm.status()

            return ""

        if arguments.name is not None:
            if not arguments.name.endswith(".json"):
                arguments.name = arguments.name + ".json"

        if verbose:
            VERBOSE(arguments)

        if arguments.generate and arguments.submit:

            #  ee generate submit --name=NAME [--job_type=JOB_TYPE] [--verbose]

            ee = ExperimentExecutor()
            ee.verbose = arguments.verbose
            job_type = arguments.job_type or "slurm"
            ee.generate_submit(name=arguments.name, job_type=job_type)

            return ""

        elif arguments.list:
                
                directory = arguments.DIRECTORY or "project"
    
                ee = ExperimentExecutor()
                ee.list(directory)
    
                return ""   
        elif arguments.generate:

            ee = ExperimentExecutor()

            # CLI arguments override the experiments

            ee.dryrun = arguments.dryrun or False
            ee.verbose = arguments.verbose or False
            ee.execution_mode = arguments.mode or "h"
            ee.name = arguments.name
            ee.source = arguments.source
            ee.input_dir = str(Shell.map_filename(arguments["source_dir"]).path)
            ee.output_dir = str(Shell.map_filename(arguments["output_dir"]).path)
            ee.script_in = f"{ee.input_dir}/{ee.source}"
            ee.copycode = Parameter.expand(arguments.copycode)

            #
            # set source and name
            #

            ee.name = arguments.name
            ee.source = arguments.source
            ee.source = ExperimentExecutor.update_with_directory(ee.input_dir,
                                                         ee.source)
            #
            # set output_script
            #
            if arguments.out is None:
                ee.script_out = pathlib.Path(ee.source).name.replace(".in.", ".")  # .replace(".in", "")
            else:
                ee.script_out = pathlib.Path(arguments.get('out', ee.script_out)).name
            ee.script_out = ExperimentExecutor.update_with_directory(ee.output_dir, ee.script_out)

            #
            # make sure output script is not input script
            #
            if ee.source == ee.script_out:
                Console.error("The source and destination filenames are the same.", traceflag=True)
                return ""

            #
            # LOAD TEMPLATE
            #
            ee.load_source_template(ee.source)

            # order of replace is defined by
            # config
            # os
            # cm
            # attributes

            if arguments.config:

                # ok create list of config files
                try:
                    ee.config_files = arguments.config.split(",")
                    ee.config_files = [ExperimentExecutor.update_with_directory(ee.input_dir, filename) for filename in
                                           ee.config_files]
                except Exception as e:
                    print(e)

                #
                # GENERATE THE REPLACEMENTS
                #

                for config_file in ee.config_files:
                    ee.update_from_file(config_file)

            if arguments.os:
                ee.os_variables = (arguments.os).split(",")
                ee.update_from_os(ee.os_variables)

            if not arguments["--noos"]:
                ee.update_from_os_environ()

            # replace variables from cm
            if not arguments["--nocm"]:
                ee.update_from_cm_variables()

            # expriments from commandline overwrites experiments in configs

            # if "experiment" in ee.data:
            #     try:
            #         d = ee.data["experiment"]
            #         print ("EEEEE", d, ee.permutation_generator(d))
            #         ee.experiment = ee.permutation_generator(d)
            #     except:
            #         pass

            if arguments.experiment:
                ee.experiments = arguments.experiment
                ee.experiment = ee.generate_experiment_permutations(ee.experiments)

            #
            #
            # result = ee.get_data(flat=arguments.flat)
            #
            # experiments = result["experiment"]
            # for e in experiments:
            #     experiments[e] = Parameter.expand(experiments[e])
            #
            # ee.permutations = ee.permutation_generator(experiments)

            # MOVE TO END
            #
            # ADD ADDITIONAL ATTRIBUTES
            #
            # move to last
            # if arguments.attributes:
            #    ee.attributes = arguments.attributes
            #    ee.update_from_attributes(arguments.attributes)

            ee.info()

            ee.generate_experiment_batch_scripts()

            ee.save_experiment_configuration(name=arguments.name)

            return ""

            # ee.config_from_cli(arguments)

            # ee.mode = arguments.mode
            # content = readfile(ee.source)

            # if ee.dryrun or verbose:
            #     banner("Configuration")
            #     print(ee.debug_state(key=".."))
            #     print()
            #     banner(f"Original Script {ee.source}")
            #     print(ee.template_content)
            #     banner("end script")
            # result = ee.generate(ee.template_content)
            #
            # if ee.dryrun or verbose:
            #     banner("Expanded Script")
            #     print(result)
            #     banner("Script End")
            # else:
            #     writefile(ee.script_out, result)
            #
            # ee.generate_experiment_batch_scripts()
            #
            # ee.save_experiment_configuration(name=arguments.name)

        return ""
