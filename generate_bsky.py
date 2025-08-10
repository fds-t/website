from pathlib import Path
from atproto import Client
import atproto_client
from datetime import date
import requests

def curr_date() -> str:
    return date.today().isoformat()

def bsky_latest_post(client, tag=None):
    result = bsky_get_latest_actor_post(client.me.did, client, tag)
    if result is not None:
        actor_did, post_did = result
    oembed_result = bsky_oembed(f"https://bsky.app/profile/{actor_did}/post/{post_did}")
    return oembed_result if oembed_result is not None else ""

def bsky_oembed(url: str) -> str | None:
    query = {
        "url": url,
    }
    response = requests.get("https://embed.bsky.app/oembed", query)

    if response.status_code == 200:
        return response.json()["html"]
    else:
        print("Failed to get bsky embed for post:", query["url"])
        return None

def bsky_get_credentials() -> tuple[str, str]:
    with open("bsky_info") as f:
        l = f.read()
        username, password = l.split()
    return username, password

# TODO: make this less terrible
def bsky_is_tag_in_facets(facets, tag) -> bool:
    if facets is None:
        return False

    for facet in facets:
        for feature in facet.features:
            if type(feature) == atproto_client.models.app.bsky.richtext.facet.Tag:
                if feature.tag == tag:
                    return True
    return False

# TODO: this one too
def bsky_get_latest_actor_post(actor_did, client, tag=None) -> tuple[str,str] | None:
    cursor = ""
    post_did = None

    while post_did is None:
        response = client.get_author_feed(actor_did, cursor=cursor, limit=10, filter="posts_and_author_threads")
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
    b_post_touhou = bsky_latest_post(client, tag="touhou")

    return (b_date, b_post, b_post_touhou)

def create_bsky_latest(build_dir: Path):
    print("Fetching latest bsky info...")

    username, password = bsky_get_credentials()

    client = Client()
    client.login(username, password)

    bsky_latest = fetch_latest_bsky(client)

    bsky_out_file = build_dir / "bsky_latest.txt"
    print("Writing latest bsky info to", bsky_out_file)
    with open(bsky_out_file, "w") as f:
        f.writelines([(repr(str(text))[1:-1] + "\n") for text in bsky_latest])