import sys
import requests
import hashlib
from pathlib import Path

ILLEGAL_FILE_TYPES = {".DS_Store"}

def hash_file(filename: Path) -> str|None:
    if filename.is_dir():
        return None

    with open(filename, "rb") as f:
        digest = hashlib.file_digest(f, "sha1")

    return digest.hexdigest()

def clean_site(api_key: str, build_dir: str):
    header = {"Authorization" : f"Bearer {api_key}"}
    r = requests.get("https://neocities.org/api/list", headers=header)

    if r.status_code == 200:
        j = r.json()

        build_dir: Path      = Path(build_dir)
        build_site_dir: Path = build_dir / "site/"

        local_files: set[Path]  = set(build_site_dir.rglob("*"))
        server_files: set[Path] = set(map(lambda e: build_site_dir / e["path"], j["files"]))

        to_remove: list[Path] = []
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
        print("Is the correct api key located in 'neocities_info'?")

def upload_site(api_key: str, build_dir: str):
    header = {"Authorization" : f"Bearer {api_key}"}
    r = requests.get("https://neocities.org/api/list", headers=header)

    if r.status_code == 200:
        j = r.json()

        build_dir: Path      = Path(build_dir)
        build_site_dir: Path = build_dir / "site/"

        local_files = set(build_site_dir.rglob("*"))
        local_files_m = set(map(lambda f: (f, hash_file(f)), local_files))

        server_files = set(
            map(
                lambda e: (
                    build_site_dir / e["path"],
                    e["sha1_hash"] if not e["is_directory"] else None
                ),
                j["files"]
            )
        )

        to_handle: list[tuple[Path,Path]] = []
        for (local_path, hash) in local_files_m:
            if (local_path, hash) not in server_files:
                server_path = Path(str(local_path).removeprefix(str(build_site_dir)))
                if server_path.suffix in ILLEGAL_FILE_TYPES or server_path.name == ".DS_Store":
                    print("   Ignoring illegal file:", server_path)
                elif local_path.is_dir():
                    print("   Ignoring directory:", server_path)
                else:
                    print("  Found file to upload:", server_path)
                    to_handle.append((server_path, local_path))

        if len(to_handle) == 0:
            print("Nothing to do!")
        else:
            print("Uploading files...")

            args = {str(server_path): open(local_path, "rb") for (server_path, local_path) in to_handle}
            r = requests.post(f"https://neocities.org/api/upload", files=args, headers=header)
            if r.status_code == 200:
                print("Successfully uploaded files!")
            else:
                print("Failed to upload files!")
                print(f"Status code: {r.status_code}")
                print(r.text)
    else:
        print(f"Request failed: {r.status_code}\n{r.text}")
        print("Is the correct api key located in 'neocities_info'?")

def print_clean_warning():
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

if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[2] != "-o" or sys.argv[1] not in ["upload", "clean", "cleanupload"]:
        print("usage: neo [upload|clean|cleanupload] -o build_dir")
        exit(0)

    action = sys.argv[1]
    build_dir = sys.argv[3]

    with open("neocities_info", "r") as f:
        api_key = f.read().strip()

    match action:
        case "clean":
            print_clean_warning()
            print("Cleaning site...")
            clean_site(api_key, build_dir)
        case "upload":
            print("Uploading site...")
            upload_site(api_key, build_dir)
        case "cleanupload":
            print_clean_warning()
            print("Cleaning site...")
            clean_site(api_key, build_dir)

            print("\nUploading site...")
            upload_site(api_key, build_dir)
        case _:
            print("what..?")
