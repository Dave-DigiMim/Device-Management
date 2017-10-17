# pi-top Device Management

Python-based systemd service for detecting, configuring and communicating with pi-top hardware/peripherals

### Table of Contents    
* [What is in this repository?](#repo-contents)
* [Controlling the device manager](#control)
* [Logging](#logging)
* [Support](#support)
    * [Links](#support-links)
    * [Troubleshooting](#support-troubleshooting)

### <a name="repo-contents"></a> What is in this repository?

#### Summary
This repository forms the basis of the `pt-device-manager` software package, available for install on both pi-topOS and Raspbian. On the latest versions of pi-topOS, this package is pre-installed. On other platforms such as Raspbian, it is not recommended to install this package directly. Instead, follow the install instructions for any of the repositories for devices that this repository targets. For example, to install support for a pi-topPULSE on a pi-topCEED:

<pre style="background-color: #002b36; color: #FFFFFF;">
sudo apt install pt-hub
sudo apt install pt-pulse
</pre>

As both the packages `pt-hub` and `pt-pulse` have dependencies on the pt-device-manager, the `pt-device-manager` package will also be installed and enabled.

pt-device-manager is a Python3 program that when installed and run on a pi-top device enables detection, configuration and management of pi-top hardware. This includes hubs (e.g. pi-top or pi-topCEED) as well as peripherals (pi-topPULSE, pi-topSPEAKER). The actual work of communicating with each hardware device is handled by software equivalent to 'device drivers' in separate repositories. However the pt-device-manager takes care of loading and initialising these drivers in a pattern akin to a _plugin_ architecture.

The responsibilities of the device manager include:

* Detecting whether the operating system is running on pi-top hardware, and if so initialising communication with the hub.
* Communicating with pi-top hubs to detect hardware changes and notifications, such as battery status, hardware-initiated shutdown, etc.
* Detecting connection/disconnection of pi-top peripherals, such as a pi-topSPEAKER, and initialising peripheral such that whenever possible it will work in a 'plug & play' manner.
* Opening a request-reponse messaging server and responding to requests from clients, e.g. responding to a request for the current screen brightness.
* Opening a publishing messaging server and broadcasting to connected client when hardware changes take place.
* Monitoring user input in order to dim the screen backlight when the user has been inactive for a configurable period.
* Shutting down the OS when required.

##### Supported device drivers and repositories

* **pi-topHUB v1**
    * For the original pi-top and pi-topCEED
    * https://github.com/pi-top/pi-topHUB-v1
* **pi-topHUB v2**
    * For the new pi-top
    * https://github.com/pi-top/pi-topHUB-v2
* **pi-topPULSE**
    * https://github.com/pi-top/pi-topPULSE
* **pi-topSPEAKER**
    * https://github.com/pi-top/pi-topSPEAKER

#### Files

##### pt-device-manager
This Python script is the brain of the pi-top device management on pi-topOS. See [How it works](#how-it-works) for more information.

##### pt-brightness, pt-battery
These Python scripts are pt-device-manager messaging clients. They send messages to the device management service to adjust the screen settings or query the battery status on a pi-top device.

##### ptdm-*
These Python modules are used by pt-device-manager

##### poweroff.c, poweroff-v2
These programs (written in C and Python respectively) are used to send a message directly to the relevent pi-top hub to trigger shutdown of the hub. They do not go via the 

##### pt-i2s
Found in `i2s` subdirectory. Used by pt-device-manager to switch I2S on/off, specifically when targeting pi-topSPEAKER/pi-topPULSE. To configure for I2S, a custom `asound.conf` file is used to enable mixing multiple audio sources. As well as this, some settings in `/boot/config.txt` are altered:

* `dtoverlay=hifiberry-dac` - enables I2S audio on subsequent boots
* `#dtparam=audio=on` - disables default sound driver
* `dtoverlay=i2s-mmap` - allows multiple audio sources to be mixed together

Disabling I2S reverses these changes.

##### hifiberry-alsactl.restore
Found in `i2s` subdirectory. This file exposes a soundcard device configuration to the operating system, enabling volume control. It is used by `pt-device-manager` when it detects that I2S has been enabled via the daemon for the first time, whereby it reboots to enable. This operation is only required once, so a 'breadcrumb' file is created to indicate that this has been completed.

### <a name="control"></a> Controlling the device manager

pt-device-manager is intended to be a systemd service which starts with the OS and stops on shutdown. However for diagnostic or debugging purposes it can be useful to start and stop it, or to run it standalone.

Checking the current status of the device manager (with example output):

<pre style="background-color: #002b36; color: #FFFFFF;">
sudo systemctl status pt-device-manager

<span style="color:#E0E0E0"><span style="color:#859900">●</span> pt-device-manager.service - pi-top device auto-detection and configuration daemon
   Loaded: loaded (/lib/systemd/system/pt-device-manager.service; enabled)
   Active: <span style="color:#859900">active (running)</span> since Tue 2017-10-17 15:55:43 UTC; 1s ago
 Main PID: 15974 (pt-device-manag)
   CGroup: /system.slice/pt-device-manager.service
           └─15974 /usr/bin/python3 /usr/lib/pt-device-manager/pt-device-manager</span>
</pre>

Starting/stopping the device manager:

<pre style="background-color: #002b36; color: #FFFFFF;">
sudo systemctl start pt-device-manager
sudo systemctl stop pt-device-manager
</pre>

Stopping and disabling the service, and then running standalone:

<pre style="background-color: #002b36; color: #FFFFFF;">
sudo systemctl stop pt-device-manager
sudo systemctl disable pt-device-manager
cd /usr/lib/pt-device-manager
sudo ./pt-device-manager --no-journal --log-level 20
</pre>

**Note** when running the device manager standalone, the above two command line parameters are useful:

* `--no-journal` forces the device manager to log to stdout rather than the systemd journal
* `--log-level X` sets the logging levels where 10 is the lowest (debug) and 40 is the highest (serious errors only)


### <a name="logging"></a> Logging

As the pt-device-manager runs as a systemd service, it logs to the system journal. This can be viewed using commands such as:

<pre style="background-color: #002b36; color: #FFFFFF;">
sudo journalctl -u pt-device-manager
sudo journalctl -u pt-device-manager --no-pager
sudo journalctl -u pt-device-manager -b
</pre>

### <a name="support"></a> Support
#### <a name="support-links"></a> Links
* [pi-topHUB v1](https://github.com/pi-top/pi-topHUB-v1)
* [pi-topHUB v2](https://github.com/pi-top/pi-topHUB-v2)
* [pi-topPULSE](https://github.com/pi-top/pi-topPULSE)
* [pi-topSPEAKER](https://github.com/pi-top/pi-topSPEAKER)
* <a name="support-pinout"></a> [pi-top Peripherals' GPIO Pinouts](https://pinout.xyz/boards#manufacturer=pi-top)
* [Support](https://support.pi-top.com/)

#### <a name="support-troubleshooting"></a> Troubleshooting
##### Why is my pi-top addon not working?

* Please see the corresponding repository for your device. Repositories are listed at the top of this README.