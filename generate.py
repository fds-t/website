import os
import shutil
from pathlib import Path
from datetime import date
import requests
import argparse

IMG_SUFFIXES = { ".png", ".jpg", ".jpeg", ".bmp" }


def curr_date() -> str:
    return date.today().isoformat()

def bsky_latest_post(client):
    actor_did, post_did = bsky_get_latest_actor_post(client.me.did, client)
    return bsky_oembed(f"https://bsky.app/profile/{actor_did}/post/{post_did}")["html"]

def bsky_latest_post_touhou(client):
    actor_did, post_did = bsky_get_latest_actor_post(client.me.did, client, tag="touhou")
    return bsky_oembed(f"https://bsky.app/profile/{actor_did}/post/{post_did}")["html"]

def bsky_oembed(url: str):
    query = {
        "url": url,
    }
    response = requests.get("https://embed.bsky.app/oembed", query)

    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to get bsky embed for post:", query["url"])
        return None

def bsky_get_credentials() -> tuple[str, str]:
    with open("bsky_info") as f:
        l = f.read()
        username, password = l.split()
    return username, password

# TODO: extremely bad code
def bsky_is_tag_in_facets(facets, tag):
    if facets is None:
        return False

    for facet in facets:
        for feature in facet.features:
            if type(feature) == atproto_client.models.app.bsky.richtext.facet.Tag:
                if feature.tag == tag:
                    return True
    return False

def bsky_get_latest_actor_post(actor_did, client, tag=None):
    cursor = ""
    post_did = None

    while post_did is None:
        response = client.get_author_feed(username, cursor=cursor, limit=10, filter="posts_and_author_threads")
        feed = response.feed
        cursor = response.cursor
        for postview in feed:
            if postview.post.author.did == actor_did:
                if tag is None or bsky_is_tag_in_facets(postview.post.record.facets, tag):
                    actor_did, post_did = postview.post.author.did, postview.post.uri.split("/")[-1]
                    return actor_did, post_did
            else:
                # print(f"{postview.post.author.did} != {actor_did}")
                pass

def fetch_latest_bsky(client):
    b_date = curr_date()
    b_post = bsky_latest_post(client)
    b_post_touhou = bsky_latest_post_touhou(client)

    return (b_date, b_post, b_post_touhou)

def handle_latest_bsky(build_dir: Path):
    with open(build_dir / "bsky_latest.txt", "r") as f:
        lines = f.readlines()

    b_date, b_post, b_post_touhou = lines

    template = f"""
    <h3>Most recent bsky posts</h3>
        <p>(last checked: {b_date})</p>

        <div class="bsky_containers">
            <div class="bsky_box">
                <p>Most recent</p>
                {b_post}
            </div>

            <div class="bsky_box">
                <p>Most recent #touhou</p>
                {b_post_touhou}
            </div>
        </div>
    """
    return template

def process_file(filename: Path, build_dir: Path):
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
    for i,line in enumerate(lines):
        if "___" in line:
            print("FOUND LINE TO MESS WITH:", repr(line))
            if "___BSKY_LATEST" in line:
                lines[i] = handle_latest_bsky(build_dir)
    return lines

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
    build_dir: Path = cwd / args.o
    out_site: Path = build_dir / "site/"

    if os.path.exists(out_site):
        print("Built site directory already exists!")
        print("  Removing built site directory", out_site)
        shutil.rmtree(out_site)

    if args.clean:
        if os.path.exists(build_dir):
            print("Build directory already exists!")
            print("  Removing build directory", build_dir)
            shutil.rmtree(build_dir)
        exit()

    source_dir: Path = Path(os.getcwd()) / args.i

    out_res = out_site / "res/"

    shutil.copytree(cwd / "res/", out_res)

    print("files in res:")
    img_files = []
    for x in out_res.rglob("*"):
        file_path = Path(str(x).replace(str(out_res), "/res"))

        print("   ", file_path, end="")

        if file_path.suffix in IMG_SUFFIXES:
            img_files.append(file_path)
            print(" (img)")
        else:
            print()


    with open(out_res / "art" / "test_all.txt", "w") as f:
        f.writelines([str(file) + "\n" for file in img_files])

    if not args.ignore_bsky:
        print("Handling bsky integration...")
        from atproto import Client
        import atproto_client

        username, password = bsky_get_credentials()

        client = Client()
        client.login(username, password)

        bsky_latest = fetch_latest_bsky(client)

        with open(build_dir / "bsky_latest.txt", "w") as f:
            f.writelines([(repr(str(text))[1:-1] + "\n") for text in bsky_latest])

    for x in source_dir.rglob("*"):
        # print(Path(str(x).replace(str(source_dir), str(build_dir))))
        lines = process_file(x, build_dir)
        if lines is not None:
            file_path = Path(str(x).replace(str(source_dir), str(out_site)))
            file_path.parent.mkdir(exist_ok=True, parents=True)
            if type(lines) is bytes:
                with open(file_path, "wb") as f:
                    f.write(lines)
            elif type(lines) is list:
                with open(file_path, "w") as f:
                    f.writelines(lines)

    print("Done!")