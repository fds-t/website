import os
import shutil
import argparse
import json
from pathlib import Path
from typing import Any, override

IMG_SUFFIXES = { ".png", ".jpg", ".jpeg", ".bmp", ".gif" }

class Template:
    def __init__(self, text: list[str], args: dict[str,str], arg_indices: list[str]) -> None:
        self.text = text
        self.args = args
        self.arg_indices = arg_indices

    @override
    def __repr__(self) -> str:
        return f"Template({self.text.__repr__()}, {self.args.__repr__()})"

# Input: string
# Output: tuple containing:
#   the string within the first curly brace pair and
#   the index of the first closing brace
def get_curly(s: str, prefix: str = "{") -> tuple[str,int]:
    text = s#.strip()
    start = text.find(prefix) + 1
    end = text.find("}")
    return text[start:end], end

def get_curly_outer(s: str, prefix: str = "{") -> str:
    text = s
    start = text.find(prefix)

    if start == -1:
        return ""

    end = text.rfind("}")
    res = text[start+len(prefix):end]

    return res

def get_curly_nested(s: str) -> list[str]:
    text = s#.strip()
    parts = []
    while text != "":
        parts.append(text)
        text = get_curly_outer(text)

    print(parts)
    for i in reversed(range(1, len(parts))):
        parts[i-1] = parts[i-1].replace(parts[i], "")

    return parts

def get_lines_until_string(string, start_line, lines) -> tuple[list[str],int]:
    i = start_line + 1
    template_lines = []
    while string not in lines[i]:
        template_lines.append(lines[i])
        i += 1
    return template_lines, i

def handle_new_template(start_line: int, lines: list[str], templates: dict[str, Any]):
    text = lines[start_line].strip()
    start = text.find("{") + 1
    end = text.find("}")
    temp_name = text[start:end]

    text_rest = text[end+1:]

    start = text_rest.find("{") + 1
    end = text_rest.find("}")

    args = {}
    arg_indices = []

    if end - start != 0:
        arg_name_type = [x.strip() for x in text_rest[start:end].split(",")]
        args = {x.split(':')[0].strip() : x.split(':')[1].strip() for x in arg_name_type}
        arg_indices = [x.split(":")[0] for x in arg_name_type]

    print(f"{temp_name = }")
    print(f"{args = }")

    i = start_line + 1
    template_lines = []
    while "___END_TEMPLATE" not in lines[i]:
        template_lines.append(lines[i])
        i += 1

    templates[temp_name] = Template(template_lines, args, arg_indices)
    print("    created template", temp_name)

    for j in range(start_line, i+1):
        lines[j] = "" 

def template_boolean_expr(s: str, template: Template, objs: dict[str, Any], prop_to_arg_map) -> bool:
    # TODO: actual expressions and not just hard coded functions
    if s.strip().startswith("___OBJ_HAS"):
        # ___OBJ_HAS(obj_name, prop_name) === prop_name in obj_name.keys()
        prop_name, prop_prop = [x.strip() for x in get_curly_outer(s, "___OBJ_HAS{").split(",")]
        if prop_name not in template.args:
            print(f"     error! argument to OBJ_HAS: {prop_name}, does not exist")
            return False
        return prop_prop in objs[prop_to_arg_map[prop_name]]
    print("     error! boolean exprs without ___OBJ_HAS is todo!")
    return False

def handle_template_gen(line: str, templates: dict[str, Template], objs: dict[str, Any]) -> str:
    MISSING_TEMPLATE_STR = "<!-- (template missing) -->"

    temp_name, end = get_curly(line)
    arg_names_s, _ = get_curly(line[end+1:])
    arg_names= [x.strip() for x in arg_names_s.split(',')]


    print("THING:", temp_name, arg_names)
    if temp_name not in templates.keys():
        print("    error! no such template:", temp_name)
        return MISSING_TEMPLATE_STR
    if len(arg_names) != len(templates[temp_name].args):
        print(f"    error! arguments to {temp_name} is incorrect (is {len(arg_names)}, requires {len(templates[temp_name].args)})")
        return MISSING_TEMPLATE_STR

    template = templates[temp_name]
    prop_to_arg_map = {}

    for i,arg in enumerate(arg_names):
        arg = arg_names[i]
        if arg in objs.keys():
            # print(arg, type(objs[arg]), objs[arg])
            param_name = template.arg_indices[i]
            param_type = template.args[param_name]

            # Type checking
            if type(objs[arg]) is dict and param_type == "json_obj":
                print("TYPE CHECKED< ")
                prop_to_arg_map[param_name] = arg
            else:
                print(f"    error! incorrect type for param {i} ({param_name}) requires {param_type}")
                return MISSING_TEMPLATE_STR
        else:
            print("    error! no such object:", arg)
            return MISSING_TEMPLATE_STR

    template_lines= template.text[:]
    new_lines = wacky_line_handler(template_lines, template, objs, prop_to_arg_map)

    return "".join(new_lines)

