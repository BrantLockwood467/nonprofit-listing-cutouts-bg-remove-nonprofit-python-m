import base64

from src.listing_cutout import CutoutResult, ListingImage, publish_listing_cutout


class FakeClient:
    def __init__(self):
        self.calls = []

    def ensure_bucket(self, bucket):
        self.calls.append(("bucket", bucket))

    def remove_background(self, image):
        self.calls.append(("remove", image.nonprofit))
        return base64.b64encode(b"cutout").decode()

    def store_and_sign(self, bucket, key, image):
        self.calls.append(("store", bucket, key, image))
        return "https://download.example/cutout.png"


def test_listing_is_published_to_the_same_bucket_after_cutout():
    client = FakeClient()
    result = publish_listing_cutout(client, ListingImage("harbor-aid", "front.jpg", "source"))
    assert isinstance(result, CutoutResult)
    assert result.object_key == "listings/harbor-aid/front.png"
    assert result.download_url.endswith("cutout.png")
    assert client.calls == [
        ("bucket", "nonprofit-listings"),
        ("remove", "harbor-aid"),
        ("store", "nonprofit-listings", "listings/harbor-aid/front.png", base64.b64encode(b"cutout").decode()),
    ]
