# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0

from pathlib import Path
from tempfile import TemporaryDirectory

from colcon_core.package_descriptor import PackageDescriptor
from colcon_bazel.package_identification.bazel \
    import BazelPackageIdentification
from colcon_bazel.package_identification.bazel \
    import extract_data
from colcon_bazel.package_identification.bazel \
    import extract_content
import pytest


def test_identify():
    extension = BazelPackageIdentification()

    with TemporaryDirectory(prefix='test_colcon_') as basepath:
        desc = PackageDescriptor(basepath)
        desc.type = 'other'
        assert extension.identify(desc) is None
        assert desc.name is None

        desc.type = None
        assert extension.identify(desc) is None
        assert desc.name is None
        assert desc.type is None

        basepath = Path(basepath)
        (basepath / 'BUILD.bazel').write_text('')
        assert extension.identify(desc) is None
        assert desc.name is not None
        assert desc.type is 'bazel'

        desc.name = None
        (basepath / 'BUILD').write_text('')
        assert extension.identify(desc) is None
        assert desc.name is not None
        assert desc.type is 'bazel'

        desc.name = None
        (basepath / 'BUILD.bazel').write_text(
            'java_binary(\n'
            '    name = "pkg-name",\n'
            ')\n')
        assert extension.identify(desc) is None
        assert desc.name == 'pkg-name'
        assert desc.type == 'bazel'

        desc.name = 'other-name'
        with pytest.raises(RuntimeError) as e:
            extension.identify(desc)
        assert str(e).endswith('Package name already set to different value')

        (basepath / 'BUILD.bazel').write_text(
            'java_binary(\n'
            '    name = "other-name",\n'
            '    deps = [":build-depA", ":build-depB"]\n'
            '    runtime_deps = [":run-depA", ":run-depB"]\n'
            ')\n'
            '\n'
            'java_test(\n'
            '    name = "other-name-test",\n'
            '    deps = [":test-dep"],\n'
            '    runtime_deps = [":test-run-dep"]\n'
            ')\n'
            )

        assert extension.identify(desc) is None
        assert desc.name == 'other-name'
        assert desc.type == 'bazel'
        assert set(desc.dependencies.keys()) == {'build', 'run', 'test'}
        # TODO check dependencies content


def test_extract_data():
    with TemporaryDirectory(prefix='test_colcon_') as basepath:
        basepath = Path(basepath)
        (basepath / 'BUILD.bazel').write_text(
            'java_binary(\n'
            '    name = "pkg-name",\n'
            ')\n')
        data = extract_data(basepath / 'BUILD.bazel')
        assert data['name'] == 'pkg-name'


def test_extract_content():
    with TemporaryDirectory(prefix='test_colcon_') as basepath:
        basepath = Path(basepath)
        # TODO Add comment
        (basepath / 'BUILD.bazel').write_text(
            'java_binary(\n'
            '    name = "pkg-name",\n'
            ')\n')
        content = extract_content(basepath / 'BUILD.bazel')
        assert content == 'java_binary(\n    name = "pkg-name",\n)\n'
