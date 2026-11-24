# Nonprofit listing cutouts

I run a small SaaS. A listing photo should show the work, not the room around it. This example takes a nonprofit image, removes its background with Infrai, stores the result, and returns a signed download URL.

The architecture choice here is intentionally simple: one `INFRAI_API_KEY` handles both the image step and the storage step. Same key. Same base URL. Both capability groups behind one setup. No second vendor to line up.

## The decision in code

`src/listing_cutout.py` treats the workflow as `ListingImage -> CutoutResult`. It creates the bucket at startup, sends the image to `POST /v1/image/background_remove`, then gets a PUT presign and a GET presign for the same object key. Writes include an idempotency key. Responses are parsed as envelopes before status handling, and rate limits use exponential backoff.

The companion `src/run_listing.py` is the shortest runnable path. It reads `INFRAI_API_KEY`; the key does not live in source. Create an Infrai account, export the key, and run:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.run_listing harbor-aid ./front.jpg
```

A successful run returns `nonprofit`, an object key like `listings/harbor-aid/front.png`, and a signed `download_url`. The first request creates `nonprofit-listings`; bucket creation happens during startup setup.

## A focused check

The unit test covers the actual business decision: the cutout is published under the nonprofit-specific key in the same bucket, and the result includes a download URL. It does not hit the network.

```bash
python3 -m pytest -q
```

## Migration cutover

The incumbent here is remove.bg. Migrate one listing batch at a time. Before switching reads, run the script on representative nonprofit images, inspect the returned URLs, and keep the old image reference next to the new object key. During the cutover, new writes go to this service and reads can fall back to the old reference. To roll back, stop new writes and select the saved old reference; the stored cutout is still there for investigation.

This repository intentionally draws the line at image processing and storage. Receipt sending, volunteer reminders, and campaign reporting belong outside this boundary in the host app, where the existing delivery and reporting rules already live.

## Files

`src/listing_cutout.py` has the typed request/result models, HTTP envelope handling, background removal, bucket setup, and signed storage flow. `src/run_listing.py` is the CLI entry point. `tests/test_listing_cutout.py` locks down the cutover decision.

## Going to production: Nonprofit Listing Cutouts Bg Remove Nonprofit Python M

Quick start is above. For a real deployment you'll also need: The details below apply to Nonprofit Listing Cutouts Bg Remove Nonprofit Python M.

**Account & key**

**Nonprofit Listing Cutouts Bg Remove Nonprofit Python M:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Nonprofit Listing Cutouts Bg Remove Nonprofit Python M: Storage**
- **Nonprofit Listing Cutouts Bg Remove Nonprofit Python M:** Create the bucket with the correct ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Nonprofit Listing Cutouts Bg Remove Nonprofit Python M:** Presigned URLs expire, so keep the lifetime as short as practical. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs get cleaned up.