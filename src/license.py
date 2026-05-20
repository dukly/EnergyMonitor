from dataclasses import dataclass
from datetime import datetime

import httpx

from config import settings
from logger import logger

PLANS_WITH_CLOUD = frozenset({'business', 'pro', 'partner'})


@dataclass
class LicenseInfo:
    valid: bool
    plan: str
    site_id: str
    expires_at: str | None
    cloud_sync_enabled: bool
    message: str = ''


class LicenseClient:
    """Validates subscription against SUNHORS license API."""

    def __init__(self) -> None:
        self.site_id = settings.site_id
        self.license_key = settings.license_key
        self.api_url = settings.license_api_url.rstrip('/')

    def validate(self) -> LicenseInfo:
        if not self.license_key:
            return LicenseInfo(
                valid=True,
                plan='start',
                site_id=self.site_id,
                expires_at=None,
                cloud_sync_enabled=False,
                message='No license key: local-only mode (Start)',
            )

        try:
            response = httpx.post(
                f'{self.api_url}/v1/license/validate',
                json={'site_id': self.site_id, 'license_key': self.license_key},
                timeout=settings.cloud_request_timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as error:
            logger.warning(f'License check failed, falling back to local mode: {error}')
            return LicenseInfo(
                valid=True,
                plan='start',
                site_id=self.site_id,
                expires_at=None,
                cloud_sync_enabled=False,
                message='License API unavailable; local-only mode',
            )

        plan = str(payload.get('plan', 'start')).lower()
        return LicenseInfo(
            valid=bool(payload.get('valid', False)),
            plan=plan,
            site_id=str(payload.get('site_id', self.site_id)),
            expires_at=payload.get('expires_at'),
            cloud_sync_enabled=plan in PLANS_WITH_CLOUD and bool(payload.get('valid', False)),
            message=str(payload.get('message', '')),
        )

    def is_expired(self, expires_at: str | None) -> bool:
        if not expires_at:
            return False
        try:
            return datetime.fromisoformat(expires_at) < datetime.now()
        except ValueError:
            return False
