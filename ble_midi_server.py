import asyncio
import sys
import threading
import queue
from datetime import datetime
from bleak import BleakServer

MIDI_SERVICE_UUID = "03b80e5a-ede8-4b33-a751-6ce34ec4c700"
MIDI_CHARACTERISTIC_UUID = "7772e5dd-3868-4112-a1a9-f2669d106bf3"
SERVER_NAME = "DAW MIDI Server"


class MidiCharacteristic:
    def __init__(self, log_queue):
        self._value = bytearray()
        self._notifying = False
        self._log_queue = log_queue

    async def read_request(self):
        return bytes(self._value)

    async def write_request(self, value):
        self._value = value
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._log_queue.put(f"[{timestamp}] RX: {value.hex()}")
        return True

    async def start_notify(self):
        self._notifying = True

    async def stop_notify(self):
        self._notifying = False


class MidiServer:
    def __init__(self):
        self.running = False
        self.log_queue = queue.Queue()
        self._thread = None
        self._loop = None
        self._server = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_async, daemon=True)
        self._thread.start()

    def _run_async(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._main())
        except Exception as e:
            self.log_queue.put(f"Errore: {e}")
        finally:
            self.running = False

    async def _main(self):
        midi_char = MidiCharacteristic(self.log_queue)
        self._server = BleakServer()
        await self._server.add_service(MIDI_SERVICE_UUID)
        await self._server.add_characteristic(
            MIDI_SERVICE_UUID,
            MIDI_CHARACTERISTIC_UUID,
            properties=["write", "notify"],
            read_request=midi_char.read_request,
            write_request=midi_char.write_request,
            start_notify=midi_char.start_notify,
            stop_notify=midi_char.stop_notify,
        )
        await self._server.start_advertising(SERVER_NAME)
        self.log_queue.put(f"Server avviato: {SERVER_NAME}")
        try:
            while self.running:
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        finally:
            try:
                await self._server.stop_advertising()
            except Exception:
                pass
            self.log_queue.put("Server fermato.")

    def stop(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        if self._loop and self._loop.is_running():
            self._loop.stop()


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

    server = MidiServer()

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
    root.geometry("420x300")
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

    log_text = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED)
    log_text.pack(fill=tk.BOTH, expand=True)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        show_error_and_exit("Errore fatale", str(e))
