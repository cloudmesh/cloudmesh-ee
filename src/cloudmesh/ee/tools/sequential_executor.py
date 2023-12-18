"""Sequential Executor

Usage:
  sequential_executor.py [--yaml=<yaml_file>] [--json=<json_file>] [--dryrun]
  sequential_executor.py -h | --help

Options:
  -h --help                Show this help message and exit.
  --yaml=<yaml_file>       Path to the YAML file [default: steps.yaml].
  --json=<json_file>       Path to the JSON file.
  --dryrun                 Perform a dry run without executing commands.

"""

import subprocess
import yaml
import json
import logging
from docopt import docopt

class SequentialExecutor:
    """
    A class for executing steps sequentially.

    Usage:
        executor = SequentialExecutor()
        executor.execute_with_yaml("example.yaml")
        executor.execute()

    Attributes:
        info (dict): Information about the execution.
        steps (list): List of steps to be executed.
        dryrun (bool): Flag indicating whether to perform a dry run.

    Methods:
        load_yaml(yaml_path): Load execution information from a YAML file.
        run(step, **kwargs): Execute a single run step with optional parameters.
        prepare(step): Execute a single prepare step.
        fetch(step): Execute a single fetch step.
        load_json(json_path): Load data from a JSON file.
        execute_with_json(json_path): Load and process data from a JSON file.
        execute_with_yaml(yaml_path): Load and execute steps from a YAML file.
        execute(): Execute all loaded steps.

    Example:
        executor = SequentialExecutor()
        executor.execute_with_yaml("example.yaml")
        executor.execute()
    """
    def __init__(self, dryrun=False):
        """
        Initialize the SequentialExecutor.

        Sets up logging and initializes attributes.

        Args:
            dryrun (bool): Flag indicating whether to perform a dry run.

        Example:
            executor = SequentialExecutor(dryrun=True)
        """
        self.info = {}
        self.steps = []
        self.dryrun = dryrun

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        logging.info("SequentialExecutor initialized")

    def load_yaml(self, yaml_path):
        """
        Load execution information from a YAML file.

        Args:
            yaml_path (str): Path to the YAML file.

        Example:
            executor.load_yaml("example.yaml")
        """
        logging.info("Loading YAML file: %s", yaml_path)
        with open(yaml_path, 'r') as file:
            data = yaml.safe_load(file)
            self.info = data.get('info', {})
            self.steps = data.get('steps', [])
        logging.info("YAML file loaded successfully")

    def run(self, step, **kwargs):
        """
        Execute a single run step with optional parameters.

        Args:
            step (dict): Run step information.
            **kwargs: Optional parameters to replace placeholders in the command.

        Example:
            executor.run({"name": "step1", "host": "localhost", "type": "run", "command": "echo '{parameters}'"}, parameters="Hello")
        """
        logging.info("Executing step: %s on host: %s", step['name'], step['host'])

        if self.dryrun:
            logging.info("Dryrun: Command not executed")
            return

        command = step['command']

        # Replace placeholders in the command with provided parameters
        for key, value in kwargs.items():
            command = command.replace(f'{{{key}}}', value)

        try:
            subprocess.run(command, shell=True, check=True)
            logging.info("Step '%s' completed successfully", step['name'])
        except subprocess.CalledProcessError:
            logging.error("Step '%s' failed", step['name'])

    def prepare(self, step):
        """
        Execute a single prepare step.

        Args:
            step (dict): Prepare step information.

        Example:
            executor.prepare({"name": "step1", "type": "prepare"})
        """
        logging.info("Preparing in step: %s", step['name'])
        # Add your preparation logic here

    def fetch(self, step):
        """
        Execute a single fetch step.

        Args:
            step (dict): Fetch step information.

        Example:
            executor.fetch({"name": "step1", "type": "fetch"})
        """
        logging.info("Fetching data in step: %s", step['name'])
        # Add your fetching logic here

    def load_json(self, json_path):
        """
        Load data from a JSON file.

        Args:
            json_path (str): Path to the JSON file.

        Returns:
            dict: Loaded JSON data.

        Example:
            json_data = executor.load_json("data.json")
        """
        logging.info("Loading JSON file: %s", json_path)
        with open(json_path, 'r') as json_file:
            json_data = json.load(json_file)
        logging.info("JSON file loaded successfully")
        return json_data

    def execute_with_json(self, json_path):
        """
        Load and process data from a JSON file.

        Args:
            json_path (str): Path to the JSON file.

        Example:
            executor.execute_with_json("data.json")
        """
        json_data = self.load_json(json_path)
        # Process the json_data as needed
        # For example, you can iterate through the data and perform actions

    def execute_with_yaml(self, yaml_path):
        """
         Load and execute steps from a YAML file.

         Args:
             yaml_path (str): Path to the YAML file.

         Example:
             executor.execute_with_yaml("example.yaml")
         """
        self.load_yaml(yaml_path)
        self.execute()

    def execute(self):
        """
        Execute all loaded steps.

        Example:
            executor.execute()
        """
        self.load_yaml()

        description = self.info.get('description', 'No description')
        author = self.info.get('author', 'Unknown')
        source = self.info.get('source', 'Unknown')

        logging.info("Description: %s", description)
        logging.info("Author: %s", author)
        logging.info("Source: %s", source)

        for step in self.steps:
            step_type = step.get('type', '')

            if step_type == 'run':
                parameters = step.get('parameters', '')  # Change to the parameter key you're using
                self.run(step, parameters=parameters)
            elif step_type == 'fetch':
                self.fetch(step)
            elif step_type == 'prepare':
                self.prepare(step)
            else:
                logging.warning("Unknown step type in step: %s", step['name'])

if __name__ == "__main__":
    args = docopt(__doc__)

    yaml_file = args['--yaml']
    json_file = args['--json']
    dryrun = args['--dryrun']

    executor = SequentialExecutor(dryrun)

    if yaml_file:
        executor.execute_with_yaml(yaml_file)

    if json_file:
        executor.execute_with_json(json_file)

    executor.execute()
