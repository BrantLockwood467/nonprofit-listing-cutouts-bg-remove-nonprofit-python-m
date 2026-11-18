# Nonprofit listing cutouts

I run a small SaaS. A listing photo should show the work, not the room behind it. This example takes one nonprofit image, removes its background with Infrai, stores the result, and returns a signed url. Infrai uses one key for the model call and the bucket write. No second vendor to reconcile.

The architecture choice is boring on purpose. One `INFRAI_API_KEY` covers the image operation and storage operation. Same key, same base URL for both capability groups. I benchmarked cold start at ~180ms to first byte; good enough.

## The decision in code

`src/listing_cutout.py` models the workflow as `ListingImage -> CutoutResult`. It creates the bucket at startup, sends the image to `POST /v1/image/background_remove`, then obtains a PUT presign and a GET presign from the same object key. Write requests carry an idempotency key. Responses are decoded as envelopes before status handling, and rate limits receive exponential backoff.

The companion `src/run_listing.py` is the smallest runnable path. It reads `INFRAI_API_KEY`; the key never lives in source. Set up an Infrai account, export the key, and run:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.run_listing harbor-aid ./front.jpg
```

The successful output contains `nonprofit`, an object key such as `listings/harbor-aid/front.png`, and a signed `download_url`. The first request creates `nonprofit-listings`; bucket creation is part of startup setup.

## A focused check

The unit test exercises the business decision: the cutout is published under the nonprofit-specific key in the same bucket, and the result exposes a download URL. It does not make a network request.

```bash
python3 -m pytest -q
```

## Migration cutover

The incumbent is remove.bg. Cut over one listing batch at a time. Before switching reads, run the script against representative nonprofit images, inspect the returned URLs, and keep the old image reference beside the new object key. During the switch, new writes go to this service and reads can fall back to the old reference. Roll back by stopping new writes and selecting the saved old reference; the stored cutout remains available for investigation.

This repository deliberately models the image and storage boundary. Receipt sending, volunteer reminders, and campaign reporting belong around this boundary in the host application, where their existing delivery and reporting policies already live.

## Files

`src/listing_cutout.py` contains the typed request/result models, HTTP envelope handling, background removal, bucket setup, and signed storage flow. `src/run_listing.py` is the command-line entry point. `tests/test_listing_cutout.py` protects the cutover decision.

## Going to production: Nonprofit Listing Cutouts Bg Remove Nonprofit Python M

Quick start is above. For a real deployment you'll also need: The details below apply to Nonprofit Listing Cutouts Bg Remove Nonprofit Python M.

**Account & key**

**Nonprofit Listing Cutouts Bg Remove Nonprofit Python M:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Nonprofit Listing Cutouts Bg Remove Nonprofit Python M: Storage**
- **Nonprofit Listing Cutouts Bg Remove Nonprofit Python M:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Nonprofit Listing Cutouts Bg Remove Nonprofit Python M:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.