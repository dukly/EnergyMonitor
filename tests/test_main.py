import socket
import socketserver
import sqlite3
import struct
import threading
from unittest.mock import MagicMock

import main
from config import settings


def test_bad_profile_has_failure_exit_code(monkeypatch):
    monkeypatch.setattr(settings, 'inverter_profile', 'missing')
    assert main.main() == 1


def test_database_startup_failure_has_failure_exit_code(monkeypatch):
    monkeypatch.setattr(main, 'Database', MagicMock(side_effect=OSError('unwritable database')))
    assert main.main() == 1


class ModbusServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address):
        super().__init__(address, ModbusHandler)
        self.connections = []
        self.thread = threading.Thread(target=self.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        self.thread.start()

    def stop(self):
        self.shutdown()
        self.server_close()
        for connection in self.connections:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()
        self.thread.join(timeout=2)


class ModbusHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.server.connections.append(self.request)
        self.request.settimeout(2)
        try:
            while True:
                request = b''
                while len(request) < 12:
                    part = self.request.recv(12 - len(request))
                    if not part:
                        return
                    request += part
                transaction, protocol, length, unit, function, start, count = struct.unpack('>HHHBBHH', request)
                if (protocol, length, unit, function, start, count) != (0, 6, 1, 4, 32000, 20):
                    raise AssertionError('Unexpected Modbus request')
                payload = struct.pack('>9fHH', 230, 5, 1000, 40, 50, 0.98, 100, 5, 10, 1, 0)
                response = struct.pack('>HHHBBB', transaction, 0, len(payload) + 3, unit, function, len(payload))
                self.request.sendall(response + payload)
        except OSError:
            return


def test_real_tcp_recovers_after_startup_outage_and_disconnect(tmp_path, monkeypatch):
    # No listener at startup. A real TCP peer is brought up/down between poll cycles.
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    db_path = tmp_path / 'measurements.db'
    for key, value in {
        'inverter_profile': 'default', 'modbus_host': '127.0.0.1', 'modbus_port': port,
        'modbus_timeout': 0.1, 'modbus_retries': 0, 'modbus_poll_interval': 0.01,
        'modbus_device_id': 1, 'sqlite_database_path': str(db_path),
    }.items():
        monkeypatch.setattr(settings, key, value)
    servers = []
    observations = []

    def next_cycle(interval):
        assert interval == 0.01
        with sqlite3.connect(db_path) as conn:
            observations.append(conn.execute('SELECT COUNT(*) FROM measurements').fetchone()[0])
        cycle = len(observations)
        if cycle in (1, 3):
            servers.append(ModbusServer(('127.0.0.1', port)))
        elif cycle == 2:
            servers[-1].stop()
        elif cycle == 4:
            raise KeyboardInterrupt

    monkeypatch.setattr(main.time, 'sleep', next_cycle)
    try:
        assert main.main() == 0
    finally:
        for server in servers:
            if server.thread.is_alive():
                server.stop()
    assert observations == [0, 1, 1, 2]
    with sqlite3.connect(db_path) as conn:
        assert conn.execute('SELECT voltage_dc, power_ac, status FROM measurements').fetchall() == [
            (230, 1000, 1), (230, 1000, 1),
        ]
