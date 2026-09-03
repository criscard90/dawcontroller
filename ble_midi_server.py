"""
DAW BLE MIDI Server - WinRT Nativo (no Bleak)
Usa le API Windows.Devices.Bluetooth.GenericAttributeProfile direttamente tramite proiezioni Python WinRT.
Richiede i pacchetti: winrt-runtime, winrt-windows-devices-bluetooth, ecc.
(già installati come dipendenze di bleak)
"""

import asyncio
import sys
import threading
import uuid
from datetime import datetime
import queue
from datetime import datetime

# Import WinRT - proiezioni Python delle API Windows
try:
    import winrt.windows.devices.bluetooth as bluetooth
    import winrt.windows.devices.bluetooth.genericattributeprofile as gatt
    import winrt.windows.storage.streams as streams
except ImportError as e:
    # Mostra errore in GUI invece di chiudersi
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Errore WinRT",
            f"Moduli WinRT non trovati.\n\n{e}\n\n"
            "Installa con: pip install --upgrade bleak\n"
            "(che include tutte le dipendenze WinRT)"
        )
        root.destroy()
    except Exception:
        print(f"Errore: Moduli WinRT non trovati. {e}")
    sys.exit(1)


# UUID standard BLE MIDI
MIDI_SERVICE_UUID = "03b80e5a-ede8-4b33-a751-6ce34ec4c700"
MIDI_CHAR_UUID = "7772e5dd-3868-4112-a1a9-f2669d106bf3"
SERVER_NAME = "DAW MIDI Server"


class BleMidiServer:
    def __init__(self):
        self.running = False
        self.log_queue = queue.Queue()
        self._thread = None
        self._loop = None
        self._service_provider = None
        self._midi_char = None

    def log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {msg}")

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_async, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        if self._loop and self._loop.is_running():
            self._loop.stop()

    def _run_async(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._main())
        except Exception as e:
            self.log(f"Errore server: {e}")
        finally:
            self.running = False

    async def _main(self):
        self.log("Inizializzazione GATT Server...")

        # 1. Crea il GattServiceProvider
        service_uuid = uuid.UUID(MIDI_SERVICE_UUID)
        result = await gatt.GattServiceProvider.create_async(service_uuid)

        if result.error != gatt.GattCommunicationStatus.SUCCESS:
            self.log(f"Errore creazione ServiceProvider: {result.error}")
            return

        self._service_provider = result.service_provider
        self.log(f"ServiceProvider creato: {self._service_provider.service.uuid}")

        # 2. Crea i parametri per la caratteristica MIDI
        char_params = gatt.GattLocalCharacteristicParameters()
        char_params.characteristic_properties = (
            gatt.GattCharacteristicProperties.WRITE |
            gatt.GattCharacteristicProperties.WRITE_WITHOUT_RESPONSE |
            gatt.GattCharacteristicProperties.NOTIFY
        )
        char_params.write_protection_level = gatt.GattProtectionLevel.PLAIN
        char_params.read_protection_level = gatt.GattProtectionLevel.PLAIN
        char_params.user_description = "MIDI I/O"

        # 3. Crea la caratteristica MIDI
        char_uuid = uuid.UUID(MIDI_CHAR_UUID)
        char_result = await self._service_provider.service.create_characteristic_async(
            char_uuid, char_params
        )

        if char_result.error != bluetooth.BluetoothError.SUCCESS:
            self.log(f"Errore creazione caratteristica: {char_result.error}")
            return

        self._midi_char = char_result.characteristic
        self.log(f"Caratteristica MIDI creata: {self._midi_char.uuid}")

        # 4. Sottoscrivi gli eventi
        self._midi_char.WriteRequested += self._on_write_requested
        self._midi_char.ReadRequested += self._on_read_requested

        # 5. Avvia l'advertising
        adv_params = gatt.GattServiceProviderAdvertisingParameters()
        adv_params.IsConnectable = True
        adv_params.IsDiscoverable = True

        self._service_provider.start_advertising(adv_params)
        self.log(f"Advertising avviato come '{SERVER_NAME}'")
        self.log("In attesa di connessioni...")

        # 6. Mantieni il server attivo
        try:
            while self.running:
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        finally:
            try:
                self._service_provider.stop_advertising()
                self._midi_char.WriteRequested -= self._on_write_requested
                self._midi_char.ReadRequested -= self._on_read_requested
                self.log("Advertising fermato.")
            except Exception as e:
                self.log(f"Errore chiusura: {e}")

    def _on_write_requested(self, sender, args):
        deferral = args.get_deferral()

        async def process_write():
            try:
                request = await args.get_request_async()
                if request is None:
                    self.log("Write request rifiutato (no access)")
                    return

                reader = streams.DataReader.from_buffer(request.value)
                data = bytearray(request.value.length)
                reader.read_bytes(data)

                self.log(f"RX MIDI: {data.hex()} ({len(data)} bytes)")

                if request.option == gatt.GattWriteOption.WRITE_WITH_RESPONSE:
                    request.respond()

            except Exception as e:
                self.log(f"Errore process_write: {e}")
            finally:
                deferral.complete()

        asyncio.run_coroutine_threadsafe(process_write(), self._loop)

    def _on_read_requested(self, sender, args):
        deferral = args.get_deferral()

        async def process_read():
            try:
                request = await args.get_request_async()
                if request is None:
                    return
                request.respond_with_value(streams.Buffer(0))
            except Exception as e:
                self.log(f"Errore process_read: {e}")
            finally:
                deferral.complete()

        asyncio.run_coroutine_threadsafe(process_read(), self._loop)


