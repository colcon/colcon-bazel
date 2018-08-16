# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0

import os
from pathlib import Path
import re

from colcon_core.package_identification import logger
from colcon_core.package_identification \
    import PackageIdentificationExtensionPoint
from colcon_core.plugin_system import satisfies_version


class BazelPackageIdentification(PackageIdentificationExtensionPoint):
    """Identify Bazel packages with `BUILD` files."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            PackageIdentificationExtensionPoint.EXTENSION_POINT_VERSION,
            '^1.0')

    def identify(self, desc):  # noqa: D102
        if desc.type is not None and desc.type != 'bazel':
            return

        build_file = desc.path / 'BUILD.bazel'
        if not build_file.is_file():
            # Dangerous, but valid for Bazel !
            build_file = desc.path / 'BUILD'
            if not build_file.is_file():
                return

        data = extract_data(build_file)
        if not data['name']:
            msg = ("Failed to extract project name from '%s'" % build_file)
            logger.error(msg)
            raise RuntimeError(msg)

        if desc.name is not None and desc.name != data['name']:
            msg = 'Package name already set to different value'
            logger.error(msg)
            raise RuntimeError(msg)

        desc.type = 'bazel'
        if desc.name is None:
            desc.name = data['name']
        desc.dependencies['build'] |= data['depends']
        desc.dependencies['run'] |= data['depends']
        desc.dependencies['test'] |= data['depends']


def extract_data(build_file):
    """
    Extract the project name and dependencies from a BUILD file.

    :param Path build_file: The path of the BUILD file
    :rtype: dict
    """
    content = extract_content(build_file)

    data = {}
    data['name'] = extract_project_name(content)
    # fall back to use the directory name
    if data['name'] is None:
        data['name'] = build_file.parent.name

    # extract dependencies from all Bazel files in the project directory
    data['depends'] = set()

    # exclude self references
    # data['depends'] = depends - {data['name']}

    return data


def extract_content(basepath, exclude=None):
    """
    Get all non-comment lines from BUILD files under the given basepath.

    :param Path basepath: The path to recursively crawl
    :param list exclude: The paths to exclude
    :rtype: str
    """
    if basepath.is_file():
        content = basepath.read_text(errors='replace')
    elif basepath.is_dir():
        content = ''
        for dirpath, dirnames, filenames in os.walk(str(basepath)):
            # skip sub-directories starting with a dot
            dirnames[:] = filter(lambda d: not d.startswith('.'), dirnames)
            dirnames.sort()

            for name in sorted(filenames):
                if name != 'BUILD.bazel':
                    continue

                path = Path(dirpath) / name
                if path in (exclude or []):
                    continue

                content += path.read_text(errors='replace') + '\n'
    else:
        return ''
    return _remove_bazel_comments(content)


def _remove_bazel_comments(content):
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return ' '  # note: a space and not an empty string
        else:
            return s
    pattern = re.compile(
        r'#.*$',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, content)


def extract_project_name(content):
    """
    Extract the Bazel project name from the BUILD file.

    :param str content: The Bazel BUILD file
    :returns: The project name, otherwise None
    :rtype: str
    """
    # extract project name
    match = re.search(
        # keyword
        'name'
        # optional white space
        '\s*'
        # equal assignment
        '\='
        # optional white space
        '\s*'
        # optional "opening" quote
        '("?)'
        # project name
        '([a-zA-Z0-9_-]+)'
        # optional "closing" quote (only if an "opening" quote was used)
        r'\1',
        content)
    if not match:
        return None
    return match.group(2)
