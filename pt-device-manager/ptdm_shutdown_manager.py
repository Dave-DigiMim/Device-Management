from ptcommon.logger import PTLogger
from ptcommon.common_ids import DeviceID
from ptcommon.counter import Counter
from os import system
from subprocess import call

# Handles safe shutdown when the hub is communicating that its battery capacity is below a threshold set by ptdm_controller


class ShutdownManager:
    warning_battery_level = 5
    warning_battery_ctr = Counter(3)

    critical_battery_level = 3
    critical_battery_ctr = Counter(3)

    shutdown_battery_level = 2
    shutdown_battery_ctr = Counter(3)

    shown_warning_battery_message = False
    shown_critical_battery_message = False
    shutdown_initiated = False

    def __init__(self):
        self._callback = None
        self._battery_capacity = -1
        self._battery_charging = -1

        self._device_id = DeviceID.unknown

    def initialise(self, callback):
        self._callback = callback

    def set_battery_capacity(self, new_value):
        self._battery_capacity = new_value

    def set_battery_charging(self, new_value):
        self._battery_charging = new_value

    def set_device_id(self, new_value):
        self._device_id = new_value

    def set_poweroff_service_states(self, v1_service_enabled, v2_service_enabled):
        v1_status_str = "enable" if v1_service_enabled else "disable"
        v2_status_str = "enable" if v2_service_enabled else "disable"

        ret_code1 = call(["systemctl", v1_status_str, "pt-poweroff-v1.service"])
        PTLogger.info("systemctl " + v1_status_str + " pt-poweroff-v1.service " + str(ret_code1))

        ret_code2 = call(["systemctl", v2_status_str, "pt-poweroff-v2.service"])
        PTLogger.info("systemctl " + v2_status_str + " pt-poweroff-v2.service " + str(ret_code2))

    def configure_shutdown_from_device_id(self):
        PTLogger.info("Configuring shutdown based on device ID: " + str(self._device_id))
        if self._device_id == DeviceID.pi_top:
            PTLogger.info("First generation pi-top detected")
            self.set_poweroff_service_states(v1_service_enabled=True, v2_service_enabled=False)
        elif self._device_id == DeviceID.pi_top_ceed:
            PTLogger.info("pi-topCEED detected")
            self.set_poweroff_service_states(v1_service_enabled=True, v2_service_enabled=False)

        elif self._device_id == DeviceID.pi_top_v2:
            PTLogger.info("Second generation pi-top detected")
            self.set_poweroff_service_states(v1_service_enabled=False, v2_service_enabled=True)

        else:
            PTLogger.info("No pi-top hardware detected - disabling poweroff")
            self.set_poweroff_service_states(v1_service_enabled=False, v2_service_enabled=False)

    def get_battery_capacity(self):
        return self._battery_capacity

    def get_battery_charging(self):
        return self._battery_charging

    def device_has_battery(self):
        return (self._device_id == DeviceID.pi_top or
                self._device_id == DeviceID.pi_top_v2)

    def battery_state_fully_defined(self):
        capacity_defined = (self._battery_capacity > -1)
        charging_defined = (self._battery_charging > -1)

        return (capacity_defined and charging_defined)

    def reset_counters(self):
        self.warning_battery_ctr.reset()
        self.critical_battery_ctr.reset()
        self.shutdown_battery_ctr.reset()

    def update_counters_from_battery_state(self):
        under_shutdown_threshold = (self._battery_capacity <= self.shutdown_battery_level)
        under_critical_threshold = (self._battery_capacity <= self.critical_battery_level)
        under_warning_threshold = (self._battery_capacity <= self.warning_battery_level)

        if under_shutdown_threshold:
            self.shutdown_battery_ctr.increment()
            if (self.shutdown_initiated is False):
                PTLogger.info("Battery: shutdown threshold reached " + str(self.shutdown_battery_ctr._current) + " of " + str(self.shutdown_battery_ctr._max))
        else:
            self.shutdown_battery_ctr.reset()

        if under_critical_threshold:
            self.critical_battery_ctr.increment()
            if (self.shown_critical_battery_message is False):
                PTLogger.info("Battery: critical threshold reached " + str(self.critical_battery_ctr._current) + " of " + str(self.critical_battery_ctr._max))
        else:
            self.critical_battery_ctr.reset()

        if under_warning_threshold:
            self.warning_battery_ctr.increment()
            if (self.shown_warning_battery_message is False):
                PTLogger.info("Battery: warning threshold reached " + str(self.warning_battery_ctr._current) + " of " + str(self.warning_battery_ctr._max))
        else:
            self.warning_battery_ctr.reset()

    def process_battery_state(self):
        reset_ctrs = True

        if self.device_has_battery():
            if self.battery_state_fully_defined():
                discharging = (self._battery_charging == 0)

                if discharging:
                    self.update_counters_from_battery_state()
                    reset_ctrs = False

        if reset_ctrs:
            self.reset_counters()
            # Need to be able to send warning messages again once the battery state is determined to be safe again
            self.shown_warning_battery_message = False
            self.shown_critical_battery_message = False
        else:
            if self.shutdown_battery_ctr.maxed() and not self.shutdown_initiated:
                self.shutdown()
            elif self.critical_battery_ctr.maxed() and not self.shown_critical_battery_message:
                self._callback._on_critical_battery_warning()
                self.shown_critical_battery_message = True
            elif self.warning_battery_ctr.maxed() and not self.shown_warning_battery_message:
                self._callback._on_low_battery_warning()
                self.shown_warning_battery_message = True

    def shutdown(self):
        if (self.shutdown_initiated is True):
            PTLogger.warning("Shutdown already initiated")
            return

        PTLogger.info("Shutting down OS...")
        system("shutdown -h now")
        self.shutdown_initiated = True
        PTLogger.info("OS shutdown command issued")

    def reboot(self):
        PTLogger.info("Rebooting OS")
        system("reboot")
        PTLogger.info("OS reboot command issued")
