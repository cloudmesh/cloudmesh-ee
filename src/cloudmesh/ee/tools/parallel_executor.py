"""Parallel Executor with Dependencies

Usage:
  parallel_executor.py <yaml_file>
  parallel_executor.py -h | --help

Options:
  -h --help           Show this help message and exit.
"""

import subprocess
import yaml
import json
import concurrent.futures
import logging
from docopt import docopt

class ParallelExecutor:
    """
    A class for executing steps in parallel with dependencies.

    Usage:
        executor = ParallelExecutor()
        executor.execute_with_yaml("example.yaml")
        executor.execute()

    Attributes:
        info (dict): Information about the execution.
        steps (list): List of steps to be executed.
        dependencies (dict): Dependencies between steps.

    Methods:
        load_yaml(yaml_path): Load execution information from a YAML file.
        load_json(json_path): Load execution information from a JSON file.
        execute_step(step): Execute a single step.
        execute_with_yaml(yaml_path): Load and execute steps from a YAML file.
        execute(): Execute all loaded steps.

    Example:
        executor = ParallelExecutor()
        executor.execute_with_yaml("example.yaml")
        executor.execute()
    """
    def __init__(self):
        """
        Initialize the ParallelExecutor.

        Sets up logging and initializes attributes.

        Example:
            executor = ParallelExecutor()
        """
        self.info = {}
        self.steps = []
        self.dependencies = {}

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        logging.info("ParallelExecutor initialized")

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
            self.dependencies = {step['name']: step.get('dependencies', []) for step in self.steps}
        logging.info("YAML file loaded successfully")

    def load_json(self, json_path):
        """
        Load execution information from a JSON file.

        Args:
            json_path (str): Path to the JSON file.

        Example:
            executor.load_json("example.json")
        """
        logging.info("Loading JSON file: %s", json_path)
        with open(json_path, 'r') as file:
            data = json.load(file)
            self.info = data.get('info', {})
            self.steps = data.get('steps', [])
            self.dependencies = {step['name']: step.get('dependencies', []) for step in self.steps}
        logging.info("JSON file loaded successfully")

    def execute_step(self, step):
        """
        Execute a single step.

        Args:
            step (dict): Step information.

        Example:
            executor.execute_step({"name": "step1", "host": "localhost", "command": "echo 'Hello, World!'"})
        """
        logging.info("Executing step: %s on host: %s", step['name'], step['host'])
        command = step['command']

        try:
            subprocess.run(command, shell=True, check=True)
            logging.info("Step '%s' completed successfully", step['name'])
        except subprocess.CalledProcessError:
            logging.error("Step '%s' failed", step['name'])

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

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.steps)) as executor:
            future_to_step = {executor.submit(self.execute_step, step): step for step in self.steps}
            concurrent.futures.wait(future_to_step)
            for future in concurrent.futures.as_completed(future_to_step):
                step = future_to_step[future]
                logging.info("Step '%s' completed", step['name'])


if __name__ == "__main__":
    args = docopt(__doc__)

    file_path = args['<file>']
    use_json = args['--json']

    executor = ParallelExecutor()

    if use_json:
        executor.load_json(file_path)
    else:
        executor.execute_with_yaml(file_path)

    executor.execute()
