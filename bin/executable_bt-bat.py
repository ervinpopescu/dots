#!/bin/python
import json
import subprocess
import time
from asyncio import get_event_loop, new_event_loop, set_event_loop
from binascii import hexlify
from datetime import datetime
from pathlib import Path
from time import time_ns

from bleak import BleakScanner


class AirpodScanner:
    # Configure update duration (update after n seconds)
    UPDATE_DURATION = 10
    MIN_RSSI = -60
    AIRPODS_MANUFACTURER = 76
    AIRPODS_DATA_LENGTH = 54
    RECENT_BEACONS_MAX_T_NS = 10000000000  # 10 Seconds

    def __init__(self) -> None:
        self.recent_beacons = []

    def get_best_result(self, device, advertisement):
        self.recent_beacons.append(
            {
                "time": time_ns(),
                "device": device,
                "advertisement": advertisement,
            }
        )
        strongest_beacon = None
        i = 0
        while i < len(self.recent_beacons):
            if (
                time_ns() - self.recent_beacons[i]["time"]
                > AirpodScanner.RECENT_BEACONS_MAX_T_NS
            ):
                self.recent_beacons.pop(i)
                continue
            if (
                strongest_beacon is None
                or advertisement.rssi < self.recent_beacons[i]["advertisement"].rssi
            ):
                strongest_beacon = self.recent_beacons[i]["device"]
            i += 1

        if strongest_beacon is not None and strongest_beacon.address == device.address:
            strongest_beacon = device

        return strongest_beacon

    # Getting data with hex format
    async def get_device(self):
        # Scanning for devices
        devices_and_advertisements = list(
            (await BleakScanner().discover(return_adv=True)).values()
        )
        for d, a in devices_and_advertisements:
            # Checking for AirPods
            d = self.get_best_result(d, a)
            if (
                a.rssi >= AirpodScanner.MIN_RSSI
                and AirpodScanner.AIRPODS_MANUFACTURER in a.manufacturer_data
            ):
                data_hex = hexlify(
                    bytearray(a.manufacturer_data[AirpodScanner.AIRPODS_MANUFACTURER])
                )
                data_length = len(
                    hexlify(
                        bytearray(
                            a.manufacturer_data[AirpodScanner.AIRPODS_MANUFACTURER]
                        )
                    )
                )
                if data_length == AirpodScanner.AIRPODS_DATA_LENGTH:
                    return data_hex
        return False

    # Same as get_device() but it's standalone method instead of async
    def get_data_hex(self):
        new_loop = new_event_loop()
        set_event_loop(new_loop)
        loop = get_event_loop()
        a = loop.run_until_complete(self.get_device())
        loop.close()
        return a

    # Getting data from hex string and converting it to dict(json)
    def get_data(self):
        raw = self.get_data_hex()

        # Return blank data if airpods not found
        if not raw:
            return dict(status=0, model="AirPods not found")

        flip: bool = AirpodScanner.is_flipped(raw)

        # On 7th position we can get AirPods model, gen1, gen2, Pro or Max
        if chr(raw[7]) == "e":
            model = "AirPodsPro"
        elif chr(raw[7]) == "3":
            model = "AirPods3"
        elif chr(raw[7]) == "f":
            model = "AirPods2"
        elif chr(raw[7]) == "2":
            model = "AirPods1"
        elif chr(raw[7]) == "a":
            model = "AirPodsMax"
        else:
            model = "unknown"

        # Checking left AirPod for availability and storing charge in variable
        status_tmp = int("" + chr(raw[12 if flip else 13]), 16)
        left_status = (
            100
            if status_tmp == 10
            else (status_tmp * 10 + 5 if status_tmp <= 10 else -1)
        )

        # Checking right AirPod for availability and storing charge in variable
        status_tmp = int("" + chr(raw[13 if flip else 12]), 16)
        right_status = (
            100
            if status_tmp == 10
            else (status_tmp * 10 + 5 if status_tmp <= 10 else -1)
        )

        # Checking AirPods case for availability and storing charge in variable
        status_tmp = int("" + chr(raw[15]), 16)
        case_status = (
            100
            if status_tmp == 10
            else (status_tmp * 10 + 5 if status_tmp <= 10 else -1)
        )

        # On 14th position we can get charge status of AirPods
        charging_status = int("" + chr(raw[14]), 16)
        charging_left: bool = (
            charging_status & (0b00000010 if flip else 0b00000001)
        ) != 0
        charging_right: bool = (
            charging_status & (0b00000001 if flip else 0b00000010)
        ) != 0
        charging_case: bool = (charging_status & 0b00000100) != 0

        # Return result info in dict format
        return dict(
            status=1,
            charge=dict(left=left_status, right=right_status, case=case_status),
            charging_left=charging_left,
            charging_right=charging_right,
            charging_case=charging_case,
            model=model,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            raw=raw.decode("utf-8"),
        )

    # Return if left and right is flipped in the data
    @staticmethod
    def is_flipped(raw):
        return (int("" + chr(raw[10]), 16) & 0x02) == 0

    def run(self):
        data = self.get_data()
        if data["status"] == 1:
            return data


AIRPODS_PRO_GEN2_VENDOR_SPECIFIC = "74ec2172-0bad-4d01-8f77-997b2be0722a"


def run_command(command):
    """Run a shell command and return its output as a string."""
    result = subprocess.run(
        command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return result.stdout.strip()


def get_bluetooth_devices():
    """Retrieve a list of Bluetooth device MAC addresses."""
    devices_output = run_command("bluetoothctl devices")
    return [line.split()[1] for line in devices_output.splitlines() if line]


def get_device_info(mac):
    """Get the detailed info of a Bluetooth device."""
    return run_command(f"bluetoothctl info {mac}")


def get_connected_status(info):
    """Extract the connection status from the device info."""
    for line in info.splitlines():
        if line.strip().startswith("Connected:"):
            return line.split()[1]
    return "no"


def get_vendor_specific_uuid(info):
    """Extract the Vendor Specific UUID from the device info."""
    for line in info.splitlines():
        if "UUID: Vendor specific" in line:
            return line.split()[-1].strip("()")
    return None


def get_battery_level(info):
    """Extract the battery level from the device info."""
    for line in info.splitlines():
        if "Battery" in line:
            return line.split("(")[1].strip(")")
    return "Unknown"


def main():
    macs = get_bluetooth_devices()

    for mac in macs:
        device_info = get_device_info(mac)
        connected = get_connected_status(device_info)
        if connected != "no":
            vendor_specific_uuid = get_vendor_specific_uuid(device_info)
            if vendor_specific_uuid == AIRPODS_PRO_GEN2_VENDOR_SPECIFIC:
                airpod_scanner = AirpodScanner()
                data = airpod_scanner.run()
                if data and data.get("status") == 1:
                    left = data["charge"].get("left", "N")
                    right = data["charge"].get("right", "N")
                    case = data["charge"].get("case", "N")
                    print(f"L:{left},R:{right},C:{case}")
            else:
                battery = get_battery_level(device_info)
                print(battery)


if __name__ == "__main__":
    main()
