import sqlite3
from pathlib import Path
from typing import Any

from logger import logger

SCHEMA_COLUMNS: dict[str, str] = {
    'synced': 'INTEGER NOT NULL DEFAULT 0',
    'status_text': 'TEXT',
    'error_text': 'TEXT',
}


class Database:
    """SQLite storage for inverter measurements."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(self.database_path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self._initialize_database()

    def _initialize_database(self) -> None:
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                voltage_dc REAL,
                current_dc REAL,
                power_ac REAL,
                temp REAL,
                freq REAL,
                pf REAL,
                energy_total REAL,
                energy_day REAL,
                runtime REAL,
                status INTEGER,
                error INTEGER,
                status_text TEXT,
                error_text TEXT,
                synced INTEGER NOT NULL DEFAULT 0
            )
        ''')
        self.conn.commit()

        columns = self._table_columns()

        if 'id' not in columns:
            self._migrate_legacy_table(columns)
            columns = self._table_columns()

        self._ensure_columns(columns)

        self.cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_measurements_timestamp
            ON measurements(timestamp)
        ''')
        self.cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_measurements_synced
            ON measurements(synced)
        ''')
        self.conn.commit()

    def _table_columns(self) -> set[str]:
        self.cur.execute('PRAGMA table_info(measurements)')
        return {row[1] for row in self.cur.fetchall()}

    def _ensure_columns(self, columns: set[str]) -> None:
        for column_name, column_type in SCHEMA_COLUMNS.items():
            if column_name in columns:
                continue
            self.cur.execute(f'ALTER TABLE measurements ADD COLUMN {column_name} {column_type}')
            self.conn.commit()
            logger.info(f'Added missing column: {column_name}')

    def _migrate_legacy_table(self, columns: set[str]) -> None:
        logger.info('Migrating legacy measurements table to the new schema')

        self.cur.execute('ALTER TABLE measurements RENAME TO measurements_legacy')
        self.cur.execute('''
            CREATE TABLE measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                voltage_dc REAL,
                current_dc REAL,
                power_ac REAL,
                temp REAL,
                freq REAL,
                pf REAL,
                energy_total REAL,
                energy_day REAL,
                runtime REAL,
                status INTEGER,
                error INTEGER,
                status_text TEXT,
                error_text TEXT,
                synced INTEGER NOT NULL DEFAULT 0
            )
        ''')

        legacy_columns = [
            column for column in (
                'timestamp', 'voltage_dc', 'current_dc', 'power_ac', 'temp', 'freq', 'pf',
                'energy_total', 'energy_day', 'runtime', 'status', 'error',
            )
            if column in columns
        ]
        if legacy_columns:
            column_list = ', '.join(legacy_columns)
            self.cur.execute(f'''
                INSERT INTO measurements ({column_list})
                SELECT {column_list}
                FROM measurements_legacy
            ''')

        self.cur.execute('DROP TABLE measurements_legacy')
        self.conn.commit()

    def save_measurement(
        self,
        timestamp: str,
        voltage_dc: float | None,
        current_dc: float | None,
        power_ac: float | None,
        temp: float | None,
        freq: float | None,
        pf: float | None,
        energy_total: float | None,
        energy_day: float | None,
        runtime: float | None,
        status: int | None,
        error: int | None,
        status_text: str | None = None,
        error_text: str | None = None,
    ) -> int:
        self.cur.execute('''
            INSERT INTO measurements (
                timestamp, voltage_dc, current_dc, power_ac, temp, freq, pf,
                energy_total, energy_day, runtime, status, error, status_text, error_text, synced
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (
            timestamp,
            voltage_dc,
            current_dc,
            power_ac,
            temp,
            freq,
            pf,
            energy_total,
            energy_day,
            runtime,
            status,
            error,
            status_text,
            error_text,
        ))
        self.conn.commit()
        measurement_id = int(self.cur.lastrowid)

        logger.info(
            (
                f'Measurement saved [#{measurement_id}]: {timestamp}, {voltage_dc} V, {current_dc} A, '
                f'{power_ac} W, Status: {status} ({status_text}), Error: {error} ({error_text})'
            )
        )
        return measurement_id

    def get_unsynced_measurements(self, limit: int = 50) -> list[dict[str, Any]]:
        self.cur.execute('''
            SELECT id, timestamp, voltage_dc, current_dc, power_ac, temp, freq, pf,
                   energy_total, energy_day, runtime, status, error, status_text, error_text
            FROM measurements
            WHERE synced = 0
            ORDER BY id ASC
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in self.cur.fetchall()]

    def mark_measurements_synced(self, measurement_ids: list[int]) -> None:
        if not measurement_ids:
            return
        placeholders = ', '.join('?' for _ in measurement_ids)
        self.cur.execute(
            f'UPDATE measurements SET synced = 1 WHERE id IN ({placeholders})',
            measurement_ids,
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
