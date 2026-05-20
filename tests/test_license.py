from unittest.mock import MagicMock, patch

from license import LicenseClient, PLANS_WITH_CLOUD


def test_license_local_mode_without_key() -> None:
    client = LicenseClient()
    client.license_key = ''
    info = client.validate()
    assert info.valid is True
    assert info.plan == 'start'
    assert info.cloud_sync_enabled is False


@patch('license.httpx.post')
def test_license_business_from_api(mock_post: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        'valid': True,
        'plan': 'business',
        'site_id': 'demo-site',
        'expires_at': '2099-01-01T00:00:00',
        'message': 'OK',
    }
    mock_post.return_value = mock_response

    client = LicenseClient()
    client.license_key = 'demo-business-key'
    info = client.validate()

    assert info.valid is True
    assert info.plan == 'business'
    assert info.cloud_sync_enabled is True
    assert 'business' in PLANS_WITH_CLOUD
