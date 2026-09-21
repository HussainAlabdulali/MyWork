# LabVIEW myRIO Project

This folder contains the LabVIEW side of the Industry 4.0 proof of concept.

The VIs were used to read NI myRIO accelerometer data and Arduino-compatible sensor inputs, then test communication with the dashboard/backend over protocols such as UDP, TCP, and HTTP.

## Key Files

- `Untitled Project 1/Untitled Project 1.lvproj` - LabVIEW project file.
- `Untitled Project 1/Main.vi` - Main myRIO program prototype.
- `Untitled Project 1/Accel_reader.vi` - Accelerometer reading prototype.
- `Untitled Project 1/UDP.vi` - UDP communication prototype.
- `Untitled Project 1/TCP.vi` - TCP communication prototype.
- `Untitled Project 1/HTTP.vi` and `Untitled Project 1/HTTP_Accel_Reader.vi` - HTTP/API communication prototypes.
- `Untitled Project 1/documentation/` - Exported LabVIEW project documentation and diagram.

## Not Tracked

The `builds/` directory is generated deployment output and is ignored by Git. LabVIEW local metadata files such as `.aliases` and `.lvlps` are also ignored because they can contain local IP addresses, machine paths, or IDE window state.
