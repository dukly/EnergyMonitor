import sqlite3

import pytest

from libraries.database import Database


@pytest.mark.parametrize('schema, error', [
    ('id INTEGER PRIMARY KEY, measured_at TEXT', 'timestamp'),
    ('id TEXT PRIMARY KEY, timestamp TEXT', 'INTEGER PRIMARY KEY'),
    ('id INTEGER, timestamp TEXT', 'INTEGER PRIMARY KEY'),
])
def test_unsupported_schema_is_preserved(tmp_path, schema, error):
    path = tmp_path / 'test.db'
    with sqlite3.connect(path) as conn:
        conn.execute(f'CREATE TABLE measurements ({schema})')
        conn.execute("INSERT INTO measurements VALUES (1, 'original')")
        original = conn.execute('SELECT * FROM measurements').fetchall()
    with pytest.raises(RuntimeError, match=error):
        Database(str(path))
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT * FROM measurements').fetchall() == original
        assert len(conn.execute('PRAGMA table_info(measurements)').fetchall()) == 2


def test_partial_target_is_repaired_before_legacy_recovery(tmp_path):
    path = tmp_path / 'recovery.db'
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE measurements (id INTEGER PRIMARY KEY, timestamp TEXT)')
        conn.execute('CREATE TABLE measurements_legacy (timestamp TEXT, current_dc REAL)')
        conn.execute("INSERT INTO measurements_legacy VALUES ('old', 12.5)")
    db = Database(str(path))
    try:
        assert db.cur.execute('SELECT timestamp, current_dc FROM measurements').fetchone()[:] == ('old', 12.5)
        assert db.save_measurement('new', *([2] * 11)) == 2
        assert not db._table_exists('measurements_legacy')
    finally:
        db.close()


def test_column_migration_rolls_back_all_changes_on_failure(tmp_path):
    path = tmp_path / 'rollback.db'
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE measurements (id INTEGER PRIMARY KEY, timestamp TEXT)')
        conn.execute("INSERT INTO measurements VALUES (1, 'original')")

    class FailingMigration(Database):
        def _ensure_columns(self, columns):
            alterations = 0

            def authorize(action, *args):
                nonlocal alterations
                if action == sqlite3.SQLITE_ALTER_TABLE:
                    alterations += 1
                    if alterations == 2:
                        return sqlite3.SQLITE_DENY
                return sqlite3.SQLITE_OK

            self.conn.set_authorizer(authorize)
            super()._ensure_columns(columns)

    with pytest.raises(sqlite3.DatabaseError):
        FailingMigration(str(path))
    with sqlite3.connect(path) as conn:
        assert [row[1] for row in conn.execute('PRAGMA table_info(measurements)')] == ['id', 'timestamp']
        assert conn.execute('SELECT * FROM measurements').fetchall() == [(1, 'original')]
