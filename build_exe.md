# How to Build the .exe

## Requirements

```
python -m pip install pyinstaller
```

## Build command

```
pyinstaller --onefile --windowed --name "SmartReview" app_gui.py
```

The finished executable will be at:

```
dist/SmartReview.exe
```

No Python installation needed to run it — share the single .exe file.
