import sqlite3
from pathlib import Path

from logger import logger

SCHEMA_COLUMNS: dict[str, str] = {
    'status_text': 'TEXT',
    'error_text': 'TEXT',
}

MEASUREMENT_COLUMNS: tuple[str, ...] = (
    'timestamp',
    'voltage_dc',
    'current_dc',
    'power_ac',
    'temp',
    'freq',
    'pf',
    'energy_total',
    'energy_day',
    'runtime',
    'status',
    'error',
)


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
        self._create_measurements_table(if_not_exists=True)
        self.conn.commit()

        columns = self._table_columns()

        if self._table_exists('measurements_legacy'):
            self._recover_legacy_table(columns)
            columns = self._table_columns()
        elif 'id' not in columns:
            self._migrate_legacy_table(columns)
            columns = self._table_columns()

        self._ensure_columns(columns)

        self.cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_measurements_timestamp
            ON measurements(timestamp)
        ''')
        self.conn.commit()

    def _table_columns(self) -> set[str]:
        self.cur.execute('PRAGMA table_info(measurements)')
        return {row[1] for row in self.cur.fetchall()}

    def _table_exists(self, table_name: str) -> bool:
        self.cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        )
        return self.cur.fetchone() is not None

    def _create_measurements_table(self, if_not_exists: bool = False) -> None:
        clause = 'IF NOT EXISTS ' if if_not_exists else ''
        self.cur.execute(f'''
            CREATE TABLE {clause}measurements (
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
                error_text TEXT
            )
        ''')

    def _ensure_columns(self, columns: set[str]) -> None:
        for column_name, column_type in SCHEMA_COLUMNS.items():
            if column_name in columns:
                continue
            self.cur.execute(f'ALTER TABLE measurements ADD COLUMN {column_name} {column_type}')
            self.conn.commit()
            logger.info(f'Added missing column: {column_name}')

    def _migrate_legacy_table(self, columns: set[str]) -> None:
        logger.info('Migrating legacy measurements table to the new schema')

        self.cur.execute('BEGIN IMMEDIATE')
        try:
            self.cur.execute('ALTER TABLE measurements RENAME TO measurements_legacy')
            self._create_measurements_table()
            self._copy_legacy_measurements('measurements_legacy', columns)
            self.cur.execute('DROP TABLE measurements_legacy')
        except Exception:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()

    def _recover_legacy_table(self, columns: set[str]) -> None:
        if 'id' not in columns:
            raise RuntimeError(
                'Found measurements_legacy while measurements still uses a legacy schema; '
                'manual recovery is required'
            )

        logger.info('Recovering rows from orphaned legacy measurements table')
        self.cur.execute('BEGIN IMMEDIATE')
        try:
            self.cur.execute('PRAGMA table_info(measurements_legacy)')
            legacy_columns = {row[1] for row in self.cur.fetchall()}
            self._copy_legacy_measurements('measurements_legacy', legacy_columns)
            self.cur.execute('DROP TABLE measurements_legacy')
        except Exception:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()

    def _copy_legacy_measurements(self, table_name: str, columns: set[str]) -> None:
        legacy_columns = [column for column in MEASUREMENT_COLUMNS if column in columns]
        if 'timestamp' not in legacy_columns:
            raise RuntimeError(
                f'Legacy table {table_name} is missing timestamp; preserving it for manual recovery'
            )

        column_list = ', '.join(legacy_columns)
        self.cur.execute(f'''
            INSERT INTO measurements ({column_list})
            SELECT {column_list}
            FROM {table_name}
        ''')

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
                energy_total, energy_day, runtime, status, error, status_text, error_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

    def close(self) -> None:
        self.conn.close()
