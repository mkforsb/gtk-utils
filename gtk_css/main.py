# MIT License
# Copyright 2024 Mikael Forsberg (github.com/mkforsb)

import sys
import os
import re
import xml.etree.ElementTree as ET

import gtk_css.constants as constants


def pseudoparse_css_block(text):
    parts = text.split("{")
    result = []

    for rule in re.split(r",\s*", parts[0].strip()):
        result.append(
            {
                "match": re.split(r"\s+", rule.strip()),
                "props": dict(
                    [
                        (part[0].strip(), part[1].strip()[:-1])
                        for propdef in re.findall(
                            r"[^:]+:.+?;", re.sub(r"(?sm)/\*.*?\*/", "", parts[1])
                        )
                        for part in (propdef.split(":"),)
                    ]
                ),
            }
        )

    return result


def pseudoparse_css(text):
    return [
        rule
        for block in re.findall(r"(?sm)[^{]+{.*?}", text)
        for rule in pseudoparse_css_block(block)
    ]


def css_classes(node):
    assert node.tag == "object"

    declared_classes = [
        subchild.attrib["name"]
        for child in node
        if child.tag == "style"
        for subchild in child
        if subchild.tag == "class"
    ]

    return constants.auto_classes.get(node.attrib["class"], []) + declared_classes


def css_element_name(node):
    assert node.tag == "object"
    return constants.element_names[node.attrib["class"]]


def css_widget_name(node):
    assert node.tag == "object"

    for child in [
        child
        for child in node
        if child.tag == "property" and child.attrib["name"] == "name"
    ]:
        return child.text


def etree_traverse(tree, f, path=None):
    if tree.tag == "object" and css_element_name(tree) is not None:
        new_path = ([] if path is None else path) + (
            [
                {
                    "element_name": css_element_name(tree),
                    "widget_name": css_widget_name(tree),
                    "classes": css_classes(tree),
                }
            ]
        )
        f(tree, new_path)
    else:
        new_path = path

    for child in tree:
        etree_traverse(child, f, new_path)


def take_while(text, f):
    pos = 0
    length = len(text)

    while pos < length and f(text[pos]) == True:
        pos += 1

    return (text[:pos], text[pos:])


def requirements(fragment):
    if fragment == "" or fragment.startswith(":"):
        return []
    elif fragment.startswith("#"):
        (widget_name, tail) = take_while(
            fragment[1:], lambda c: re.match(r"[^.:#]", c) is not None
        )
        return [("widget_name", widget_name)] + requirements(tail)
    elif fragment.startswith("."):
        (class_name, tail) = take_while(
            fragment[1:], lambda c: re.match(r"[^.:#]", c) is not None
        )
        return [("class", class_name)] + requirements(tail)
    else:
        (element_name, tail) = take_while(
            fragment, lambda c: re.match(r"[^.:#]", c) is not None
        )
        return [("element_name", element_name)] + requirements(tail)


def match_rule(rule, path, ascend=False):
    if len(rule) == 0:
        return True

    if len(path) == 0:
        return False

    if rule[-1] == ">":
        return match_rule(rule[:-1], path, False)

    if rule[-1] == "*":
        if ascend:
            # return any(match_rule(rule[:-1], path[:-i]) for i in range(1, len(path)))
            return match_rule(rule[:-1], path[:-1], True) or match_rule(
                rule, path[:-1], True
            )
        else:
            return match_rule(rule[:-1], path[:-1], True)

    for req_type, req_val in requirements(rule[-1]):
        if req_type == "element_name" and req_val != path[-1]["element_name"]:
            return match_rule(rule, path[:-1], True) if ascend else False
        if req_type == "widget_name" and req_val != path[-1]["widget_name"]:
            return match_rule(rule, path[:-1], True) if ascend else False
        if req_type == "class" and req_val not in path[-1]["classes"]:
            return match_rule(rule, path[:-1], True) if ascend else False

    return match_rule(rule[:-1], path[:-1], True)


def render_css(css, include="all"):
    out = []

    for rule in css:
        rendered_props = rule["props"]

        if include == "nongtk":
            rendered_props = [
                prop for prop in rule["props"] if not prop.startswith("gtk-")
            ]

        if len(rendered_props) > 0:
            out.append(f"{' '.join(rule['match'])} {{")

            for prop in rendered_props:
                out.append(f"    {prop}: {rule['props'][prop]};")

            out.append(f"}}\n")

    return "\n".join(out).strip()


