from datetime import datetime
import sqlite3
from unittest.mock import MagicMock

import pytest

from handler import handle_measurement
from libraries.database import Database
from libraries.modbus import InverterMeasurement, ModbusClient
from status_labels import decode_error, decode_status


def test_decode_status_and_error() -> None:
    assert decode_status(1) == 'Нормальная работа'
    assert decode_error(0) == 'Нет ошибки'
    assert 'Неизвестный' in decode_status(99)


def test_handle_measurement_saves_row(tmp_path) -> None:
    db = Database(str(tmp_path / 'test.db'))
    client = MagicMock(spec=ModbusClient)
    client.read_measurement_block.return_value = InverterMeasurement(
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
    )

    handle_measurement(db, client)
    client.ensure_connected.assert_called_once()

    db.cur.execute('SELECT COUNT(*) FROM measurements')
    assert db.cur.fetchone()[0] == 1

    db.cur.execute('SELECT status_text, error_text FROM measurements')
    status_text, error_text = db.cur.fetchone()
    assert status_text == 'Нормальная работа'
    assert error_text == 'Нет ошибки'

    db.close()


def test_database_migration_from_legacy_schema(tmp_path) -> None:
    db_path = tmp_path / 'legacy.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE measurements (
            timestamp TEXT,
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
            error INTEGER
        )
    ''')
    cur.execute('''
        INSERT INTO measurements (
            timestamp, voltage_dc, current_dc, power_ac, temp, freq, pf,
            energy_total, energy_day, runtime, status, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 0,
    ))
    conn.commit()
    conn.close()

    db = Database(str(db_path))
    db.cur.execute('PRAGMA table_info(measurements)')
    columns = {row[1] for row in db.cur.fetchall()}
    assert 'id' in columns
    assert 'status_text' in columns

    db.cur.execute('SELECT COUNT(*) FROM measurements')
    assert db.cur.fetchone()[0] == 1
    db.close()


def test_database_recovers_interrupted_legacy_migration(tmp_path) -> None:
    db_path = tmp_path / 'interrupted.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE measurements_legacy (
            timestamp TEXT,
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
            error INTEGER
        )
    ''')
    cur.execute('''
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
    cur.execute('''
        INSERT INTO measurements_legacy (
            timestamp, voltage_dc, current_dc, power_ac, temp, freq, pf,
            energy_total, energy_day, runtime, status, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        '2026-06-01 10:00:00',
        1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 0,
    ))
    cur.execute('''
        INSERT INTO measurements (
            timestamp, voltage_dc, current_dc, power_ac, temp, freq, pf,
            energy_total, energy_day, runtime, status, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        '2026-06-01 10:01:00',
        10, 20, 30, 40, 50, 60, 70, 80, 90, 1, 0,
    ))
    conn.commit()
    conn.close()

    db = Database(str(db_path))

    db.cur.execute('SELECT COUNT(*) FROM measurements')
    assert db.cur.fetchone()[0] == 2
    assert not db._table_exists('measurements_legacy')

    db.cur.execute('SELECT voltage_dc FROM measurements WHERE timestamp = ?', ('2026-06-01 10:00:00',))
    assert db.cur.fetchone()[0] == 1
    db.close()


def test_database_recovery_skips_already_copied_legacy_rows(tmp_path) -> None:
    db_path = tmp_path / 'interrupted_duplicate.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE measurements_legacy (
            timestamp TEXT,
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
            error INTEGER
        )
    ''')
    cur.execute('''
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
    row = (
        '2026-06-01 10:00:00',
        1, 2, 3, 4, 5, 6, 7, 8, 9, None, None,
    )
    cur.execute('''
        INSERT INTO measurements_legacy (
            timestamp, voltage_dc, current_dc, power_ac, temp, freq, pf,
            energy_total, energy_day, runtime, status, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', row)
    cur.execute('''
        INSERT INTO measurements (
            timestamp, voltage_dc, current_dc, power_ac, temp, freq, pf,
            energy_total, energy_day, runtime, status, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', row)
    conn.commit()
    conn.close()

    db = Database(str(db_path))

    db.cur.execute('SELECT COUNT(*) FROM measurements')
    assert db.cur.fetchone()[0] == 1
    assert not db._table_exists('measurements_legacy')
    db.close()


def test_database_migration_preserves_duplicate_legacy_rows(tmp_path) -> None:
    db_path = tmp_path / 'legacy_duplicates.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE measurements (
            timestamp TEXT,
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
            error INTEGER
        )
    ''')
    row = (
        '2026-06-01 10:00:00',
        1, 2, 3, 4, 5, 6, 7, 8, 9, None, None,
    )
    cur.executemany('''
        INSERT INTO measurements (
            timestamp, voltage_dc, current_dc, power_ac, temp, freq, pf,
            energy_total, energy_day, runtime, status, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row, row))
    conn.commit()
    conn.close()

    db = Database(str(db_path))

    db.cur.execute('SELECT COUNT(*) FROM measurements')
    assert db.cur.fetchone()[0] == 2
    db.close()


def test_database_keeps_unsupported_legacy_schema_on_migration_failure(tmp_path) -> None:
    db_path = tmp_path / 'unsupported.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE measurements (
            measured_at TEXT,
            watts REAL
        )
    ''')
    cur.execute(
        'INSERT INTO measurements (measured_at, watts) VALUES (?, ?)',
        ('2026-06-01 10:00:00', 1000),
    )
    conn.commit()
    conn.close()

    with pytest.raises(RuntimeError, match='without a timestamp column'):
        Database(str(db_path))

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'measurements'")
    assert cur.fetchone() is not None
    cur.execute('SELECT measured_at, watts FROM measurements')
    assert cur.fetchone() == ('2026-06-01 10:00:00', 1000)
    cur.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'measurements_legacy'")
    assert cur.fetchone() is None
    conn.close()


def test_database_adds_missing_columns_when_id_exists(tmp_path) -> None:
    db_path = tmp_path / 'partial.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            voltage_dc REAL,
            status INTEGER,
            error INTEGER
        )
    ''')
    conn.commit()
    conn.close()

    db = Database(str(db_path))
    columns = {row[1] for row in db.cur.execute('PRAGMA table_info(measurements)').fetchall()}
    assert 'status_text' in columns
    assert 'error_text' in columns
    db.close()


def test_database_creates_parent_directory(tmp_path) -> None:
    db_path = tmp_path / 'nested' / 'data' / 'monitor.db'
    db = Database(str(db_path))
    assert db_path.exists()
    db.close()
