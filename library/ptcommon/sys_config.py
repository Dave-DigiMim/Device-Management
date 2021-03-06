from os import devnull
from os import path
from shutil import copy
from ptcommon.logger import PTLogger
from ptcommon import common_functions
from subprocess import check_output
from subprocess import call
from sys import version_info
import traceback
from re import compile


class _SystemCalls:
    RASPI_CMD = "/usr/bin/raspi-config"

    GET_I2C_CMD_ARR = [RASPI_CMD, "nonint", "get_i2c"]
    SET_I2C_CMD_ARR_PREFIX = ["/usr/bin/raspi-config", "nonint", "do_i2c"]

    I2CDETECT_CMD_ARR = ["/usr/sbin/i2cdetect", "-y", "1"]

    PTI2S_CMD = "/usr/bin/pt-i2s"
    I2S_ENABLE_CMD_ARR = [PTI2S_CMD, "enable"]
    I2S_DISABLE_CMD_ARR = [PTI2S_CMD, "disable"]

    AMIXER_GET_CMD_ARR = ['amixer', 'cget', 'numid=3']
    AMIXER_SET_CMD_ARR = ['amixer', 'cset', 'numid=3']
    ALSA_RESTART_CMD = ['sudo', '/etc/init.d/alsa-utils', 'restart']

    @staticmethod
    def _get_cmd_resp(cmd_arr, print_std_err=True):
        with open(devnull, 'w') as FNULL:
            if print_std_err is True:
                resp = check_output(cmd_arr)
            else:
                resp = check_output(cmd_arr, stderr=FNULL)

            if version_info >= (3, 0):
                resp = resp.decode("utf-8")

        return resp

    @staticmethod
    def _run_cmd(cmd_arr, print_std_out=False, print_std_err=False):
        with open(devnull, 'w') as FNULL:
            if print_std_out is True and print_std_err is True:
                call(cmd_arr)
            elif print_std_out is True and print_std_err is False:
                call(cmd_arr, stderr=FNULL)
            elif print_std_out is False and print_std_err is True:
                call(cmd_arr, stdout=FNULL)
            else:
                call(cmd_arr, stdout=FNULL, stderr=FNULL)

    @staticmethod
    def get_connected_i2c_device_addresses():
        addresses_arr = []
        output_lines = _SystemCalls._get_cmd_resp(_SystemCalls.I2CDETECT_CMD_ARR).splitlines()[1:]
        for line in output_lines:
            prefix, addresses_line = str(line).split(':')

            new_addresses = addresses_line.replace("--", "").split()
            addresses_arr.extend(new_addresses)

        return addresses_arr

    @staticmethod
    def get_i2c_state():
        try:
            i2c_output_str = str(_SystemCalls._get_cmd_resp(_SystemCalls.GET_I2C_CMD_ARR)).rstrip()
            i2c_output = int(i2c_output_str)

            i2c_mode = (i2c_output == 0)

            if i2c_mode is False and i2c_output == 1:
                PTLogger.error("Unable to verify I2C mode - assuming disabled")

            return i2c_mode
        except Exception as e:
            PTLogger.error("Unable to verify I2C mode. " + str(e))
            PTLogger.info(traceback.format_exc())
            return None

    @staticmethod
    def set_i2c_state(enable):
        if enable is True:
            val = "0"
        else:
            val = "1"

        cmd_to_run = list(_SystemCalls.SET_I2C_CMD_ARR_PREFIX)
        cmd_to_run.append(val)
        _SystemCalls._run_cmd(cmd_to_run)

    @staticmethod
    def get_i2s_state():
        i2s_mode_current = None
        i2s_mode_next = None
        try:
            i2s_output = _SystemCalls._get_cmd_resp([_SystemCalls.PTI2S_CMD]).splitlines()

            for line in i2s_output:
                if 'I2S is currently enabled' in str(line):
                    i2s_mode_current = True
                elif 'I2S is currently disabled' in str(line):
                    i2s_mode_current = False
                elif 'I2S is due to be enabled on reboot' in str(line):
                    i2s_mode_next = True
                elif 'I2S is due to be disabled on reboot' in str(line):
                    i2s_mode_next = False

        except Exception as e:
            PTLogger.error("Unable to verify I2S mode. " + str(e))
            PTLogger.info(traceback.format_exc())

        if i2s_mode_current is None or i2s_mode_next is None:
            PTLogger.error("Unable to determine I2S mode. Current: " + str(i2s_mode_current) + ", Next: " + str(i2s_mode_next))

        return i2s_mode_current, i2s_mode_next

    @staticmethod
    def set_i2s_state(enable):
        if enable:
            _SystemCalls._run_cmd(_SystemCalls.I2S_ENABLE_CMD_ARR)
        else:
            _SystemCalls._run_cmd(_SystemCalls.I2S_DISABLE_CMD_ARR)

    @staticmethod
    def get_audio_output_interface_no():
        interface = None
        try:
            mixer_output = _SystemCalls._get_cmd_resp(_SystemCalls.AMIXER_GET_CMD_ARR, print_std_err=False).splitlines()

            for line in mixer_output:
                if ': values=' in line:
                    prefix, interface = line.split('=')
                    break

        except Exception as e:
            PTLogger.error("There was an error getting audio output state: " + str(e))

        return interface

    @staticmethod
    def set_audio_output_interface_no(interface_no, debug_interface_name):
        PTLogger.debug("Setting audio output to " + debug_interface_name + "...")

        try:
            current_interface_no = _SystemCalls.get_audio_output_interface_no()

            if current_interface_no != str(interface_no) and current_interface_no is not None:
                PTLogger.debug("Audio not configured to " + debug_interface_name + " - updating...")
                amixer_set_interface_cmd_arr = list(_SystemCalls.AMIXER_SET_CMD_ARR)
                amixer_set_interface_cmd_arr.append(str(interface_no))
                _SystemCalls._run_cmd(amixer_set_interface_cmd_arr)
                _SystemCalls._run_cmd(_SystemCalls.ALSA_RESTART_CMD)

            PTLogger.debug("OK")
            return True

        except Exception as e:
            PTLogger.error("There was an error setting audio output to " + debug_interface_name + ": " + str(e))
            return False


