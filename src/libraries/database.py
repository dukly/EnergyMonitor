import sqlite3
from pathlib import Path

from logger import logger

SCHEMA_COLUMNS: dict[str, str] = {
    'status_text': 'TEXT',
    'error_text': 'TEXT',
}

MEASUREMENT_DATA_COLUMNS: tuple[str, ...] = (
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
    'status_text',
    'error_text',
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
        self._create_measurements_table()
        self.conn.commit()

        if self._table_exists('measurements_legacy'):
            self._recover_legacy_table()

        columns = self._table_columns()

        if 'id' not in columns:
            self._migrate_legacy_table(columns)
            columns = self._table_columns()

        self._ensure_columns(columns)

        self.cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_measurements_timestamp
            ON measurements(timestamp)
        ''')
        self.conn.commit()

    def _create_measurements_table(self) -> None:
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
                error_text TEXT
            )
        ''')

    def _table_exists(self, table_name: str) -> bool:
        self.cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        )
        return self.cur.fetchone() is not None

    def _table_columns(self, table_name: str = 'measurements') -> set[str]:
        if table_name not in {'measurements', 'measurements_legacy'}:
            raise ValueError(f'Unsupported table name: {table_name}')
        self.cur.execute(f'PRAGMA table_info({table_name})')
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

        self.cur.execute('BEGIN IMMEDIATE')
        try:
            self.cur.execute('ALTER TABLE measurements RENAME TO measurements_legacy')
            self._create_measurements_table()
            copied_rows = self._copy_legacy_rows(columns)
            self.cur.execute('DROP TABLE measurements_legacy')
        except Exception:
            self.conn.rollback()
            raise

        self.conn.commit()
        logger.info(f'Migrated legacy measurements table: {copied_rows} rows copied')

    def _recover_legacy_table(self) -> None:
        logger.warning('Recovering unfinished measurements table migration')
        columns = self._table_columns('measurements_legacy')

        self.cur.execute('BEGIN IMMEDIATE')
        try:
            copied_rows = self._copy_legacy_rows(columns, skip_existing=True)
            self.cur.execute('DROP TABLE measurements_legacy')
        except Exception:
            self.conn.rollback()
            raise

        self.conn.commit()
        logger.info(f'Recovered legacy measurements table: {copied_rows} rows copied')

    def _legacy_row_count(self) -> int:
        self.cur.execute('SELECT COUNT(*) FROM measurements_legacy')
        return int(self.cur.fetchone()[0])

    def _copy_legacy_rows(self, source_columns: set[str], skip_existing: bool = False) -> int:
        row_count = self._legacy_row_count()
        if row_count == 0:
            return 0

        target_columns = self._table_columns()
        legacy_columns = [
            column for column in MEASUREMENT_DATA_COLUMNS
            if column in source_columns and column in target_columns
        ]

        if 'timestamp' not in legacy_columns:
            raise RuntimeError(
                'Cannot migrate legacy measurements table without a timestamp column; '
                'leaving source data untouched for manual recovery.'
            )

        dropped_columns = [
            column for column in MEASUREMENT_DATA_COLUMNS
            if column in source_columns and column not in target_columns
        ]
        if dropped_columns:
            raise RuntimeError(
                'Cannot migrate legacy measurements table because target table is missing '
                f'columns: {", ".join(dropped_columns)}'
            )

        column_list = ', '.join(legacy_columns)
        where_clause = ''
        if skip_existing:
            duplicate_checks = ' AND '.join(
                f'measurements.{column} IS measurements_legacy.{column}'
                for column in legacy_columns
            )
            where_clause = f'''
            WHERE NOT EXISTS (
                SELECT 1
                FROM measurements
                WHERE {duplicate_checks}
            )
            '''

        self.cur.execute(f'''
            INSERT INTO measurements ({column_list})
            SELECT {column_list}
            FROM measurements_legacy
            {where_clause}
        ''')
        return self.cur.rowcount

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