def wacky_line_handler(template_lines: list[str], template: Template, objs: dict[str, Any], prop_to_arg_map: dict[str, str]):
    for i in range(len(template_lines)):
        line = template_lines[i]
        if "___" in line:
            print("     !!!wacky line", line, end="")
            if "___{" in line:
                # eval?
                to_eval,_ = get_curly(line)
                var, *props = to_eval.split(".")

                print("     eval?,", to_eval)
                print("     var:", var, "props:", props)

                ok = True
                local_obj = objs[prop_to_arg_map[var]]
                for j,prop in enumerate(props):
                    if type(local_obj) is not dict or prop not in local_obj.keys():
                        print(f"     error! `{var}.{".".join(props[:j])}` does not have property `{prop}`")
                        ok = False
                        continue
                    local_obj = local_obj[prop]
                template_lines[i] = line.replace("___{"+to_eval+"}", local_obj) if ok else "<!-- (invalid prop access in template) -->"
                print("replacement:", template_lines[i], end="")
            elif "___IF{" in line:
                to_eval = get_curly_outer(line, "___IF{")
                print("to_eval:", to_eval)
                result = template_boolean_expr(to_eval, template, objs, prop_to_arg_map)

                inner_lines, stop_line = get_lines_until_string("___END_IF", i, template_lines)
                print("result of if:", result)
                if result:
                    new_lines = wacky_line_handler(inner_lines, template, objs, prop_to_arg_map)
                    template_lines[i] = "".join(new_lines)
                else:
                    template_lines[i] = ""
                for j in range(i+1, stop_line+1):
                    template_lines[j] = ""
            else:
                print("    error! unknown `___` template thing:", line)
                return ["" * len(template_lines)]
    return template_lines


def handle_json(start_line: int, lines: list[str], objs: dict[str, Any]):
    text = lines[start_line].strip()
    start = text.find("{") + 1
    end = text.find("}")

    obj_name = text[start:end]

    i = start_line + 1
    json_lines = ""
    while "___END_JSON" not in lines[i]:
        json_lines += lines[i]
        i += 1

    objs[obj_name] = json.loads(json_lines)
    print("    Created local object", obj_name)

    for j in range(start_line, i+1):
        lines[j] = ""

def handle_latest_bsky(build_dir: Path) -> str:
    try:
        with open(build_dir / "bsky_latest.txt", "r") as f:
            lines = f.readlines()

        b_date, b_post, b_post_touhou = lines

        template = f"""
        <h3>Most recent bsky posts</h3>

        <p>(last checked: {b_date} (note: checking done manually lol))</p>

        <div class="bsky_containers">
            <div class="bsky_box">
                <p>Most recent post</p>
                {b_post}
            </div>

            <div class="bsky_box">
                <p>Most recent <a href="https://bsky.app/hashtag/touhou?author=fds-t.bsky.social">#touhou</a> post</p>
                {b_post_touhou}
            </div>
        </div>
        """
        return template
    except FileNotFoundError:
        return "<!-- (bsky integration missing) -->"

def handle_imgs(line: str, build_dir: Path) -> str:
    text = line.strip()

    start = text.find("{") + 2
    end = text.find("}")

    filename = build_dir / "site" / text[start:end]

    print("    reading images from", filename)

    with open(filename, "r") as f:
        images = f.readlines()

    innerhtml = '<div id="static_thing">'
    for img in images:
        innerhtml += f'<img src="{img}">\n'
    innerhtml += '</div">'
    return innerhtml