def cssable_props(node):
    return [
        child
        for child in node
        if child.tag == "property" and child.attrib["name"] in constants.cssable_props
    ]


def path_to_css_selector(path):
    result = []

    for entry in path:
        if len(result) > 0:
            result.append(">")

        part = [entry["element_name"]]

        if entry["widget_name"] is not None:
            part.append("#")
            part.append(entry["widget_name"])

        for cl in entry["classes"]:
            part.append(".")
            part.append(cl)

        result.append("".join(part))

    return result


def compile(css, xml, target_dir):
    with open(f"{target_dir}/{os.path.basename(css[0])}", "w+") as out:
        out.write(render_css(css[1], include="nongtk"))

    def match_add_props(node, path):
        for rule in css[1]:
            if match_rule(rule["match"], path):
                for prop in [prop for prop in rule["props"] if prop.startswith("gtk-")]:
                    element = ET.Element("property", {"name": prop[4:]})
                    element.text = rule["props"][prop]
                    node.append(element)

    for filename, etree in xml:
        etree_traverse(etree.getroot(), match_add_props)
        ET.indent(etree)
        etree.write(
            f"{target_dir}/{os.path.basename(filename)}",
            encoding="utf-8",
            xml_declaration=True,
        )

        with open(f"{target_dir}/{os.path.basename(filename)}", "a") as fd:
            fd.write("\n")


def decompile(css, xml, target_dir):
    def remove_props(node, path):
        matched_in_css = False
        target_props = cssable_props(node)

        if len(target_props) == 0:
            return

        for rule in css[1]:
            if match_rule(rule["match"], path):
                matched_in_css = True

                for prop in target_props:
                    rule["props"][prop.attrib["name"]] = prop.text.strip()

        if not matched_in_css:
            css[1].append(
                {
                    "match": path_to_css_selector(path),
                    "props": dict(
                        [
                            (f"gtk-{prop.attrib['name']}", prop.text.strip())
                            for prop in target_props
                        ]
                    ),
                }
            )

        for prop in target_props:
            node.remove(prop)

    for filename, etree in xml:
        etree_traverse(etree.getroot(), remove_props)
        ET.indent(etree)
        etree.write(
            f"{target_dir}/{os.path.basename(filename)}",
            encoding="utf-8",
            xml_declaration=True,
        )

        with open(f"{target_dir}/{os.path.basename(filename)}", "a") as fd:
            fd.write("\n")

    with open(f"{target_dir}/{os.path.basename(css[0])}", "w+") as out:
        out.write(render_css(css[1], include="all"))


def main(args):
    css = None
    xml = []
    target_dir = None
    action = None

    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))

    for arg in args:
        if arg == "compile":
            action = "compile"
        elif arg == "decompile":
            action = "decompile"
        elif os.path.isfile(arg):
            if arg.endswith("css"):
                with open(arg) as fd:
                    css = (arg, pseudoparse_css(fd.read()))
            else:
                xml.append((arg, ET.parse(arg, parser)))
        elif os.path.isdir(arg):
            target_dir = arg

    if (
        (action == "compile" and css is None)
        or len(xml) == 0
        or target_dir is None
        or action is None
    ):
        print(
            "usage: python -m gtk_css.main compile CSSFILE XMLFILE[, XMLFILE, ...] "
            "OUTPUTDIR"
        )
        print(
            "       python -m gtk_css.main decompile [CSSFILE] XMLFILE[, XMLFILE, ...]"
            " OUTPUTDIR"
        )
        print("")
        print("examples:")
        print(
            "  python -m gtk_css.main compile style.css window.xml dialog.xml /tmp/out"
        )
        print(
            "  python -m gtk_css.main decompile /tmp/style.css /tmp/out/window.xml "
            "/tmp/out/dialog.xml /tmp/decomp"
        )
        return

    if action == "compile":
        compile(css, xml, target_dir)
    elif action == "decompile":
        if css is None:
            css = ("style.css", [])
        decompile(css, xml, target_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
