import httpx

from config import settings
from libraries.database import Database
from license import LicenseInfo
from logger import logger


class CloudUploader:
    """Uploads pending measurements from SQLite to SUNHORS cloud API."""

    def __init__(self, license_info: LicenseInfo) -> None:
        self.license_info = license_info
        self.api_url = settings.cloud_api_url.rstrip('/')
        self.site_id = license_info.site_id
        self.license_key = settings.license_key

    @property
    def enabled(self) -> bool:
        return self.license_info.cloud_sync_enabled and bool(self.license_key)

    def sync_pending(self, db: Database, batch_size: int | None = None) -> int:
        if not self.enabled:
            return 0

        limit = batch_size or settings.cloud_sync_batch_size
        rows = db.get_unsynced_measurements(limit=limit)
        if not rows:
            return 0

        payload = {
            'site_id': self.site_id,
            'license_key': self.license_key,
            'measurements': rows,
        }

        try:
            response = httpx.post(
                f'{self.api_url}/v1/telemetry',
                json=payload,
                timeout=settings.cloud_request_timeout,
            )
            response.raise_for_status()
            result = response.json()
            synced_ids = result.get('synced_ids', [row['id'] for row in rows])
            db.mark_measurements_synced(synced_ids)
            logger.info(f'Cloud sync OK: {len(synced_ids)} measurements')
            return len(synced_ids)
        except Exception as error:
            logger.error(f'Cloud sync failed: {error}', exc_info=True)
            return 0