def handle_oc_box(line: str, objs: dict[str, Any]) -> str:
    text = line.strip()
    start = text.find("{") + 1
    end = text.find("}")

    oc_name = text[start:end]

    oc: dict[str, Any] = objs[oc_name]
    details_innerhtml = ""

    if "details" in oc.keys():
        details = oc["details"]
        details_innerhtml = f'''
        <details>
            <summary>
                {details["summary"]}
            </summary>'
            <a href="{details["image"]}">
                <img class="oc_design" src="{details["image"]}"></img>
            </a>
        </details>
        '''

    innerhtml = f'''
    <div class="oc_info_box_box">
        <p><b>{oc["name"]}</b></p>
        <div class="oc_info_box">
            <img class="oc_image" src={oc["image"]}></img>
            <p>{oc["description"]}</p>
        </div>
        {details_innerhtml}
    </div>
    '''

    return innerhtml

def process_file(filename: Path, build_dir: Path):
    local_objs= {}
    local_templates = {}

    print(f"  processing {filename}! process process...")

    if not os.path.isfile(filename):
        # print("    not a file! skipping...")
        return
    elif filename.suffix != ".html":
        # print("    not a html file! skipping...")
        with open(filename, "rb") as f:
            file = f.read()
        return file

    with open(filename, "r") as f:
        lines = f.readlines()

    for i in range(len(lines)):
        line = lines[i]
        if "___" in line:
            print("   FOUND LINE TO MESS WITH:", repr(line))
            if "___BSKY_LATEST" in line:
                lines[i] = handle_latest_bsky(build_dir)
            if "___IMGS" in line:
                lines[i] = handle_imgs(line, build_dir)
            if "___JSON" in line:
                handle_json(i, lines, local_objs)
            if "___TEMPLATE" in line:
                handle_new_template(i, lines, local_templates)
            if "___GEN_TEMPLATE" in line:
                lines[i] = handle_template_gen(line, local_templates, local_objs)
            if "___OC_BOX" in line:
                lines[i] = handle_oc_box(line, local_objs)

    return lines

def index_res_dir(build_res_dir: Path):
    print("files in res:")

    art_files = []
    for x in build_res_dir.rglob("*"):
        file_path = Path(str(x).replace(str(build_res_dir), "/res"))

        if file_path.name.startswith("_"):
            print("  ", file_path, "starts with '_'! removing", x, "...")
            os.remove(x)
            continue

        print("   ", file_path, end="")

        if file_path.suffix in IMG_SUFFIXES and "/res/art" in str(file_path):
            art_files.append(file_path)
            print(" (img)")
        else:
            print()

    build_art_dir = build_res_dir / "art"
    with open(build_art_dir / "test_all.txt", "w") as f:
        f.writelines([str(file) + "\n" for file in art_files])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="generate",
        description="Generates the website"
    )
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("-i", required=True)
    parser.add_argument("-o", required=True)
    parser.add_argument("--ignore_bsky", action="store_true")
    args = parser.parse_args()

    cwd = Path(os.getcwd())
    source_site_dir: Path = cwd / args.i
    build_dir: Path       = cwd / args.o
    build_site_dir: Path  = build_dir / "site/"

    if os.path.exists(build_site_dir):
        print("Built site directory already exists!")
        print("  Removing built site directory", build_site_dir)
        shutil.rmtree(build_site_dir)

    if args.clean:
        if os.path.exists(build_dir):
            print("Build directory already exists!")
            print("  Removing build directory", build_dir)
            shutil.rmtree(build_dir)
        exit()

    build_res_dir = build_site_dir / "res/"

    shutil.copytree(cwd / "res/", build_res_dir)

    index_res_dir(build_res_dir)

    if not args.ignore_bsky:
        from generate_bsky import create_bsky_latest
        create_bsky_latest(build_dir)

    for x in source_site_dir.rglob("*"):
        file_path = Path(str(x).replace(str(source_site_dir), str(build_site_dir)))
        file_path.parent.mkdir(exist_ok=True, parents=True)

        if file_path.name.startswith("_"):
            print(file_path, "starts with '_'! ignoring...")
            continue

        lines = process_file(x, build_dir)
        if lines is not None:
            if type(lines) is bytes:
                with open(file_path, "wb") as f:
                    f.write(lines)
            elif type(lines) is list:
                with open(file_path, "w") as f:
                    f.writelines(lines)

    print("Done!")