# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0

import ast
import os
from pathlib import Path
import re

from colcon_bazel.task.bazel import BAZEL_EXECUTABLE
from colcon_core.environment import create_environment_scripts
from colcon_core.logging import colcon_logger
from colcon_core.plugin_system import satisfies_version
from colcon_core.shell import get_command_environment
from colcon_core.task import check_call
from colcon_core.task import TaskExtensionPoint

logger = colcon_logger.getChild(__name__)


class BazelBuildTask(TaskExtensionPoint):
    """Build bazel packages."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(TaskExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')

    def add_arguments(self, *, parser):  # noqa: D102
        parser.add_argument(
            '--bazel-args',
            nargs='*', metavar='*', type=str.lstrip,
            help='Pass arguments to Bazel projects. '
            'Arguments matching other options must be prefixed by a space,\n'
            'e.g. --bazel-args " --help"')
        parser.add_argument(
            '--bazel-task',
            help='Run a specific task instead of the default task')

    async def build(
        self, *, additional_hooks=None, skip_hook_creation=False
    ):  # noqa: D102
        pkg = self.context.pkg
        args = self.context.args

        logger.info(
            "Building Bazel package in '{args.path}'".format_map(locals()))

        try:
            env = await get_command_environment(
                'build', args.build_base, self.context.dependencies)
        except RuntimeError as e:
            logger.error(str(e))
            return 1

        rc = await self._build(args, env)
        if rc and rc.returncode:
            return rc.returncode

        if not skip_hook_creation:
            create_environment_scripts(
                pkg, args, additional_hooks=additional_hooks)

    async def _build(self, args, env):
        self.progress('build')

        # Bazel Executable
        if has_local_executable(args):
            cmd = [str(get_local_executable(args).absolute())]
        elif BAZEL_EXECUTABLE is not None:
            cmd = [BAZEL_EXECUTABLE]
        else:
            msg = "Could not find 'bazel' or 'wrapper' executable"
            logger.error(msg)
            raise RuntimeError(msg)

        cmd += ['--output_base=' + args.build_base + '/bazel']
        cmd += ['--install_base=' + args.install_base + '/bazel']

        # Bazel Task (by default 'build')
        if args.bazel_task:
            cmd += [args.bazel_task]
        else:
            cmd += ['build', '//:ProjectRunner' ]

        # Bazel Arguments
        cmd += (args.bazel_args or [])

        # Disable Symlink in src.
        cmd += ['--symlink_prefix=/']

        print(' '.join(cmd))
        # invoke build step
        return await check_call(
            self.context, cmd, cwd=args.path, env=env)

def has_local_executable(args):
    bazel_path   = get_local_executable(args)
    return bazel_path.is_file()

def get_local_executable(args):
    bazel_script = 'bazelw'
    bazel_path   = Path(args.path) / bazel_script
    return bazel_path

