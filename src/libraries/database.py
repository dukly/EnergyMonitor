import sqlite3

from logger import logger


class Database:
    """SQLite storage for inverter measurements."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        self.conn = sqlite3.connect(self.database_path)
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
                error_text TEXT
            )
        ''')
        self.conn.commit()

        self.cur.execute('PRAGMA table_info(measurements)')
        columns = {row[1] for row in self.cur.fetchall()}

        if 'id' not in columns:
            self._migrate_legacy_table(columns)

        self.cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_measurements_timestamp
            ON measurements(timestamp)
        ''')
        self.conn.commit()

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
                error_text TEXT
            )
        ''')

        legacy_columns = [
            column for column in (
                'timestamp', 'voltage_dc', 'current_dc', 'power_ac', 'temp', 'freq', 'pf',
                'energy_total', 'energy_day', 'runtime', 'status', 'error',
            )
            if column in columns
        ]
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
    ) -> None:
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

        logger.info(
            (
                f'Measurement saved: {timestamp}, {voltage_dc} V, {current_dc} A, {power_ac} W, {temp} °C, '
                f'{freq} Hz, PF: {pf}, Energy Total: {energy_total} kWh, Energy Day: {energy_day} kWh, '
                f'Runtime: {runtime} h, Status: {status} ({status_text}), Error: {error} ({error_text})'
            )
        )

    def close(self) -> None:
        self.conn.close()
