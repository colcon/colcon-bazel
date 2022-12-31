# Copyright 2018 Mickael Gaillard
# Licensed under the Apache License, Version 2.0

import sys

from colcon_bazel.argcomplete_completer.bazel_args \
    import BazelArgcompleteCompleter
from colcon_bazel.argcomplete_completer.bazel_args \
    import get_bazel_args_completer_choices
import pytest


@pytest.mark.skipif(sys.platform == 'win32',
                    reason='does not run on windows')
def test_get_completer():
    extension = BazelArgcompleteCompleter()

    args = ['--bazel-args']
    karg = {'--bazel-args': 'test'}
    assert extension.get_completer(None, None, None) is None
    assert extension.get_completer(None, *args, **karg) is not None


@pytest.mark.skipif(sys.platform == 'win32',
                    reason='does not run on windows')
def test_get_bazel_args_completer_choices():
    choices = get_bazel_args_completer_choices()

    assert len(choices) == 0
