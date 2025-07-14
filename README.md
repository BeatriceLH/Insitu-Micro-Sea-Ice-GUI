# Insitu-Micro-Sea-Ice-GUI
SeaIceMicro GUI
===============

A Python GUI for real-time control and image acquisition using FLIR/Point Grey cameras via `simple_pyspin`,
with integrated illumination control (e.g., Arduino-driven LEDs) and automated file saving.

Features
--------

- Live camera view with adjustable exposure, gain, and frame rate
- Support for multiple image formats (Mono8, RGB8, etc.)
- Illumination control: fluorescence, oblique, and off modes
- Acquisition with programmable delay
- Organized image saving based on metadata (station, site, depth, direction)
- Console output in GUI
- TIFF image saving with optional metadata

Requirements
------------

Install the following packages:

    pip install matplotlib pillow tifffile matplotlib-scalebar

You also need:

- A working installation of `simple_pyspin`
- A FLIR / Point Grey USB3 or GigE camera
- An Arduino connected via serial (COM3 by default)

Use the interface to:
----------
 - Set pixel format, frame rate, exposure, and gain
 - Choose illumination mode (e.g., Fluo or Oblique)
 - Input metadata (station, site, depth, direction)
 - Click "Start Live" to preview
 - Click "Start acquisition" to capture and save images
