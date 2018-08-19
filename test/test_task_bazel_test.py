# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0


import asyncio
import pytest

from colcon_bazel.task.bazel.test import BazelTestTask
from colcon_core.package_descriptor import PackageDescriptor
from colcon_core.task import TaskContext
from colcon_core.verb.test import TestPackageArguments

from pathlib import Path
from tempfile import TemporaryDirectory


class MockArgs(object):
    def __init__(self, basepath):  # noqa: D107
        super().__init__()
        self.build_base = (basepath + '/build/')
        self.install_base = (basepath + '/install/')
        self.merge_install = (basepath + '/merge/')
        self.test_result_base = (basepath + '/test/')


@pytest.mark.asyncio
async def test_task_test():
    with TemporaryDirectory(prefix='test_colcon_') as basepath:
        extension = BazelTestTask()

        desc = PackageDescriptor(basepath)
        desc.name = "test"

        args_verb = MockArgs(basepath)
        args_pkg = TestPackageArguments(desc, args_verb)
        args_pkg.path = basepath
        args_pkg.build_base = args_verb.build_base
        args_pkg.install_base = args_verb.install_base
        args_pkg.merge_install = args_verb.merge_install
        args_pkg.test_result_base = args_verb.test_result_base

        context = TaskContext(pkg=desc, args=args_pkg, dependencies=set())

        extension.set_context(context=context)
        ret = await extension.test()

        assert ret
