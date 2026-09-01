from dataclasses import dataclass
from datetime import date
from typing import Dict

from infrai_storage import InfraiStorage


@dataclass(frozen=True)
class MatterIntake:
    matter_id: str
    client_name: str
    document_name: str
    deadline: date


class LegalAssetService:
    def __init__(self, storage: InfraiStorage, bucket: str = "legal-matter-assets"):
        self.storage, self.bucket = storage, bucket

    def upload_request(self, matter: MatterIntake) -> Dict[str, str]:
        key = f"matters/{matter.matter_id}/{matter.document_name}"
        signed = self.storage.presign(self.bucket, key, {
            "op": "put", "expires_seconds": 600, "content_type": "application/pdf",
            "max_bytes": 20_000_000, "idempotency_key": f"intake-{matter.matter_id}",
        })
        return {"matter_id": matter.matter_id, "key": key, "upload_url": signed["url"]}

    def delivery_request(self, matter: MatterIntake) -> Dict[str, str]:
        key = f"matters/{matter.matter_id}/{matter.document_name}"
        found = self.storage.head(self.bucket, key).get("found", False)
        if not found:
            return {"status": "awaiting_upload", "matter_id": matter.matter_id}
        signed = self.storage.presign(self.bucket, key, {
            "op": "get", "expires_seconds": 300, "response_disposition": "attachment",
        })
        return {"status": "ready", "matter_id": matter.matter_id, "download_url": signed["url"]}

    @staticmethod
    def deadline_follow_up(matter: MatterIntake, today: date) -> str:
        days = (matter.deadline - today).days
        return "follow_up" if days <= 3 else "on_track"
