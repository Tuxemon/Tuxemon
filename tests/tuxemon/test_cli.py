# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext
from tuxemon.cli.exceptions import CommandNotFoundError
from tuxemon.cli.formatter import Formatter
from tuxemon.cli.parser import tokenize
from tuxemon.cli.processor import MetaCommand


class Leaf(CLICommand):
    name = "leaf"
    description = "Leaf command"


class Branch(CLICommand):
    name = "branch"
    description = "Branch command"

    def get_subcommands(self, ctx):
        return [Leaf()]


class Root(CLICommand):
    name = "root"
    description = "Root command"

    def get_subcommands(self, ctx):
        return [Branch(), Leaf()]


@pytest.fixture
def ctx():
    class Dummy:
        pass

    dummy = Dummy()
    dummy.client = Dummy()
    dummy.client.is_running = False

    root = Root()
    return InvokeContext(
        processor=dummy,
        session=dummy,
        root_command=root,
        current_command=root,
        formatter=Formatter(),
    )


@pytest.fixture
def root(ctx):
    return ctx.root_command


@pytest.mark.parametrize(
    "path, expected_cmd, expected_tail",
    [
        pytest.param(
            "branch leaf x y",
            "leaf",
            "x y",
            id="nested-subcommand-with-args",
        ),
        pytest.param(
            "leaf",
            "leaf",
            "",
            id="direct-leaf-no-args",
        ),
        pytest.param(
            "leaf a b",
            "leaf",
            "a b",
            id="direct-leaf-with-args",
        ),
        pytest.param(
            "branch unknown something",
            "branch",
            "unknown something",
            id="unknown-subcommand-falls-back",
        ),
        pytest.param(
            "unknown",
            "root",
            "unknown",
            id="unknown-top-level",
        ),
        pytest.param(
            "branch",
            "branch",
            "",
            id="exact-branch-no-args",
        ),
    ],
)
def test_resolve(root, ctx, path, expected_cmd, expected_tail):
    cmd, tail = root.resolve(ctx, path)
    assert cmd.name == expected_cmd
    assert tail == expected_tail


def test_get_subcommand_success(root, ctx):
    cmd = root.get_subcommand(ctx, "leaf")
    assert cmd.name == "leaf"


def test_get_subcommand_failure(root, ctx):
    with pytest.raises(CommandNotFoundError):
        root.get_subcommand(ctx, "does_not_exist")


def test_get_parameters_lists_subcommands(root, ctx):
    params = list(root.get_parameters(ctx))
    names = [p.name for p in params]
    assert set(names) == {"branch", "leaf"}


@pytest.mark.parametrize(
    "line, expected",
    [
        pytest.param("a b c", ["a", "b", "c"], id="simple-tokenize"),
        pytest.param("single", ["single"], id="single-token"),
        pytest.param("a   b", ["a", "", "", "b"], id="multiple-spaces"),
    ],
)
def test_tokenize(line, expected):
    assert tokenize(line) == expected


class A(CLICommand):
    name = "a"
    description = "Command A"


class B(CLICommand):
    name = "b"
    description = "Command B"


def test_metacommand_lists_subcommands(capsys, ctx):
    meta = MetaCommand([A(), B()])
    meta.invoke(ctx, "")
    out = capsys.readouterr().err

    assert "No command provided" in out
    assert "- a: Command A" in out
    assert "- b: Command B" in out


def test_metacommand_get_subcommands(ctx):
    meta = MetaCommand([A(), B()])
    subs = list(meta.get_subcommands(ctx))
    assert {cmd.name for cmd in subs} == {"a", "b"}


class L3(CLICommand):
    name = "l3"


class L2(CLICommand):
    name = "l2"

    def get_subcommands(self, ctx):
        return [L3()]


class L1(CLICommand):
    name = "l1"

    def get_subcommands(self, ctx):
        return [L2()]


class DeepRoot(CLICommand):
    name = "deep"

    def get_subcommands(self, ctx):
        return [L1()]


def test_resolve_deep_recursion(ctx):
    root = DeepRoot()
    cmd, tail = root.resolve(ctx, "l1 l2 l3 final args")
    assert cmd.name == "l3"
    assert tail == "final args"


class A1(CLICommand):
    name = "dup"


class A2(CLICommand):
    name = "dup"


class ShadowRoot(CLICommand):
    name = "root"

    def get_subcommands(self, ctx):
        return [A1(), A2()]


def test_shadowed_subcommands(ctx):
    root = ShadowRoot()
    cmd, tail = root.resolve(ctx, "dup x")
    assert isinstance(cmd, A1)
    assert tail == "x"


