import itertools
import json
import os
import pathlib
import typing
import uuid
from collections import OrderedDict
from datetime import datetime
from pprint import pprint
from tqdm import tqdm
import shutil
import yaml
from nbconvert.exporters import PythonExporter
import humanize

from cloudmesh.common.util import readfile
from cloudmesh.rivanna.rivanna import Rivanna
from cloudmesh.common.FlatDict import FlatDict
from cloudmesh.common.Printer import Printer
from cloudmesh.common.Shell import Shell
from cloudmesh.common.console import Console
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.util import banner, writefile
from cloudmesh.common.variables import Variables
from cloudmesh.common.dotdict import dotdict

PathLike = typing.Union[str, pathlib.Path]
DictOrList = typing.Union[dict, list]
OptPath = typing.Optional[PathLike]
OptStr = typing.Optional[str]


class ExperimentExecutor:

    # def config_read(self, path="./config.yaml"):
    #     print (path)
    #     return None

    def __init__(self, verbose=False):
        """Initialize the ExperimentExecutor Object

        Args:
            verbose (bool): If true prints additional infromation when
                ExperimentExecutor methods are called
        """
        self.flat = FlatDict({}, sep=".")
        self.data = dict()
        self.permutations = list()
        self.experiments = None
        self.dryrun = False
        self.verbose = False
        self.execution_mode = "h"
        self.input_dir = str(Shell.map_filename(".").path)
        self.output_dir = str(Shell.map_filename(".").path)
        self.os_variables = None
        self.verbose = verbose
        self.template_path = None
        self.template_content = None
        self.configuration_parameters = None
        self.script_out = None
        # self.gpu = None
        self.copycode = None

  

    def list(self, directory="project", config="config.yaml", debug=False, verbose=True):
        """Lists all experiments

        Returns:
            None: prints the experiments
        """

        banner(f"List Experiments in {directory}/*/{config}")
        experiments = []

        if verbose:
            num_entries = sum(1 for entry in os.scandir(directory) if entry.is_dir())
            progress_bar = tqdm(total=num_entries, desc="Processing", ncols=70)  # Set ncols to 70

        for entry in os.scandir(directory):
            if entry.is_dir():
                config_dir = f"{directory}/{entry.name}"
                config_file = f"{config_dir}/{config}"
                if debug:
                    print(config_file)
                content = yaml.safe_load(readfile(config_file))
                content = content["experiment"]
                # space = Shell.calculate_disk_space(config_dir)
                content["space"] = Shell.calculate_disk_space(config_dir)
                content["space"] = humanize.naturalsize(content["space"])

                experiments.append(content)
            if verbose:
                progress_bar.update(1)
        if verbose:
            progress_bar.close()

        print(Printer.write(experiments))
    import shutil

    def info(self, verbose=None):
        """Prints information about the ExperimentExecutor object for debugging purposes

        Args:
            verbose (bool): if True prints even more information

        Returns:
            None: None
        """
        verbose = verbose or self.verbose

        if not verbose:
            return

        for a in [
            "dryrun",
            "verbose",
            "name",
            "source",
            "destination",
            "attributes",
            "gpu",
            "config",
            "config_files",
            "directory",
            "experiment",
            "execution_mode",
            "template",
            "script_output",
            "output_dir",
            "input_dir",
            "script_in",
            "script_out",
            "os_variables",
            "experiments",
            "copy"
        ]:
            # noinspection PyBroadException
            try:
                result = getattr(self, a)
            except:  # noqa: E722
                result = self.data.get(a)
            print(f'{a:<12}: {result}')
        print("permutations:")

        result = getattr(self, "permutations")
        pprint(result)

        print("BEGIN FLAT")
        pprint(self.flat)
        print("END FLAT")
        print()

        print("BEGIN DATA")
        pprint(self.data)
        print("END DATA")
        print()

        print("BEGIN YAML")
        spec = yaml.dump(self.data, indent=2)
        print(spec)
        print("END YAML")

        print("BEGIN SPEC")
        spec = self.spec_replace(spec)
        print(spec)
        print("END SPEC")
        print("BEGIN PERMUTATION")
        p = self.permutations
        pprint(p)
        print("END PERMUTATION")

        # self.info()
        #
        # self.data = result
        #
        print("BEGIN DATA")
        pprint(self.data)
        print("END DATA")

        banner("BEGIN TEMPLATE")
        print(self.template_content)
        banner("END TEMPLATE")

    @staticmethod
    def update_with_directory(directory, filename):
        """prefix with the directory if the filename is not starting with . / ~

        Args:
            directory (str): the string value of the directory
            filename (str): the filename

        Returns:
            str: directory/filename
        """
        if directory is None:
            return filename
        elif not filename.startswith("/") and not filename.startswith(".") and not filename.startswith("~"):
            return f"{directory}/{filename}"
        else:
            return filename

    def get_data(self, flat=False):
        """converts the data from the yaml file with the flatdict

        Args:
            flat (boolen): if set to true uses flatdict

        Returns:
            dict: result of flatdict without the seperator
        """
        result = self.data

        if flat:
            from cloudmesh.common.FlatDict import FlatDict
            result = FlatDict(self.data, sep=".")
            del result["sep"]

        return result

    def spec_replace(self, spec):
        """given a spec in yaml format, replaces all values in the yaml file that
        are of the form "{a.b}" with the value of

        a:
           b: value

        if it is defined in the yaml file

        Args:
            spec (str): yaml string

        Returns:
            str: replaced yaml file
        """

        banner("SPECIFICATION")
        print(spec)

        data = FlatDict()
        data.loads(spec)

        banner("FLATDICT")
        pprint(data.__dict__)

        spec1 = str(data.__dict__)
        print(str(spec1[1:-1]))

        banner("MUNCH")
        #
        # should be replaced with flatdct aplied on config.yaml file
        #
        import re
        import munch
        variables = re.findall(r"\{\w.+\}", spec)
        data = yaml.load(spec, Loader=yaml.SafeLoader)


        m = munch.DefaultMunch.fromDict(data)

        for o in range(0,4):
            for i in range(0, len(variables)):

                for variable in variables:
                    text = variable
                    variable = variable[1:-1]
                    # noinspection PyBroadException
                    try:
                        value = eval("m.{variable}".format(**locals()))
                        if "{" not in value:
                            spec = spec.replace(text, value)
                    except:  # noqa: E722
                        value = variable

        banner("END MUNCH")
        return spec

    def update_from_os(self, variables):
        """LOads all variables from os.environ into self.data with os.name

        Args:
            variables ([str]): the name of the variables such as "HOME"

        Returns:
            dict: self.data with all variaples added with os.name: value
        """
        if variables is not None:
            if os not in self.data:
                self.data["os"] = {}
            for key in variables:
                self.data["os"][key] = os.environ[key]
        return self.data

    def load_source_template(self, script):
        """Registers and reads the template script in for processing

        This method must be run at least once prior to generating the batch script output.

        Args:
            script (str): A string that is the path to the template
                script.

        Returns:
            str: The text of the template file unaltered.
        """
        self.template_path = script
        self.template_content = readfile(script)
        return self.template_content

    def update_from_dict(self, d):
        """Add a dict to self. data

        Args:
            d (dict): dictionary

        Returns:
            dict: self.data with updated dict
        """
        self.data.update(d)
        return self.data

    def update_from_attributes(self, attributes: str):
        """attributes are of the form "a=1,b=3"

        Args:
            attributes: A string to expand into key-value pairs

        Returns:
            dict: self.data with updated dict
        """
        flatdict = Parameter.arguments_to_dict(attributes)

        d = FlatDict(flatdict, sep=".")
        d = d.unflatten()
        del d["sep"]

        self.update_from_dict(d)
        return self.data

    def update_from_os_environ(self):
        """Updates the config file output to include OS environment variables

        Returns:
            dict: The current value of the data configuration variable
        """
        self.update_from_dict(dict(os.environ))
        return self.data

    def update_from_cm_variables(self, load=True):
        """Adds Cloudmesh variables to the class's data parameter as a flat dict.

        Args:
            load (bool): Toggles execution; if false, method does
                nothing.

        Returns:
            dict: self.data with updated cloudmesh variables
        """
        if load:
            variables = Variables()
            v = FlatDict({"cloudmesh": variables.dict()}, sep=".")
            d = v.unflatten()
            del d["sep"]
            self.update_from_dict(d)
        return self.data

    @staticmethod
    def _suffix(filename):
        """
        Args:
            filename (str): Returns the file suffix of a filename

        Returns:
            str: the suffix of the filename
        """
        return pathlib.Path(filename).suffix

    def update_from_file(self, filename):
        """Updates the configuration self.data with the data within the passed file.

        Args:
            filename (str): The path to the configuration file (yaml,
                json, py, ipynb)

        Returns:
            dict: self.data with updated cloudmesh variables from the
            specified file
        """
        if self.verbose:
            print(f"Reading variables from {filename}")

        suffix = self._suffix(filename).lower()
        content = readfile(filename)

        if suffix in [".json"]:
            values = json.loads(content)

        elif suffix in [".yml", ".yaml"]:
            content = readfile(filename)
            values = yaml.safe_load(content)

        elif suffix in [".py"]:

            modulename = filename.replace(".py", "").replace("/", "_").replace("build_", "")
            from importlib.machinery import SourceFileLoader

            mod = SourceFileLoader(modulename, filename).load_module()

            values = {}
            for name, value in vars(mod).items():
                if not name.startswith("__"):
                    values[name] = value

        elif suffix in [".ipynb"]:

            py_name = filename.replace(".ipynb", ".py")
            jupy = PythonExporter()
            body, _ = jupy.from_filename(filename)
            writefile(py_name, body)
            # Shell.run(f"jupyter nbconvert --to python {filename}")

            filename = py_name
            modulename = filename.replace(".py", "").replace("/", "_").replace("build_", "")
            from importlib.machinery import SourceFileLoader

            mod = SourceFileLoader(modulename, filename).load_module()

            values = {}
            for name, value in vars(mod).items():
                if not name.startswith("__"):
                    values[name] = value

        else:
            raise RuntimeError(f"Unsupported config type {suffix}")

        self.update_from_dict(values)

        # self.read_config_from_dict(regular_dict)
        if values is not None and 'experiment' in values:
            experiments = values['experiment']

            for key, value in experiments.items():
                print(key, value)
                # noinspection PyBroadException,PyPep8
                try:
                    experiments[key] = Parameter.expand(value)
                except:
                    experiments[key] = [value]

            self.permutations = self.permutation_generator(experiments)

        return self.data

    def generate(self, script=None, variables=None, fences=("{", "}")):
        """Expands the script template given the passed configuration.

        Args:
            script (str): The string contents of the script file.
            variables (dict): the variables to be replaced, if ommitted
                uses the internal variables found
            fences ((str,str)): A 2 position tuple, that encloses
                template variables (start and end).

        Returns:
            str: The script that has expanded its values based on
            `data`.
        """

        replaced = {}

        if variables is None:
            variables = self.data
        if script is None:
            script = self.template_content
        content = str(script)
        flat = FlatDict(variables, sep=".")

        for attribute in flat:
            value = flat[attribute]
            frame = fences[0] + attribute + fences[1]
            if frame in content:
                if self.verbose:
                    print(f"- Expanding {frame} with {value}")
                replaced[attribute] = value
                content = content.replace(frame, str(value))
        return content, replaced

    @staticmethod
    def permutation_generator(exp_dict):
        """Creates a cartisian product of a {key: list, ...} object.

        Args:
            exp_dict (dict): The dictionary to process

        Returns:
            list: A list of dictionaries containing the resulting
            cartisian product.

        For example
            my_dict = {"key1": ["value1", "value2"], "key2": ["value3", "value4"]}
            out = permutation_generator(my_dict)
            out # [{"key1": "value1", "key2": 'value3"},
                #  {"key1": "value1", "key2": "value4"},
                #  {"key1": "value2", "key2": "value3"},
                #  {"key1": "value2", "key2": "value4"}

        """
        keys, values = zip(*exp_dict.items())
        return [dict(zip(keys, value)) for value in itertools.product(*values)]

    def generate_experiment_permutations(self, variable_str):
        """Generates experiment permutations based on the passed string and appends it to the current instance.

        Args:
            variable_str (str): A Parameter.expand string (such as
                epoch=[1-3] x=[1,4] y=[10,11])

        Returns:
            list: list with permutations over the experiment variables
        """
        experiments = OrderedDict()
        entries = variable_str.split(' ')

        for entry in entries:
            k, v = entry.split("=")
            experiments[k] = Parameter.expand(v)
        self.permutations = self.permutation_generator(experiments)
        return self.permutations

    @staticmethod
    def _generate_bootstrapping(permutation):
        """creates an identifier, a list of assignments, ad values.

        Args:
            permutation (list): the permutation list

        Returns:
            str, list, list: identifier, assignments, values
        """
        values = list()
        for attribute, value in permutation.items():
            values.append(f"{attribute}_{value}")
        assignments = list()
        for attribute, value in permutation.items():
            assignments.append(f"{attribute}={value}")
        assignments = " ".join(assignments)

        identifier = "_".join(values)
        return identifier, assignments, values

    def _generate_hierarchical_config(self):
        """Creates a hierarchical directory with configuration yaml files, and shell script

        Returns:
            dict: directory with configuration and yaml files
        """
        """Runs process to build out all templates in a hierarchical-style

        Returns:
            None.

        Side Effects:
            Writes two files for each established experiment, each in their own directory.

        """
        if self.verbose:
            print("Outputting Hierarchical Experiments")
        configuration = dict()
        self.script_variables = []
        suffix = self._suffix(self.script_out)
        directory = self.output_dir  # .path.dirname(name)
        for permutation in self.permutations:

            identifier, assignments, values = self._generate_bootstrapping(permutation)

            if self.verbose:
                print(identifier, assignments, values)

            spec = yaml.dump(self.data, indent=2)
            spec = self.spec_replace(spec)
            print (type(spec))

            variables = yaml.safe_load(spec)

            print ("VARIABLES")
            pprint (variables)
            print ("END VARIABLES")

            name = os.path.basename(self.script_out)
            script = f"{directory}/{identifier}/{name}"
            config = f"{directory}/{identifier}/config.yaml"

            variables.update({'experiment': permutation})
            variables["ee"]["identifier"] = identifier

            configuration[identifier] = {
                "id": identifier,
                "directory": f"{directory}/{identifier}",
                "experiment": assignments,
                "script": script,
                "config": config,
                "variables": variables,
                "copycode": self.copycode
            }
        return configuration

    def generate_experiment_batch_scripts(self, out_mode=None, replace_all=True):
        """Utility method to genrerate either hierarchical or flat outputs; or debug.

        NOte the falt mode is no longer supported

        Args:
            out_mode (string): The mode of operation.  One of: "debug",
                "flat", "hierarchical"

        Returns:
            None: generates the batch scripts
        """
        mode = self.execution_mode if out_mode is None else out_mode.lower()
        if mode.startswith("d"):
            Console.warning("This is just debug mode")
            print()
            for permutation in self.permutations:
                values = ""
                for attribute, value in permutation.items():
                    values = values + f"{attribute}={value} "
                script = f"{self.output_dir}/{self.script_out}{values}".replace("=", "_")
        else:
            configuration = None
            if mode.startswith("h"):
                configuration = self._generate_hierarchical_config()
            else:
                raise RuntimeError(f"Invalid generator mode {mode}")
            if self.verbose:
                banner("Script generation")

            print(Printer.write(configuration, order=["id", "experiment", "script", "config", "directory"]))

            self.configuration_parameters = configuration

            self.generate_setup_from_configuration(configuration, replace_all)

    def generate_submit(self, name=None, job_type='slurm'):
        """Generates a list of commands based on the permutations for submission

        Args:
            name (str): Name of the experiments
            job_type (str): name of the job type used at submission such
                as ee, slurm, jsrun, mpirun, sh, bash

        Returns:
            None: prepars the internal data for the experiments, if set
            to verbose, prints them
        """

        if ".json" not in name:
            name = f"{name}.json"

        if job_type == 'slurm':
            cmd = 'sbatch'
        elif job_type == 'lsf':
            cmd = 'bsub'
        else:
            cmd = job_type

        # else:
        #    raise RuntimeError(f"Unsupported submission type {type_}")

        experiments = json.loads(readfile(name))

        #  print (experiments)

        if experiments is None:
            Console.error("please define the experiment parameters")
            return ""

        for entry in experiments:
            if self.verbose:
                print(f"# Generate {entry}")
            experiment = experiments[entry]
            parameters = experiment["experiment"]
            directory = experiment["directory"]
            script = os.path.basename(experiment["script"])
            print(f"{parameters} cd {directory} && {cmd} {script}")

    def generate_setup_from_configuration(self, configuration, replace_all=True):
        """generates a setup directory from the configuration parameters

        Args:
            configuration (dict): the configuration dict

        Returns:

        """
        for identifier in configuration:
            experiment = configuration[identifier]
            Shell.mkdir(experiment["directory"])
            if self.verbose:
                print()
                Console.info(f"Setup experiment {identifier}")
                print(f"- Making dir {experiment['directory']}")
                print(f"- write file {experiment['config']}")

            # Generate UUID for each perm
            experiment["variables"]['ee']['uuid'] = str(uuid.uuid4())

            #
            # CREATE SLURM SBATCH PARAMETERS FORM A KEY based on experiment.card_name
            #
            host = experiment["variables"]["system"]["host"]

            if "cardname" in experiment["variables"]["experiment"]:
                key = experiment["variables"]["experiment"]["card_name"]
                rivanna = Rivanna(host=host)

                experiment["variables"]["slurm"] = {
                    "directive": rivanna.directive[host][key],
                    "sbatch": rivanna.create_slurm_directives(host=host, key=key).strip()
                }
            elif experiment["variables"]["experiment"]["directive"]:
                directive = experiment["variables"]["experiment"]["directive"]
                rivanna = Rivanna(host=host)

                experiment["variables"]["slurm"] = {
                    "sbatch": rivanna.create_slurm_directives(host=host, key=directive).strip()
                }
                if "-" in directive:
                    experiment["variables"]["experiment"]["card_name"] = directive.split("-")[0]
                else:
                    experiment["variables"]["experiment"]["card_name"] = directive

            #
            # END GENERATE SLURM SBATCH
            #

            writefile(experiment["config"], yaml.dump(experiment["variables"], indent=2))
            content_config = readfile(experiment["config"])
            try:
                check = yaml.safe_load(content_config)
            except Exception as e:
                print(e)
                Console.error("We had issues with our check for the config.yaml file")

            content_script, replaced = self.generate(
                self.template_content,
                variables=experiment["variables"])

            # if self.verbose:
            #    for attribute, value in replaced.items():
            #        print (f"- replaced {attribute}={value}")

            writefile(experiment["script"], content_script)
            if self.copycode is not None:
                for code in self.copycode:
                    Shell.copy_source(source=code, destination=experiment["directory"])
            try:
                if replace_all:
                    c = FlatDict()
                    c.load(experiment["config"])
                    c.apply(experiment["script"])
                    c.apply(experiment["config"])
            except Exception as e:
                print (e)
                raise ValueError
    @property
    def now(self):
        """The time of now in the format "%Y-m-%d"

        Returns:
            str: "%Y-m-%d"
        """
        return datetime.now().strftime("%Y-m-%d")

    def save_experiment_configuration(self, name=None):
        """Saves the experiment configuration in a json file

        Args:
            name (str): name of the configuration file

        Returns:
            None: writes into the file with given name the json content
        """
        if name is not None:
            content = json.dumps(self.configuration_parameters, indent=2)
            writefile(name, content)

