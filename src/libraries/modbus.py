import struct

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException

from logger import logger


class ModbusClient:
    """A wrapper around the ModbusTcpClient to handle reading float32 and int16 values with error handling."""

    def __init__(self, host, port) -> None:
        """Initializes the Modbus client with the specified host and port."""

        # Create a ModbusTcpClient instance with the provided host and port
        self.client = ModbusTcpClient(host, port=port)

    def connect(self, timeout=5, retries=3) -> bool:
        """Attempts to connect to the Modbus server and returns True if successful, False otherwise."""

        # Try to connect to the Modbus server and return the result
        for i in range(retries):
            if self.client.connect(timeout=timeout):
                return True
            logger.warning(f'Failed to connect to Modbus server (attempt {i + 1}/{retries})')

        raise ConnectionError(f'Unable to connect to Modbus server after {retries} attempts')

    def close(self) -> None:
        """Closes the Modbus client connection."""

        # Close the Modbus client connection
        self.client.close()

    def read_float32(self, address) -> float | None:
        """Reads a 32-bit float from the specified Modbus register address."""

        # Try to read two consecutive 16-bit registers and check for ModbusIOException, returning None if it occurs
        try:
            # Read two consecutive 16-bit registers and check for ModbusIOException
            first_result = self.client.read_input_registers(address, 1)
            second_result = self.client.read_input_registers(address + 1, 1)

            # Check if either result is a ModbusIOException and log a warning if so
            if isinstance(first_result, ModbusIOException) or isinstance(second_result, ModbusIOException):
                logger.warning(f'Ignoring ModbusIOException reading float32 at address {address}')
                return None

            # Combine the two 16-bit registers into a single 32-bit integer
            raw = (first_result.registers[0] << 16) | second_result.registers[0]

            # Unpack the raw value as a big-endian float
            return struct.unpack('>f', raw.to_bytes(4, byteorder='big'))[0]

        # Catch any other exceptions that may occur during the read operation and log a warning
        except Exception as e:
            logger.warning(f'Ignoring error reading float32 at address {address}: {e}', exc_info=True)
            return None

    def read_int16(self, address) -> int | None:
        """Reads a 16-bit integer from the specified Modbus register address."""

        # Try to read the register and check for ModbusIOException, returning None if it occurs
        try:
            # Read the register and check for ModbusIOException
            result = self.client.read_input_registers(address, 1)

            # Check if the result is a ModbusIOException and log a warning if so
            if isinstance(result, ModbusIOException):
                logger.warning(f'Ignoring ModbusIOException reading int16 at address {address}')
                return None

            # Return the value of the first register
            return result.registers[0]

        # Catch any other exceptions that may occur during the read operation and log a warning
        except Exception as e:
            logger.warning(f'Ignoring error reading int16 at address {address}: {e}', exc_info=True)
            return None
