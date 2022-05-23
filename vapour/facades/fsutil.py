import itertools
import os
import shutil
import subprocess
from abc import ABC, abstractclassmethod, abstractproperty, abstractmethod
from typing import List, Sequence

from .apps import App
from .config import ConfigMixin
from .logging import LoggingMixin


class AbstractFsTool(ABC):
    """All tools must have a method for determining availability."""

    @abstractclassmethod
    def is_available(cls) -> bool:
        return True or False


class AbstractExternalFsTool(AbstractFsTool, App):
    """All external tools are commands with options."""

    @abstractproperty
    def executable(self) -> str:
        return 'command'

    @abstractproperty
    def options(self) -> List[str]:
        return ['--option1=value1', '-o', 'value2']

    @classmethod
    def is_available(cls) -> bool:
        result = subprocess.run(
            ['which', cls.executable],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        try:
            result.check_returncode()
            return True
        except subprocess.CalledProcessError:
            # If which result is non-zero then executable not in path
            return False


# --------------------------------------------------------------------
# Clone tools
# --------------------------------------------------------------------
class AbstractCloneTool(AbstractFsTool):

    @abstractmethod
    def clone(self, source, destination):
        return


class AbstractExternalCloneTool(AbstractExternalFsTool, AbstractCloneTool):

    def clone(self, source, destination, options=None):
        if options is None:
            options = self.options
        elif isinstance(options, list):
            options = options
        else:
            self.log.error(f"options parameter must be a list or None")

        result = subprocess.run(
            [self.executable]
            + options
            + [source]
            + [destination],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        result.check_returncode()
        return result


class Rsync(AbstractExternalCloneTool):
    executable = 'rsync'
    options = ['-azP']


class Rclone(AbstractExternalCloneTool):
    executable = 'rclone'
    options = ['copy'] #, '--multi-thread-streams=12']

    def clone(self, source, destination):
        source = os.path.normpath(source)
        source_basename = os.path.basename(source)
        destination = os.path.normpath(destination)
        destination_basename = os.path.basename(destination)

        if os.path.isfile(source):
            if os.path.isfile(destination):
                self.log.error(f"{self.__class__.__name__} cannot copy to a specific file")
            # Source is an individual file so don't list the destination
            options = self.options + ['--no-traverse']
        elif destination_basename != source_basename:
            # Source is a directory, so ensure the destination matches to avoid flattening.
            destination = os.path.join(destination, source_basename)
            options = self.options

        return super().clone(source, destination, options)


class CopyTree(AbstractCloneTool):

    def clone(self, source, destination):
        shutil.copytree(source, destination, dirs_exist_ok=True)

    @classmethod
    def is_available(cls):
        return True


class CloneToolFactory(ConfigMixin, LoggingMixin):
    # Maybe make this CloneTool and use wrapper + strategy to defer to inner tool.

    @staticmethod
    def get_options():
        return {
            cls.__name__: cls
            for cls in itertools.chain(
                AbstractCloneTool.__subclasses__(),
                AbstractExternalCloneTool.__subclasses__()
            )
        }

    def get_strategy(self, strategy=('Rclone', 'Rsync', 'CopyTree')):
        try:
            strategy = self.config['strategy']
        except KeyError:
            strategy_source = self.__class__.__qualname__
        else:
            strategy_source = self.settings.path

        self.log.info(f"Clone tool strategy: {strategy} (Source: {strategy_source})")

        return strategy, strategy_source

    def get(self):
        options = self.get_options()
        strategy, source = self.get_strategy()
        for tool_name in strategy:
            try:
                tool = options.get(tool_name)
            except KeyError:
                self.log.error(f"Unrecognised clone tool '{tool_name}'.")
            else:
                if tool.is_available():
                    self.log.info(f"Clone tool: {tool_name}")
                    return tool

clone_tool = CloneToolFactory().get()()


# --------------------------------------------------------------------
# Size Tool
# --------------------------------------------------------------------
class AbstractSizeTool(AbstractFsTool):

    @abstractmethod
    def total_size(self, path: str) -> int:
        return 0


class AbstractExternalSizeTool(AbstractSizeTool, AbstractExternalFsTool):

    def run(self, path, executable=None, options=None):
        if options is None:
            options = self.options
        elif isinstance(options, list):
            options = options
        else:
            self.log.error(f"options parameter must be a list or None")

        return subprocess.check_output(
            [self.executable]
            + options
            + [path]
        )



class Du(AbstractExternalSizeTool):
    executable = 'du'
    options = ['-cbs']

    def stat(self, path) -> dict:
        table = self._parse_stdout(subprocess.check_output([
            'find', path,
            '-type', 'f',
            '-exec', 'du', '-b', '{}', '+'
        ]))
        return {path: size for size, path in table}

    def total_size(self, path, options=None):
        return int(self._parse_stdout(self.run(path))[-1][0])

    @staticmethod
    def _parse_stdout(stdout):
        def transform(fs, xs):
            return [f(x) for f, x in zip(fs, xs)]

        lines = stdout.decode('utf8').strip().splitlines()

        return [
            transform((int, lambda x: x), line.split('\t'))
            for line in lines
        ]


size_tool = Du()




