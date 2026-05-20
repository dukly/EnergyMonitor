from unittest.mock import MagicMock, patch

from libraries.database import Database
from license import LicenseInfo
from sync.cloud_uploader import CloudUploader


def test_uploader_disabled_for_start_plan(tmp_path) -> None:
    db = Database(str(tmp_path / 'test.db'))
    info = LicenseInfo(True, 'start', 'demo-site', None, False)
    uploader = CloudUploader(info)
    assert uploader.enabled is False
    assert uploader.sync_pending(db) == 0
    db.close()


@patch('sync.cloud_uploader.httpx.post')
def test_uploader_syncs_rows(mock_post: MagicMock, tmp_path) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {'synced_ids': [1]}
    mock_post.return_value = mock_response

    db = Database(str(tmp_path / 'test.db'))
    measurement_id = db.save_measurement(
        timestamp='2026-05-20 12:00:00',
        voltage_dc=230.0,
        current_dc=5.0,
        power_ac=1000.0,
        temp=40.0,
        freq=50.0,
        pf=0.98,
        energy_total=100.0,
        energy_day=5.0,
        runtime=10.0,
        status=1,
        error=0,
        status_text='OK',
        error_text='None',
    )

    info = LicenseInfo(True, 'business', 'demo-site', None, True)
    uploader = CloudUploader(info)
    uploader.license_key = 'demo-business-key'

    synced = uploader.sync_pending(db)
    assert synced == 1

    rows = db.get_unsynced_measurements()
    assert rows == [] or measurement_id not in [row['id'] for row in rows]
    db.close()
