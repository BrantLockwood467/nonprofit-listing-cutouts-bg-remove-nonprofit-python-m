import argparse
import base64
import json
from pathlib import Path

from .listing_cutout import ListingImage, client_from_environment, publish_listing_cutout


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a nonprofit listing cutout")
    parser.add_argument("nonprofit")
    parser.add_argument("image")
    args = parser.parse_args()
    encoded = base64.b64encode(Path(args.image).read_bytes()).decode("ascii")
    image = ListingImage(args.nonprofit, Path(args.image).name, encoded)
    result = publish_listing_cutout(client_from_environment(), image)
    print(json.dumps({"nonprofit": result.nonprofit, "object_key": result.object_key, "download_url": result.download_url}))


if __name__ == "__main__":
    main()
