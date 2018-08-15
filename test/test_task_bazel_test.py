# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0


import pytest

from colcon_bazel.task.bazel.test import BazelTestTask
from colcon_core.package_descriptor import PackageDescriptor
from colcon_core.task import TaskContext

from tempfile import TemporaryDirectory

@pytest.mark.asyncio
async def test_task_test():
    with TemporaryDirectory(prefix='test_colcon_') as basepath:
        extension = BazelTestTask()
        desc = PackageDescriptor(basepath)
        context = TaskContext(pkg=desc, args=[''], dependencies=set())

        extension.set_context(context=context)
        rc = await extension.test()

        assert rc == 0
