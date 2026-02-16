import sqlite3

from logger import logger


class Database:
    """This class provides methods to interact with the SQLite database for storing measurement data."""

    def __init__(self, database_path: str) -> None:
        """Initializes the Database class by connecting to the SQLite database and creating the measurements table if it doesn't exist."""

        # Set the database path
        self.database_path = database_path

        # Connect to the SQLite database (or create it if it doesn't exist)
        self.conn = sqlite3.connect(self.database_path)
        self.cur = self.conn.cursor()

        # Initialize the database and create the measurements table if it doesn't exist
        self._initialize_database()

    def _initialize_database(self) -> None:
        """This function initializes the SQLite database and creates the measurements table if it doesn't exist."""

        # Execute the SQL command to create the measurements table if it doesn't already exist
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
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

        # Commit the changes
        self.conn.commit()

    def save_measurement(
        self, timestamp: str, voltage_dc: float, current_dc: float, power_ac: float, temp: float, freq: float,
        pf: float, energy_total: float, energy_day: float, runtime: float, status: int, error: int,
    ) -> None:
        """This function saves the provided measurement values to the SQLite database."""

        # Execute the SQL command to insert the measurement data into the measurements table
        self.cur.execute('''
            INSERT INTO measurements (
                timestamp, voltage_dc, current_dc, power_ac, temp, freq, pf,
                energy_total, energy_day, runtime, status, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        ))

        # Commit the changes
        self.conn.commit()

        # Log the saved measurement data
        logger.info(
            (
                f'Measurement saved: {timestamp}, {voltage_dc} V, {current_dc} A, {power_ac} W, {temp} °C, {freq} Hz, PF: {pf}, '
                f'Energy Total: {energy_total} kWh, Energy Day: {energy_day} kWh, Runtime: {runtime} h, Status: {status}, Error: {error}'
            )
        )
