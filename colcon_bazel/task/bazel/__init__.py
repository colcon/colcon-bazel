# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0

import os
from pathlib import Path
import shutil
import subprocess

from colcon_core.environment_variable import EnvironmentVariable
from colcon_core.subprocess import check_output

"""Environment variable to override the Bazel executable"""
BAZEL_COMMAND_ENVIRONMENT_VARIABLE = EnvironmentVariable(
    'BAZEL_COMMAND', 'The full path to the Bazel executable')
    
"""Environment variable to override the Bazel executable"""
BAZEL_HOME_ENVIRONMENT_VARIABLE = EnvironmentVariable(
    'BAZEL_HOME', 'The full path to the Bazel home')

def which_executable(environment_variable, executable_name):
    """
    Determine the path of an executable.

    An environment variable can be used to override the location instead of
    relying on searching the PATH.

    :param str environment_variable: The name of the environment variable
    :param str executable_name: The name of the executable
    :rtype: str
    """
    cmd = None
    env_cmd  = os.getenv(environment_variable)
    env_home = os.getenv(BAZEL_HOME_ENVIRONMENT_VARIABLE.name)
    
    # Case of BAZEL_COMMAND (colcon)
    if env_cmd is not None and Path(env_cmd).is_file():
        cmd = env_cmd

    # Case of BAZEL_HOME (official)
    if cmd is None and env_home is not None:
        bazel_path = Path(env_home) / 'bin' / executable_name
        if bazel_path.is_file():
            cmd = bazel_path

    # fall back (from PATH)
    if cmd is None:
        cmd = shutil.which(executable_name)

    return cmd

BAZEL_EXECUTABLE = which_executable(
    BAZEL_COMMAND_ENVIRONMENT_VARIABLE.name, 'bazel')


async def has_task(path, task):
    """
    Check if the Bazel project has a specific task.

    :param str path: The path of the directory containing the build.bazel file
    :param str target: The name of the target
    :rtype: bool
    """
    return task in await get_bazel_tasks(path)


async def get_bazel_tasks(path):
    """
    Get all targets from a `build.bazel`.

    :param str path: The path of the directory contain the build.bazel file
    :returns: The target names
    :rtype: list
    """
    output = await check_output([
        BAZEL_EXECUTABLE, 'tasks'], cwd=path)
    lines = output.decode().splitlines()
    separator = ' - '
    return [l.split(separator)[0] for l in lines if separator in l]

