# MIT License
# Copyright 2024 Mikael Forsberg (github.com/mkforsb)

from gtk_css.main import match_rule


def test_match_rule():
    # rules are lists of fragments: ["overlay", ".settings-page", "pane", ">", "*"]
    # paths are lists of maps: [{"element_name": "frame", "widget_name": None, "classes": ["foo", "bar"]}]

    assert match_rule(
        ["foo", "bar"],
        [
            {"element_name": "foo", "widget_name": None, "classes": []},
            {"element_name": "bar", "widget_name": None, "classes": []},
        ],
    )

    assert not match_rule(
        ["bar", "foo"],
        [
            {"element_name": "foo", "widget_name": None, "classes": []},
            {"element_name": "bar", "widget_name": None, "classes": []},
        ],
    )

    assert match_rule(
        ["foo", "bar"],
        [
            {"element_name": "foo", "widget_name": None, "classes": []},
            {"element_name": "qux", "widget_name": None, "classes": []},
            {"element_name": "bar", "widget_name": None, "classes": []},
        ],
    )

    assert match_rule(
        ["foo", ">", "bar"],
        [
            {"element_name": "foo", "widget_name": None, "classes": []},
            {"element_name": "bar", "widget_name": None, "classes": []},
        ],
    )

    assert not match_rule(
        ["foo", ">", "bar"],
        [
            {"element_name": "foo", "widget_name": None, "classes": []},
            {"element_name": "qux", "widget_name": None, "classes": []},
            {"element_name": "bar", "widget_name": None, "classes": []},
        ],
    )

    assert match_rule(
        [".foo", "*"],
        [
            {"element_name": "x", "widget_name": None, "classes": ["foo"]},
            {"element_name": "y", "widget_name": None, "classes": []},
            {"element_name": "z", "widget_name": None, "classes": []},
        ],
    )

    assert not match_rule(
        [".foo", ">" "*"],
        [
            {"element_name": "x", "widget_name": None, "classes": ["foo"]},
            {"element_name": "y", "widget_name": None, "classes": []},
            {"element_name": "z", "widget_name": None, "classes": []},
        ],
    )

    assert match_rule(
        [".foo", ">", "*", ">", "z.bar"],
        [
            {"element_name": "x", "widget_name": None, "classes": ["foo"]},
            {"element_name": "y", "widget_name": None, "classes": []},
            {"element_name": "z", "widget_name": None, "classes": ["bar"]},
        ],
    )

    assert match_rule(
        [".foo", "*"],
        [
            {"element_name": "x", "widget_name": None, "classes": ["foo"]},
            {"element_name": "y", "widget_name": None, "classes": []},
        ],
    )

    assert match_rule(
        ["x.foo", "*"],
        [
            {"element_name": "x", "widget_name": None, "classes": ["foo"]},
            {"element_name": "y", "widget_name": None, "classes": []},
        ],
    )

    assert not match_rule(
        ["y.foo", "*"],
        [
            {"element_name": "x", "widget_name": None, "classes": ["foo"]},
            {"element_name": "y", "widget_name": None, "classes": []},
        ],
    )

    assert match_rule(
        ["#foo"], [{"element_name": "box", "widget_name": "foo", "classes": []}]
    )

    assert not match_rule(
        ["#foo"], [{"element_name": "box", "widget_name": "bar", "classes": []}]
    )
