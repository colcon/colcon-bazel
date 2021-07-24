# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0

# try import since this package doesn't depend on colcon-argcomplete
try:
    from colcon_argcomplete.argcomplete_completer \
        import ArgcompleteCompleterExtensionPoint
except ImportError:
    class ArgcompleteCompleterExtensionPoint:  # noqa: D101
        pass
from colcon_core.plugin_system import satisfies_version


class BazelArgcompleteCompleter(ArgcompleteCompleterExtensionPoint):
    """Completion of Bazel arguments."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            ArgcompleteCompleterExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')

    def get_completer(self, parser, *args, **kwargs):  # noqa: D102
        if not any(elem in args for elem in ['--bazel-args', '--bazel-opts']):
            return None

        try:
            from argcomplete.completers import ChoicesCompleter
        except ImportError:
            return None

        if '--bazel-opts' in args:
            return ChoicesCompleter(get_bazel_opts_completer_choices())

        if '--bazel-args' in args:
            return ChoicesCompleter(get_bazel_args_completer_choices())


def get_bazel_args_completer_choices():
    """
    Get the Bazel arguments completer choices.

    Currently this empty.
    :rtype: list
    """
    # HACK the quote and equal characters are currently a problem
    # see https://github.com/kislyuk/argcomplete/issues/94
    return []


def get_bazel_opts_completer_choices():
    """
    Get the Bazel options completer choices.

    Currently this empty.
    :rtype: list
    """
    # HACK the quote and equal characters are currently a problem
    # see https://github.com/kislyuk/argcomplete/issues/94
    return []
