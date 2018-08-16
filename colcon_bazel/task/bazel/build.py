# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0

from colcon_bazel.task.bazel import get_bazel_arguments
from colcon_bazel.task.bazel import get_bazel_command
from colcon_bazel.task.bazel import get_bazel_executable
from colcon_bazel.task.bazel import get_bazel_startup_options
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

        bzl_exec_path = get_bazel_executable(args)
        bzl_startup_options = get_bazel_startup_options(args)
        bzl_command = get_bazel_command(args)
        bzl_args = get_bazel_arguments(args)
        bzl_target_patterns = ['//...']

        # Make full command
        # https://docs.bazel.build/versions/master/command-line-reference.html
        cmd = [bzl_exec_path]
        cmd.extend(bzl_startup_options)
        cmd.append(bzl_command)
        cmd.extend(bzl_args)
        cmd.append('--')
        cmd.extend(bzl_target_patterns)

        # invoke build step
        return await check_call(
            self.context, cmd, cwd=args.path, env=env)
