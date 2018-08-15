# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0

from colcon_bazel.argcomplete_completer.bazel_args \
    import BazelArgcompleteCompleter
from colcon_bazel.argcomplete_completer.bazel_args \
    import get_bazel_args_completer_choices
import pytest


def test_get_completer():
    extension = BazelArgcompleteCompleter()

    assert extension.get_completer(None, [''], None) is None
    assert extension.get_completer(None, ['--bazel-args'], None) is None


def test_get_bazel_args_completer_choices():
    choices = get_bazel_args_completer_choices()

    assert len(choices) == 0