class _BootCmdline:
    BOOT_CMDLINE_FILE = "/boot/cmdline.txt"

    @staticmethod
    def remove_serial():
        found_string = False

        regex_1 = compile('console=ttyAMA0,[0-9]+ ')
        regex_2 = compile('console=serial0,[0-9]+ ')

        with open(_BootCmdline.BOOT_CMDLINE_FILE) as f:
            for line in f:
                match_regex_1 = (regex_1.search(line) is not None)
                match_regex_2 = (regex_2.search(line) is not None)
                if match_regex_1 or match_regex_2:
                    found_string = True
                    break

        if found_string:
            common_functions.sed_inplace(_BootCmdline.BOOT_CMDLINE_FILE, r'console=ttyAMA0,[0-9]+ ', '')
            common_functions.sed_inplace(_BootCmdline.BOOT_CMDLINE_FILE, r'console=serial0,[0-9]+ ', '')

        return found_string


class _BootConfig:
    BOOT_CONFIG_FILE = "/boot/config.txt"

    @staticmethod
    def _get_last_field_from_line(line_to_check):
        fields = line_to_check.split("=")
        return fields[-1].replace("\n", "")

    @staticmethod
    def _get_number_value_from_line(line_to_check):

            value = ""
            index = 0

            while line_to_check[index] != "=" and index < len(line_to_check):
                index = index + 1

            while (line_to_check[index] == "=" or line_to_check[index] == " ") and index < len(line_to_check):
                index = index + 1

            while line_to_check[index].isdigit() and index < len(line_to_check):
                value = value + line_to_check[index]
                index = index + 1

            return value.strip()

    @staticmethod
    def get_value(property_name, value_is_number):
        if not (path.isfile(_BootConfig.BOOT_CONFIG_FILE)):
            PTLogger.error(_BootConfig.BOOT_CONFIG_FILE + " - file not found!")
            return ""

        with open(_BootConfig.BOOT_CONFIG_FILE) as config_file:
            for line in config_file:
                if (property_name in line):
                    if not line.strip().startswith("#"):
                        if value_is_number:
                            value = _BootConfig._get_number_value_from_line(line)
                        else:
                            value = _BootConfig._get_last_field_from_line(line)
                        return value

        return ""

    @staticmethod
    def set_value(property_name, value_to_set):
        PTLogger.debug("Checking " + property_name + " setting in " + _BootConfig.BOOT_CONFIG_FILE + "...")

        property_updated = False
        property_found = False

        temp_file = common_functions.create_temp_file()

        with open(temp_file, 'w') as output_file:

            last_char = ""
            with open(_BootConfig.BOOT_CONFIG_FILE, 'r') as input_file:

                for line in input_file:
                    line_to_write = line

                    line_to_find = str(property_name + "=")
                    desired_line = str(line_to_find + str(value_to_set))

                    if line_to_find in line_to_write:
                        property_found = True

                        if (common_functions.is_line_commented(line_to_write)):
                            line_to_write = common_functions.get_uncommented_line(line_to_write)
                            property_updated = True

                        if desired_line not in line_to_write:
                            line_to_write = desired_line + "\n"
                            property_updated = True

                    output_file.write(line_to_write)
                    last_char = line_to_write[-1]

            if (property_found is False):
                line_to_append = ""
                if last_char != "\n":
                    line_to_append += "\n"

                line_to_append += desired_line + "\n"

                # Append if not found
                output_file.write(line_to_append)
                property_updated = True

        if (property_updated is True):
            PTLogger.info("Updating " + _BootConfig.BOOT_CONFIG_FILE + " to set " + property_name + " setting...")
            copy(temp_file, _BootConfig.BOOT_CONFIG_FILE)

        else:
            PTLogger.debug(property_name + " setting already set in " + _BootConfig.BOOT_CONFIG_FILE)

        return property_updated


