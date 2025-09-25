import os
import sys
import requests
from pathlib import Path

def clean_site(api_key: str, build_dir: str):
    header = {"Authorization" : f"Bearer {api_key}"}
    r = requests.get("https://neocities.org/api/list", headers=header)

    if r.status_code == 200:
        j = r.json()

        cwd = Path(os.getcwd())
        build_dir: Path      = cwd / "build/"
        build_site_dir: Path = build_dir / "site/"

        local_files = set(build_site_dir.rglob("*"))
        server_files = set(map(lambda e: build_site_dir / e["path"], j["files"]))

        to_remove = []
        for file in server_files:
            if file not in local_files:
                path = Path(str(file).removeprefix(str(build_site_dir)))
                print("  Found file to remove:", path)
                to_remove.append(path)

        if len(to_remove) == 0:
            print("Nothing to do!")
        else:
            print("Removing files from server...")

            args = {"filenames[]": to_remove}
            r = requests.post("https://neocities.org/api/delete", data=args, headers=header)
            if r.status_code == 200:
                print("Successfully removed files!")
            else:
                print("Failed to remove files!")
                print(f"Status code: {r.status_code}")
                print(r.text)
    else:
        print(f"Request failed: {r.status_code}\n{r.text}")
        print("Is the correct api key loacted in 'neocities_info'?")

if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "-o":
        print("usage: clean -o build_dir")
        exit(0)

    build_dir = sys.argv[2]

    print("!!  CAUTION!!  CAUTION!!  CAUTION!!  CAUTION!!  CAUTION!!  CAUTION!!  !!")
    print("!!                                                                    !!")
    print("!!   If your res/ folder is not up to date, everything newer on the   !!")
    print("!!   server WILL be deleted!! Double check if anything's missing!!!   !!")
    print("!!                                                                    !!")
    print("!!  CAUTION!!  CAUTION!!  CAUTION!!  CAUTION!!  CAUTION!!  CAUTION!!  !!")

    try:
        if input("\nAre you sure you want to continue? [y/N] ").lower() != "y":
            print("Exiting")
            exit(0)
    except KeyboardInterrupt:
        exit(0)

    print("Cleaning site...")

    with open("neocities_info", "r") as f:
        api_key = f.read().strip()

    clean_site(api_key, build_dir)