from datetime import datetime, timedelta

# Demo license store for MVP (replace with billing DB in production)
LICENSES: dict[str, dict] = {
    'demo-business-key': {
        'site_id': 'demo-site',
        'plan': 'business',
        'valid': True,
        'expires_at': (datetime.utcnow() + timedelta(days=365)).isoformat(),
    },
    'demo-start-key': {
        'site_id': 'demo-site',
        'plan': 'start',
        'valid': True,
        'expires_at': (datetime.utcnow() + timedelta(days=365)).isoformat(),
    },
}


def validate_license(site_id: str, license_key: str) -> dict:
    record = LICENSES.get(license_key)
    if not record:
        return {
            'valid': False,
            'site_id': site_id,
            'plan': 'start',
            'expires_at': None,
            'message': 'Unknown license key',
        }

    if record['site_id'] != site_id:
        return {
            'valid': False,
            'site_id': site_id,
            'plan': 'start',
            'expires_at': None,
            'message': 'License key does not match site_id',
        }

    return {
        'valid': record['valid'],
        'site_id': record['site_id'],
        'plan': record['plan'],
        'expires_at': record['expires_at'],
        'message': 'OK',
    }