def show_error_and_exit(title, message):
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        pass


def main():
    try:
        import tkinter as tk
        from tkinter import ttk, scrolledtext, messagebox
    except Exception as e:
        show_error_and_exit("Errore", f"Tkinter non disponibile:\n{e}")
        return

    server = BleMidiServer()

    def on_start_stop():
        if server.running:
            server.stop()
            btn.config(text="AVVIA")
            status_var.set("Fermato")
            status_label.config(foreground="red")
        else:
            try:
                server.start()
                btn.config(text="FERMA")
                status_var.set("In esecuzione")
                status_label.config(foreground="green")
                root.after(100, update_log)
            except Exception as e:
                messagebox.showerror("Errore avvio", str(e))

    def update_log():
        try:
            while True:
                msg = server.log_queue.get_nowait()
                log_text.config(state=tk.NORMAL)
                log_text.insert(tk.END, msg + "\n")
                log_text.see(tk.END)
                log_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        if server.running:
            root.after(100, update_log)

    def on_close():
        if server.running:
            server.stop()
        root.destroy()

    try:
        root = tk.Tk()
    except Exception as e:
        show_error_and_exit("Errore GUI", f"Impossibile creare la finestra:\n{e}")
        return

    root.title("DAW BLE MIDI Server")
    root.geometry("480x320")
    root.resizable(False, False)

    top_frame = ttk.Frame(root, padding=10)
    top_frame.pack(fill=tk.X)

    btn = ttk.Button(top_frame, text="AVVIA", command=on_start_stop)
    btn.pack(side=tk.LEFT)

    status_var = tk.StringVar(value="Fermato")
    status_label = ttk.Label(top_frame, textvariable=status_var, foreground="red")
    status_label.pack(side=tk.RIGHT)

    log_frame = ttk.Frame(root, padding=(10, 0, 10, 10))
    log_frame.pack(fill=tk.BOTH, expand=True)

    log_text = scrolledtext.ScrolledText(log_frame, height=12, state=tk.DISABLED)
    log_text.pack(fill=tk.BOTH, expand=True)

    root.protocol("WM_DELETE_WINDOW", on_close)

    # Messaggio iniziale
    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, "Pronto. Clicca AVVIA per avviare il server BLE MIDI.\n")
    log_text.insert(tk.END, f"Servizio: {MIDI_SERVICE_UUID}\n")
    log_text.insert(tk.END, f"Caratteristica: {MIDI_CHAR_UUID}\n")
    log_text.config(state=tk.DISABLED)

    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        show_error_and_exit("Errore fatale", str(e))