@pytest.mark.parametrize(
    "line, expected",
    [
        pytest.param("  a b", ["a", "b"], id="leading-spaces"),
        pytest.param("a b   ", ["a", "b"], id="trailing-spaces"),
        pytest.param(
            "   a    b   c   ",
            ["a", "", "", "", "b", "", "", "c"],
            id="messy-spaces",
        ),
    ],
)
def test_tokenize_whitespace(line, expected):
    assert tokenize(line) == expected


def test_resolve_stops_on_first_unknown(root, ctx):
    cmd, tail = root.resolve(ctx, "branch ??? leaf")
    assert cmd.name == "branch"
    assert tail == "??? leaf"


def test_get_parameters_nested(ctx):
    branch = Branch()
    params = list(branch.get_parameters(ctx))
    assert [p.name for p in params] == ["leaf"]


def test_metacommand_resolve(ctx):
    meta = MetaCommand([A(), B()])
    ctx.root_command = meta
    cmd, tail = meta.resolve(ctx, "a x y")
    assert cmd.name == "a"
    assert tail == "x y"


def test_resolve_on_leaf(ctx):
    leaf = Leaf()
    cmd, tail = leaf.resolve(ctx, "anything here")
    assert cmd is leaf
    assert tail == "anything here"


class SelfRef(CLICommand):
    name = "self"

    def get_subcommands(self, ctx):
        return [self]


def test_self_recursive_resolve_terminates(ctx):
    class SelfRef(CLICommand):
        name = "self"

        def get_subcommands(self, ctx):
            return [self]

    root = SelfRef()
    cmd, tail = root.resolve(ctx, "self self self")
    assert cmd is root
    assert tail == ""


def test_case_sensitivity(root, ctx):
    # "Leaf" should NOT match "leaf"
    cmd, tail = root.resolve(ctx, "Leaf something")
    assert cmd is root
    assert tail == "Leaf something"


class Foo(CLICommand):
    name = "foo"


class Foobar(CLICommand):
    name = "foobar"


class PrefixRoot(CLICommand):
    name = "root"

    def get_subcommands(self, ctx):
        return [Foo(), Foobar()]


def test_overlapping_prefixes(ctx):
    root = PrefixRoot()

    cmd, tail = root.resolve(ctx, "foo x")
    assert cmd.name == "foo"
    assert tail == "x"

    cmd, tail = root.resolve(ctx, "foobar y")
    assert cmd.name == "foobar"
    assert tail == "y"


class Hyphen(CLICommand):
    name = "char-face"


class Underscore(CLICommand):
    name = "char_face"


class WeirdRoot(CLICommand):
    name = "root"

    def get_subcommands(self, ctx):
        return [Hyphen(), Underscore()]


def test_unusual_names(ctx):
    root = WeirdRoot()

    cmd, tail = root.resolve(ctx, "char-face up")
    assert cmd.name == "char-face"
    assert tail == "up"

    cmd, tail = root.resolve(ctx, "char_face down")
    assert cmd.name == "char_face"
    assert tail == "down"


class Multi(CLICommand):
    name = "multi word"


class MultiRoot(CLICommand):
    name = "root"

    def get_subcommands(self, ctx):
        return [Multi()]


def test_multiword_command_name(ctx):
    root = MultiRoot()
    cmd, tail = root.resolve(ctx, "multi word test")
    # "multi" is treated as head, "word test" as tail → no match
    assert cmd is root
    assert tail == "multi word test"


class Custom(CLICommand):
    name = "custom"

    def get_subcommand(self, ctx, name):
        if name.lower() == "x":
            return Leaf()
        raise CommandNotFoundError()


class CustomRoot(CLICommand):
    name = "root"

    def get_subcommands(self, ctx):
        return [Custom()]


def test_custom_get_subcommand(ctx):
    root = CustomRoot()
    cmd, tail = root.resolve(ctx, "custom X arg")
    assert cmd.name == "leaf"
    assert tail == "arg"


class Exploding(CLICommand):
    name = "boom"

    def invoke(self, ctx, line):
        raise RuntimeError("boom!")


class ExplodingRoot(CLICommand):
    name = "root"

    def get_subcommands(self, ctx):
        return [Exploding()]


def test_invoke_exception_propagates(ctx):
    root = ExplodingRoot()
    cmd, tail = root.resolve(ctx, "boom now")
    with pytest.raises(RuntimeError):
        cmd.invoke(ctx, tail)
