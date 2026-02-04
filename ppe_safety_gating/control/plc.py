import logging
from pymodbus.client.sync import ModbusTcpClient


class PLCController:
    """Modbus TCP PLC controller. Writes a coil/register to enable/disable machine.

    Example usage:
        plc = PLCController(host='192.168.0.10', port=502, coil_address=1)
        plc.enable()
        plc.disable()
    """

    def __init__(self, host: str, port: int = 502, coil_address: int = 1, timeout=3):
        self.host = host
        self.port = port
        self.coil_address = coil_address
        self.timeout = timeout
        self.client = None
        self._connect()

    def _connect(self):
        try:
            self.client = ModbusTcpClient(self.host, port=self.port, timeout=self.timeout)
            if not self.client.connect():
                logging.error("PLC Modbus connection failed to %s:%s", self.host, self.port)
                self.client = None
        except Exception as e:
            logging.exception(e)
            self.client = None

    def enable(self):
        if self.client is None:
            self._connect()
        if self.client is None:
            raise RuntimeError("PLC not connected")
        # write True to coil to enable
        rr = self.client.write_coil(self.coil_address, True)
        return rr

    def disable(self):
        if self.client is None:
            self._connect()
        if self.client is None:
            return
        rr = self.client.write_coil(self.coil_address, False)
        return rr

    def close(self):
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass
