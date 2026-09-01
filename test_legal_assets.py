from datetime import date

from legal_assets import LegalAssetService, MatterIntake


class FakeStorage:
    def __init__(self, found=False): self.found = found
    def create_bucket(self, name): self.bucket = name
    def presign(self, bucket, key, body): return {"url": f"https://signed/{key}"}
    def head(self, bucket, key): return {"ok": True, "found": self.found}


def test_deadline_follow_up_is_due_within_three_days():
    matter = MatterIntake("m-17", "Ada Health", "consent.pdf", date(2026, 8, 15))
    service = LegalAssetService(FakeStorage())
    assert service.deadline_follow_up(matter, date(2026, 8, 13)) == "follow_up"

