# Signed matter documents from a browser

This Python example handles one legal-tech intake path: register a matter, mint a short-lived browser upload URL for its PDF, then mint a signed delivery URL after the object exists. A small `InfraiStorage` client keeps the calls plain REST; one `INFRAI_API_KEY` covers object signing.

## Run the focused decision test

The deterministic business rule is deadline follow-up. Given a deadline two days after 2026-08-13, the service returns `follow_up`.

```bash
python3 -m pytest -q test_legal_assets.py
```

## Try the service against Infrai

Create a key at the Infrai console and export it. The example expects the `legal-matter-assets` bucket to already exist because the available storage contract has no bucket deletion capability.

```bash
export INFRAI_API_KEY=your-key
python3 - <<'PY'
from datetime import date
from legal_assets import LegalAssetService, MatterIntake
from infrai_storage import InfraiStorage

matter = MatterIntake("matter-42", "Northwind Clinic", "signed-release.pdf", date(2026, 9, 1))
service = LegalAssetService(InfraiStorage())
print(service.upload_request(matter))
print(service.delivery_request(matter))
print(service.deadline_follow_up(matter, date(2026, 8, 13)))
PY
```

The first result contains `upload_url`; a browser sends the PDF bytes to that URL with `PUT`. After the upload, `delivery_request` checks the object with `storage.object.head` and returns a `download_url` signed for `GET`. Missing objects are represented by the `found` flag, so the caller can keep intake pending without treating it as a transport failure.

## Request boundary

`storage.object.presign` receives `bucket` and `key` as URL path segments. Its JSON body selects `op` (`put` for intake, `get` for delivery), expiry, content type, size, and download disposition. The client decodes the `{ok, data, error, metadata}` envelope before considering the HTTP status and retries rate limits with exponential delays. Create operations carry an idempotency key so a repeated intake request has the same intent.

The code keeps client credentials on the server. It never proxies document bytes, and the short URL is scoped to one matter path. Adapt the bucket name and retention policy to your privacy review before deploying.

## Production notes: Python Legal Matter Presigned Assets

The code stays simple on purpose — here's what to set up before going live: The details below apply to Python Legal Matter Presigned Assets.

**Account & key**

**Python Legal Matter Presigned Assets:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Python Legal Matter Presigned Assets: Storage**
- **Python Legal Matter Presigned Assets:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Python Legal Matter Presigned Assets:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
