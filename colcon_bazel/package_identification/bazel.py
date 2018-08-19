# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0

import os
import re

from colcon_core.package_identification import logger
from colcon_core.package_identification \
    import PackageIdentificationExtensionPoint
from colcon_core.plugin_system import satisfies_version

from pathlib import Path
from pyparsing import alphanums
from pyparsing import delimitedList
from pyparsing import Dict
from pyparsing import Group
from pyparsing import Literal
from pyparsing import nestedExpr
from pyparsing import OneOrMore
from pyparsing import Optional
from pyparsing import pyparsing_common
from pyparsing import QuotedString
from pyparsing import Word


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
        desc.dependencies['build'] |= data['depends']['build']
        desc.dependencies['run'] |= data['depends']['run']
        desc.dependencies['test'] |= data['depends']['test']


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
    depends_content = content + extract_content(
        build_file.parent, exclude=[build_file])

    config = parse_config(depends_content)
    data['depends'] = extract_dependencies(config, exclude=data['name'])

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
    result = re.sub(r'(?m) ?#.*', '', content)  # Remove comment.
    result = re.sub(r'(?m)^\s*\n?', '', result)  # Remove extra space.
    return result


def extract_project_name(content):
    """
    Extract the Bazel project name from the BUILD file.

    :param str content: The Bazel BUILD file content.
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


def extract_dependencies(depends_content, exclude=None):
    """
    Extract the Bazel project name from the BUILD file.

    :param set depends_content: The Bazel BUILD files merged content.
    :param str exclude: exclude self references.
    :returns: List of dependencies, otherwise None.
    :rtype: set
    """
    depends = {'build': set(), 'run': set(), 'test': set()}

    for key, value in depends_content.items() or []:
        if 'binary' in key:
            _extra_deps(value, 'deps', depends['build'], exclude)
            _extra_deps(value, 'runtime_deps', depends['run'], exclude)
        if 'library' in key:
            _extra_deps(value, 'deps', depends['build'])
            _extra_deps(value, 'runtime_deps', depends['run'], exclude)
        if 'test' in key:
            _extra_deps(value, 'deps', depends['test'])
            _extra_deps(value, 'runtime_deps', depends['test'], exclude)

    return depends


def parse_config(content):
    """
    Parse the Bazel project BUILD file content.

    :param str content: The Bazel BUILD file content.
    :returns: Dictionary of config.
    :rtype: dict
    """
    quoted = QuotedString(quoteChar='"') | QuotedString(quoteChar='\'')
    item_name = pyparsing_common.identifier.setName('id')
    item_value = (
        Group(  # Array values.
            Literal('[').suppress() +
            delimitedList(quoted) +
            Literal(']').suppress()) |
        Group(  # Glob case.
            Word('glob([').suppress() +
            delimitedList(quoted) +
            Word('])').suppress()) |
        quoted).setName('value')  # Quoted string value.
    rule_item = Group(item_name + Literal('=').suppress() +
                      item_value + Optional(',').suppress())
    rule_items = Dict(delimitedList(rule_item))
    rule_values = nestedExpr(content=rule_items)
    rule_taret = item_name
    rule = Group(rule_taret + rule_values)
    parser = Dict(OneOrMore(rule))

    try:
        config = parser.parseString(content)
    except Exception as e:
        logger.warning('No valid Build content')
        return {}

    return config.asDict()


def _extra_deps(value, entry, depends_target, exclude=None):
    if entry in value:
        pattern = Group(
            Optional(Group(
                Literal('@') +
                Word(alphanums + '_-')
            ).suppress()) +
            Optional(Literal('//').suppress()) +
            Optional(Word(alphanums + '_-/').suppress()) +
            Optional(Literal(':').suppress()) +
            Word(alphanums + '_-')
        )

        for dep in value.get(entry):
            try:
                extract_name = pattern.parseString(dep)[0][0]
                if extract_name != exclude:  # exclude self references
                    depends_target.update({extract_name})
            except Exception as e:
                logger.warning('No valid Build content %s' % dep)