class HeadphoneJack:

    @staticmethod
    def set_as_audio_output():
        return _SystemCalls.set_audio_output_interface_no(1, "35mm")

    @staticmethod
    def get_audio_output_interface_no():
        return _SystemCalls.get_audio_output_interface_no()


class HDMI:

    @staticmethod
    def set_hdmi_drive_in_boot_config(mode):
        _BootConfig.set_value("hdmi_drive", mode)

    @staticmethod
    def set_as_audio_output():
        return _SystemCalls.set_audio_output_interface_no(2, "HDMI")


class I2C:

    @staticmethod
    def get_state():
        return _SystemCalls.get_i2c_state()

    @staticmethod
    def set_state(enable):
        if enable:
            PTLogger.debug("Enabling I2C...")
        else:
            PTLogger.debug("Disabling I2C...")
        _SystemCalls.set_i2c_state(enable)

    @staticmethod
    def get_connected_device_addresses():
        addresses_arr = []

        # Switch on I2C if it's not enabled
        if I2C.get_state() is False:
            PTLogger.warning("I2C is not initialised - attempting to initialise")
            I2C.set_state(True)

        # Error if still false
        if I2C.get_state() is False:
            PTLogger.error("Unable to initialise I2C - unable to get connected device addresses")

        else:
            addresses_arr = _SystemCalls.get_connected_i2c_device_addresses()

        return addresses_arr


class I2S:

    @staticmethod
    def get_states():
        i2s_mode_current, i2s_mode_next = _SystemCalls.get_i2s_state()
        return i2s_mode_current, i2s_mode_next

    @staticmethod
    def get_current_state():
        i2s_mode_current, i2s_mode_next = I2S.get_states()
        return i2s_mode_current

    @staticmethod
    def get_next_state():
        i2s_mode_current, i2s_mode_next = I2S.get_states()
        return i2s_mode_next

    @staticmethod
    def set_state(enable):
        i2s_mode_current, i2s_mode_next = I2S.get_states()
        PTLogger.info("SYS_CONFIG - i2s_mode_current: " + str(i2s_mode_current))
        PTLogger.info("SYS_CONFIG - i2s_mode_next: " + str(i2s_mode_next))
        if enable == i2s_mode_current:
            PTLogger.info("I2S is configured correctly for this session. Requested enabled: " + str(enable))

        if enable == i2s_mode_next:
            PTLogger.info("I2S is configured correctly for next session. Requested enabled: " + str(enable))
        else:
            _SystemCalls.set_i2s_state(enable)


class UART:

    @staticmethod
    def remove_serial_from_cmdline():
        return _BootCmdline.remove_serial()

    @staticmethod
    def configure_in_boot_config(init_uart_clock=None, init_uart_baud=None, enable_uart=None):
        if isinstance(init_uart_clock, int):
            _BootConfig.set_value("init_uart_clock", init_uart_clock)
        else:
            PTLogger.warning("Unable to set init_uart_clock in /boot/config.txt to non-integer value")
        if isinstance(init_uart_baud, int):
            _BootConfig.set_value("init_uart_baud", init_uart_baud)
        else:
            PTLogger.warning("Unable to set init_uart_baud in /boot/config.txt to non-integer value")
        if enable_uart == 1 or enable_uart == 0:
            _BootConfig.set_value("enable_uart", enable_uart)
        else:
            PTLogger.warning("Unable to set enable_uart in /boot/config.txt to value other than 0 or 1")

    @staticmethod
    def boot_config_correctly_configured(expected_clock_val=None, expected_baud_val=None, expected_enabled_val=None):

        if expected_clock_val is not None:
            if isinstance(expected_clock_val, int):
                clock_string = _BootConfig.get_value(property_name="init_uart_clock", value_is_number=True)
                clock_val_okay = (clock_string == str(expected_clock_val))
            else:
                PTLogger.warning("Invalid init_uart_clock value to check for in /boot/config.txt - must be an integer")
        else:
            clock_val_okay = True

        if expected_baud_val is not None:
            if isinstance(expected_baud_val, int):
                baud_string = _BootConfig.get_value(property_name="init_uart_baud", value_is_number=True)
                baud_val_okay = (baud_string == str(expected_baud_val))
            else:
                PTLogger.warning("Invalid init_uart_baud value to check for in /boot/config.txt - must be an integer")
        else:
            baud_val_okay = True

        if expected_enabled_val is not None:
            if expected_enabled_val == 1 or expected_enabled_val == 0:
                enabled_string = _BootConfig.get_value(property_name="enable_uart", value_is_number=True)
                enabled_val_okay = (enabled_string == str(expected_enabled_val))
            else:
                PTLogger.warning("Invalid enable_uart value to check for in /boot/config.txt - must be 0 or 1")
        else:
            enabled_val_okay = True

        return (clock_val_okay and baud_val_okay and enabled_val_okay)

    @staticmethod
    def enabled():
        return UART.boot_config_correctly_configured(expected_enabled_val=1)

    @staticmethod
    def set_enable(enabled=True):
        if enabled:
            UART.configure_in_boot_config(enable_uart=1)
        else:
            UART.configure_in_boot_config(enable_uart=0)
