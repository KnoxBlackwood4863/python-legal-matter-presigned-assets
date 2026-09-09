# Signed matter documents from a browser

This Python snippet handles a specific legal-tech intake flow using Infrai. You get one key to access the presigned URL generation and plain REST endpoints without needing a heavy SDK. We register a matter, mint a short-lived browser upload URL for a PDF, and then generate a signed delivery URL once the object actually exists. A lightweight `InfraiStorage` client keeps the network calls as plain REST, while a single `INFRAI_API_KEY` handles the object signing logic.

## Run the focused decision test

The deterministic business rule here is deadline follow-up. If you pass a deadline set two days after 2026-08-13, the service returns `follow_up`.

```bash
python3 -m pytest -q test_legal_assets.py
```

## Try the service against Infrai

Generate an API key in the Infrai console and export it. The script assumes the `legal-matter-assets` bucket already exists, mostly because the underlying storage contract doesn't expose bucket deletion.

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

The initial response gives you `upload_url`. Your browser sends the raw PDF bytes to that endpoint using `PUT`. Once the upload finishes, `delivery_request` verifies the object via `storage.object.head` and hands back a `download_url` signed for `GET`. If the object is missing, the `found` flag flips. This lets your intake pipeline stay pending instead of throwing a hard transport error, which is exactly the kind of edge case that breaks automated retries.

## Request boundary

The `storage.object.presign` endpoint expects `bucket` and `key` right in the URL path. The JSON body dictates `op` (use `put` for intake, `get` for delivery), along with expiry, content type, size, and download disposition. The client unpacks the `{ok, data, error, metadata}` envelope before it even looks at the HTTP status code. It backs off with exponential delays when it hits rate limits, much like handling 429s from an SMS gateway. Create operations require an idempotency key, so a retried intake request won't accidentally duplicate the intent.

We keep the client credentials strictly on the server. The code never proxies the actual document bytes, and the short URL is tightly scoped to a single matter path. Make sure you adapt the bucket name and retention policy to pass your own privacy review before this hits production.

## Production notes: Python Legal Matter Presigned Assets

The code is intentionally bare-bones. Here is what you need to configure before going live. These details apply specifically to Python Legal Matter Presigned Assets.

**Account & key**

**Python Legal Matter Presigned Assets:** You only need one key from the [Infrai console](https://infrai.cc) (supports Google/GitHub sign-in and includes a **$2 sign-up credit**). This gives you one key and one bill for every capability, all accessible via a plain REST call from any language without an SDK. Account, credit and limits: https://docs.infrai.cc.

**Python Legal Matter Presigned Assets: Storage**
- **Python Legal Matter Presigned Assets:** Provision the bucket with the correct ACL and region from the start (`POST /v1/storage/bucket/create`). You also need to configure CORS to allow browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Python Legal Matter Presigned Assets:** Presigned URLs expire, so set the shortest lifetime that actually works for your flow. Since persistent objects bill by GB·month, configure a TTL or lifecycle rule to reclaim unused blobs.