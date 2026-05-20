from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.database import SessionLocal, TelemetryRow, init_db
from app.licenses import validate_license

app = FastAPI(
    title='SUNHORS Energy Cloud API',
    description='MVP ingest and license API for САНХОРС Мониторинг',
    version='0.1.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


class LicenseRequest(BaseModel):
    site_id: str
    license_key: str


class TelemetryPayload(BaseModel):
    site_id: str
    license_key: str
    measurements: list[dict[str, Any]] = Field(default_factory=list)


@app.on_event('startup')
def on_startup() -> None:
    init_db()


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok', 'service': 'sunhors-cloud'}


@app.post('/v1/license/validate')
def license_validate(body: LicenseRequest) -> dict[str, Any]:
    return validate_license(body.site_id, body.license_key)


@app.post('/v1/telemetry')
def ingest_telemetry(body: TelemetryPayload) -> dict[str, Any]:
    license_info = validate_license(body.site_id, body.license_key)
    if not license_info['valid']:
        raise HTTPException(status_code=403, detail=license_info['message'])

    if license_info['plan'] not in ('business', 'pro', 'partner'):
        raise HTTPException(status_code=403, detail='Cloud sync requires Business plan or higher')

    session = SessionLocal()
    synced_ids: list[int] = []

    try:
        for row in body.measurements:
            measurement_id = int(row['id'])
            session.add(TelemetryRow(
                site_id=body.site_id,
                agent_measurement_id=measurement_id,
                timestamp=str(row['timestamp']),
                voltage_dc=row.get('voltage_dc'),
                current_dc=row.get('current_dc'),
                power_ac=row.get('power_ac'),
                temp=row.get('temp'),
                freq=row.get('freq'),
                pf=row.get('pf'),
                energy_total=row.get('energy_total'),
                energy_day=row.get('energy_day'),
                runtime=row.get('runtime'),
                status=row.get('status'),
                error=row.get('error'),
                status_text=row.get('status_text'),
                error_text=row.get('error_text'),
                received_at=datetime.utcnow(),
            ))
            synced_ids.append(measurement_id)
        session.commit()
    finally:
        session.close()

    return {'synced_ids': synced_ids, 'count': len(synced_ids)}


@app.get('/v1/sites/{site_id}/metrics')
def site_metrics(site_id: str, limit: int = 100) -> dict[str, Any]:
    session = SessionLocal()
    try:
        rows = (
            session.query(TelemetryRow)
            .filter(TelemetryRow.site_id == site_id)
            .order_by(TelemetryRow.id.desc())
            .limit(limit)
            .all()
        )
        measurements = [
            {
                'timestamp': row.timestamp,
                'power_ac': row.power_ac,
                'energy_day': row.energy_day,
                'status': row.status,
                'status_text': row.status_text,
                'error': row.error,
                'error_text': row.error_text,
            }
            for row in reversed(rows)
        ]
    finally:
        session.close()

    latest = measurements[-1] if measurements else None
    return {'site_id': site_id, 'latest': latest, 'measurements': measurements}
