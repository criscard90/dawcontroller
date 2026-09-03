import asyncio
import sys
from bleak import BleakServer

MIDI_SERVICE_UUID = "03b80e5a-ede8-4b33-a751-6ce34ec4c700"
MIDI_CHARACTERISTIC_UUID = "7772e5dd-3868-4112-a1a9-f2669d106bf3"
SERVER_NAME = "DAW MIDI Server"


class MidiCharacteristic:
    def __init__(self):
        self._value = bytearray()
        self._notifying = False

    async def read_request(self):
        return bytes(self._value)

    async def write_request(self, value):
        self._value = value
        print(f"Ricevuto MIDI: {value.hex()}")
        return True

    async def start_notify(self):
        self._notifying = True

    async def stop_notify(self):
        self._notifying = False


async def main():
    server = BleakServer()
    midi_char = MidiCharacteristic()

    await server.add_service(MIDI_SERVICE_UUID)
    await server.add_characteristic(
        MIDI_SERVICE_UUID,
        MIDI_CHARACTERISTIC_UUID,
        properties=["write", "notify"],
        read_request=midi_char.read_request,
        write_request=midi_char.write_request,
        start_notify=midi_char.start_notify,
        stop_notify=midi_char.stop_notify,
    )

    await server.start_advertising(SERVER_NAME)
    print(f"Server BLE MIDI avviato: {SERVER_NAME}")
    print("Premi Ctrl+C per fermare.")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await server.stop_advertising()
        await server.disconnect_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
