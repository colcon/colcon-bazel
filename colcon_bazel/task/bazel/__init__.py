# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0

import os
from pathlib import Path
import re
import shutil

from colcon_core.environment_variable import EnvironmentVariable
from colcon_core.subprocess import check_output

BZL_COMAND = 'build'
BZL_OUTPUT = '--output_base'
BZL_INSTALL = '--install_base'
BZL_SYMLYNK = '--symlink_prefix'

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
    env_cmd = os.getenv(environment_variable)
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


def get_bazel_executable(args):
    """
    Get executable path of bazel.

    :param str args: Arguments of package descriptor.
    :returns: The executable path
    :rtype: str
    """
    if _has_local_executable(args):
        cmd_exec_path = str(_get_local_executable(args).absolute())
    elif BAZEL_EXECUTABLE is not None:
        cmd_exec_path = BAZEL_EXECUTABLE
    else:
        raise RuntimeError("Could not find 'bazel' or 'wrapper' executable.")
    return cmd_exec_path


def get_bazel_startup_options(args):
    """
    Get startup options of bazel.

    :param str args: Arguments of package descriptor.
    :returns: startup options
    :rtype: list
    """
    bazel_args = (args.bazel_args or [])
    tmp_args = ' '.join(bazel_args)

    regex = '.*(' + BZL_OUTPUT + '|' + BZL_INSTALL + ').*'
    if (not re.match(regex, tmp_args)):
        # Default Bazel 'build' & 'install' folder for colcon.
        output_path = BZL_OUTPUT + '=' + args.build_base + '/bazel'
        install_path = BZL_INSTALL + '=' + args.install_base + '/bazel'
        cmd_startup_options = [output_path, install_path]
    else:
        # Do not override the default Bazel 'build' & 'install'
        # folder for colcon.
        msg = "Could not use 'output_base' and 'install_base' arguments."
        raise RuntimeError(msg)

    return cmd_startup_options


def get_bazel_command(args, default_cmd=BZL_COMAND):
    """
    Get target command of bazel.

    :param str args: Arguments of package descriptor.
    :returns: The target command
    :rtype: str
    """
    if args.bazel_task:
        cmd_command = args.bazel_task
    else:
        cmd_command = default_cmd

    return cmd_command


def get_bazel_arguments(args):
    """
    Get target arguments of bazel.

    :param str args: Arguments of package descriptor.
    :returns: target arguments
    :rtype: list
    """
    cmd_args = (args.bazel_args or [])
    tmp_args = ' '.join(cmd_args)

    # Disable symbolic link in source folder.
    if (not re.match('.*' + BZL_SYMLYNK + '.*', ' '.join(tmp_args))):
        cmd_args += [BZL_SYMLYNK + '=/']

    # Define verbose mode.
    cmd_args += ['--show_result=-1', '--noshow_progress',
                 '--noshow_loading_progress', '--logging=0',
                 '--verbose_failures']

    return cmd_args


def _has_local_executable(args):
    bazel_path = _get_local_executable(args)
    return bazel_path.is_file()


def _get_local_executable(args):
    bazel_script = 'bazelw'
    bazel_path = Path(args.path) / bazel_script
    return bazel_path
