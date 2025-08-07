import re
import os
import shutil
from pathlib import Path
from datetime import date
import requests
import argparse

re.compile("")

def curr_date() -> str:
    return date.today().isoformat()

def latest_bsky(client):
    actor_did, post_did = bsky_get_latest_actor_post(client.me.did, client)
    return bsky_oembed(f"https://bsky.app/profile/{actor_did}/post/{post_did}")["html"]

def latest_bsky_touhou(client):
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

client = None

def process_file(filename: Path):
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
            if "___CURR_DATE" in line:
                lines[i] = line.replace("___CURR_DATE", curr_date())
            if "___BSKY_MOST_RECENT" in line:
                lines[i] = line.replace("___BSKY_MOST_RECENT", latest_bsky(client))
            if "___BSKY_MOST_RECENT_TOUHOU" in line:
                lines[i] = line.replace("___BSKY_MOST_RECENT_TOUHOU", latest_bsky_touhou(client))
    return lines

if __name__ == "__main__":

    from atproto import Client
    import atproto_client

    username, password = bsky_get_credentials()

    client = Client()
    client.login(username, password)

    parser = argparse.ArgumentParser(
        prog="generate",
        description="Generates the website"
    )
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("-i", required=True)
    parser.add_argument("-o", required=True)
    args = parser.parse_args()

    build_dir: Path = Path(os.getcwd()) / args.o

    if os.path.exists(build_dir):
        print("Build directory already exists!")
        print("  Removing build directory", build_dir)
        shutil.rmtree(build_dir)

    if args.clean:
        exit()

    source_dir: Path = Path(os.getcwd()) / args.i

    for x in source_dir.rglob("*"):
        # print(Path(str(x).replace(str(source_dir), str(build_dir))))
        lines = process_file(x)
        if lines is not None:
            file_path = Path(str(x).replace(str(source_dir), str(build_dir)))
            file_path.parent.mkdir(exist_ok=True, parents=True)
            if type(lines) is bytes:
                with open(file_path, "wb") as f:
                    f.write(lines)
            elif type(lines) is list:
                with open(file_path, "w") as f:
                    f.writelines(lines)
    print("Done!")