class DeviceID():
    unknown = -1
    pi_top = 0
    pi_top_ceed = 1
    pi_top_v2 = 2


class HostDevice():
    id = DeviceID.unknown
    name = ""
    addr = -1

    def __init__(self, name="", id=-1, addr=-1):
        if name == "pi-top v1" or id == DeviceID.pi_top or addr == 0x0b:
            self.id = DeviceID.pi_top
            self.name = "pi-top v1"
            self.addr = 0x0b
        if (name == "pi-topCEED" or id == DeviceID.pi_top) and addr == -1:
            self.id = DeviceID.pi_top_ceed
            self.name = "pi-topCEED"
            self.addr = -1
        if name == "pi-top v2" or id == DeviceID.pi_top_v2 or addr == 0x10:
            self.id = DeviceID.pi_top_v2
            self.name = "pi-top v2"
            self.addr = 0x10


class PeripheralID():
    unknown = -1
    pi_top_pulse = 0
    pi_top_speaker_l = 1
    pi_top_speaker_m = 2
    pi_top_speaker_r = 3
    pi_top_speaker_v2 = 4
    pi_top_proto_plus = 5


class PeripheralType():
    unknown = -1
    hat = 0
    addon = 1


class Peripheral():
    id = PeripheralID.unknown
    compatible_ids = []
    name = ""
    type = PeripheralType.unknown
    addr = -1

    def __init__(self, name="", id=-1, addr=-1):
        if name == "pi-topPULSE" or id == PeripheralID.pi_top_pulse or addr == 0x24:
            self.config_pulse()
        elif name == "pi-topSPEAKER-v1-Left" or id == PeripheralID.pi_top_speaker_l or addr == 0x71:
            self.config_speaker_l()
        elif name == "pi-topSPEAKER-v1-Mono" or id == PeripheralID.pi_top_speaker_m or addr == 0x73:
            self.config_speaker_m()
        elif name == "pi-topSPEAKER-v1-Right" or id == PeripheralID.pi_top_speaker_r or addr == 0x72:
            self.config_speaker_r()
        elif name == "pi-topSPEAKER-v2" or id == PeripheralID.pi_top_speaker_v2 or addr == 0x43:
            self.config_speaker_v2()
        elif name == "pi-topPROTO+" or id == PeripheralID.pi_top_proto_plus or addr == 0x2a:
            self.config_proto_plus()

    def config_pulse(self):
        self.id = PeripheralID.pi_top_pulse
        self.compatible_ids = []
        self.name = "pi-topPULSE"
        self.type = PeripheralType.hat
        self.addr = 0x24

    def config_speaker_l(self):
        self.id = PeripheralID.pi_top_speaker_l
        self.compatible_ids = [2, 3]
        self.name = "pi-topSPEAKER-v1-Left"
        self.type = PeripheralType.addon
        self.addr = 0x71

    def config_speaker_m(self):
        self.id = PeripheralID.pi_top_speaker_m
        self.compatible_ids = [1, 3]
        self.name = "pi-topSPEAKER-v1-Mono"
        self.type = PeripheralType.addon
        self.addr = 0x73

    def config_speaker_r(self):
        self.id = PeripheralID.pi_top_speaker_r
        self.compatible_ids = [1, 2]
        self.name = "pi-topSPEAKER-v1-Right"
        self.type = PeripheralType.addon
        self.addr = 0x72

    def config_speaker_v2(self):
        self.id = PeripheralID.pi_top_speaker_v2
        self.compatible_ids = [5]
        self.name = "pi-topSPEAKER-v2"
        self.type = PeripheralType.addon
        self.addr = 0x43

    def config_proto_plus(self):
        self.id = PeripheralID.pi_top_proto_plus
        self.compatible_ids = [0, 4]
        self.name = "pi-topPROTO+"
        self.type = PeripheralType.addon
        self.addr = 0x2a
