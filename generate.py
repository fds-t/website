import os
import shutil
import argparse
import json
from pathlib import Path
from typing import Any

IMG_SUFFIXES = { ".png", ".jpg", ".jpeg", ".bmp", ".gif" }

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