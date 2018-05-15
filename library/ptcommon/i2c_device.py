from ptcommon.logger import PTLogger
from io import open as iopen
import fcntl
from time import sleep
from threading import Lock


class I2CDevice:

    I2C_SLAVE = 0x0703

    def __init__(self, device_path: str, device_address: int):

        self._device_path = device_path
        self._device_address = device_address

        self._post_read_delay = 0.020
        self._post_write_delay = 0.020

        self._thread_lock = Lock()
        self._lock_file_name = "/tmp/i2c_" + str(device_address) + ".lock"

    def set_delays(read_delay: float, write_delay: float):

        self._post_read_delay = read_delay
        self._post_write_delay = write_delay

    def connect(self, read_test=True):

        PTLogger.debug("I2C: Connecting to address " + hex(self._device_address) + " on " + self._device_path)

        self._lock_file_handle = open(self._lock_file_name, 'w')

        self._read_device = iopen(self._device_path, "rb", buffering=0)
        self._write_device = iopen(self._device_path, "wb", buffering=0)

        fcntl.ioctl(self._read_device, self.I2C_SLAVE, self._device_address)
        fcntl.ioctl(self._write_device, self.I2C_SLAVE, self._device_address)

        if (read_test is True):
            PTLogger.debug("I2C: Test read 1 byte")
            self._read_device.read(1)
            PTLogger.debug("I2C: OK")

    def disconnect(self):

        PTLogger.debug("I2C: Disconnecting...")

        self._write_device.close()
        self._read_device.close()

        self._lock_file_handle.close()

    def write_byte(self, register_address: int, byte_value: int):

        if (byte_value > 0xFF):
            PTLogger.warning("Possible unintended overflow writing value to register " + hex(register_address))

        PTLogger.debug("I2C: Writing byte " + str(byte_value) + " to " + hex(register_address))

        self._run_transaction([register_address, byte_value & 0xFF], 0)

    def write_word(self, register_address: int, word_value: int):

        if (word_value > 0xFFFF):
            PTLogger.warning("Possible unintended overflow writing value to register " + hex(register_address))

        PTLogger.debug("I2C: Writing word " + str(word_value) + " to " + hex(register_address))

        high, low = self._split_word(word_value)
        self._run_transaction([register_address, high & 0xFF, low & 0xFF], 0)

    def read_signed_byte(self, register_address: int):

        result = self.read_unsigned_byte(register_address)

        if (result & 0x80):
            result = -0x100 + result

        return result

    def read_unsigned_byte(self, register_address: int):

        result_array = self._run_transaction([register_address], 1)

        if (len(result_array) != 1):
            return None

        PTLogger.debug("I2C: Read byte " + str(result_array[0]) + " from " + hex(register_address))

        return result_array[0]

    def read_signed_word(self, register_address: int):

        result = self.read_unsigned_word(register_address)

        if (result & 0x8000):
            result = -0x10000 + result

        return result

    def read_unsigned_word(self, register_address: int):

        result_array = self._run_transaction([register_address], 2)

        if (len(result_array) != 2):
            return None

        result = self._join_word(result_array[0], result_array[1])

        PTLogger.debug("I2C: Read word " + str(result) + " from " + hex(register_address))

        return result

    def _run_transaction(self, listin: list, expected_read_length: int):

        try:
            self._acquire_locks()

            return_array = 0
            self._write_data(bytearray(listin))

            if expected_read_length != 0:
                return_array = self._read_data(expected_read_length)

            return return_array

        finally:
            self._release_locks()

    def _write_data(self, data: list):

        data = bytes(data)
        self._write_device.write(data)
        sleep(self._post_write_delay)

    def _read_data(self, expected_output_size: int):

        data = ''
        result_array = []
        data = self._read_device.read(expected_output_size)
        sleep(self._post_read_delay)

        if len(data) != 0:
            for n in data:
                if (data is str):
                    result_array.append(ord(n))
                else:
                    result_array.append(n)

        return result_array

    def _acquire_locks(self):

        self._thread_lock.acquire()
        fcntl.flock(self._lock_file_handle, fcntl.LOCK_EX)

    def _release_locks(self):

        fcntl.flock(self._lock_file_handle, fcntl.LOCK_UN)
        self._thread_lock.release()

    def _split_word(self, word):

        return divmod(word, 0x100)

    def _join_word(self, high, low):

        return (high << 8) + low
