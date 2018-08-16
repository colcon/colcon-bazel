# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0

from colcon_bazel.argcomplete_completer.bazel_args \
    import BazelArgcompleteCompleter
from colcon_bazel.argcomplete_completer.bazel_args \
    import get_bazel_args_completer_choices
import sys
import pytest

@pytest.mark.skipif(sys.platform == 'win32',
                    reason="does not run on windows")
def test_get_completer():
    extension = BazelArgcompleteCompleter()

    assert extension.get_completer(None, [''], None) is None
    assert extension.get_completer(None, ['--bazel-args'], None) is None

@pytest.mark.skipif(sys.platform == 'win32',
                    reason="does not run on windows")
def test_get_bazel_args_completer_choices():
    choices = get_bazel_args_completer_choices()

    assert len(choices) == 0
