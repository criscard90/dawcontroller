@echo off
setlocal

echo Installazione dipendenze...
pip install -r requirements.txt

echo Creazione EXE con PyInstaller...
pyinstaller --onefile ^
  --name "DAW-MIDI-Server" ^
  --console ^
  --hidden-import=winrt ^
  --hidden-import=winrt.windows.devices.bluetooth ^
  --hidden-import=winrt.windows.devices.bluetooth.genericattributeprofile ^
  --hidden-import=winrt.windows.devices.enumeration ^
  --hidden-import=winrt.windows.foundation ^
  --hidden-import=winrt.windows.storage.streams ^
  --hidden-import=tkinter ^
  --hidden-import=tkinter.ttk ^
  --hidden-import=tkinter.scrolledtext ^
  --hidden-import=_midi ^
  ble_midi_server.py

echo.
echo EXE creato in: dist\DAW-MIDI-Server.exe
echo Premi un tasto per chiudere...
pause >nul
