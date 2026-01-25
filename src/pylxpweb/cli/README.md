# pylxpweb CLI Tools

## pylxpweb-modbus-diag

Diagnostic tool for collecting and comparing Modbus register data from Luxpower/EG4 inverters. Useful for debugging register mapping issues, comparing local vs cloud data, and generating bug reports.

### Installation

```bash
pip install pylxpweb
```

### Quick Start

```bash
# Interactive mode (prompts for everything)
pylxpweb-modbus-diag

# Direct Modbus TCP connection (RS485-to-Ethernet adapter)
pylxpweb-modbus-diag --host 192.168.1.100

# With cloud API comparison
pylxpweb-modbus-diag --host 192.168.1.100 --cloud --username user@email.com
```

### Connection Methods

#### Modbus TCP (Default)
Connect via RS485-to-Ethernet adapter (e.g., Waveshare) on port 502:

```bash
pylxpweb-modbus-diag --host 192.168.1.100 --transport modbus
```

#### WiFi Dongle
Connect directly to the inverter's WiFi dongle on port 8000:

```bash
pylxpweb-modbus-diag --host 192.168.1.100 --transport dongle --dongle-serial BA12345678
```

**Note:** The dongle serial is printed on the dongle label (10 characters).

#### Both (Comparison)
Collect from both sources and compare:

```bash
pylxpweb-modbus-diag --host 192.168.1.100 --transport both --dongle-serial BA12345678
```

### Cloud API Comparison

Add `--cloud` to fetch data from the Luxpower/EG4 monitoring portal for comparison:

```bash
pylxpweb-modbus-diag --host 192.168.1.100 --cloud --username user@email.com
```

You'll be prompted for the password. The tool compares local Modbus readings against cloud API data and highlights mismatches.

### Output Formats

The tool generates a ZIP archive containing:

| File | Description |
|------|-------------|
| `modbus_diagnostic.json` | Structured JSON with all data |
| `modbus_diagnostic.md` | Human-readable Markdown tables |
| `modbus_diagnostic.csv` | Spreadsheet-compatible CSV |
| `modbus_diagnostic.bin` | Raw binary register dump |

### Privacy & Sanitization

**By default, serial numbers are masked** with realistic-looking replacement characters in all output files (e.g., `CE12345678` becomes `CE7B3KHN78`).

To include full serial numbers:

```bash
pylxpweb-modbus-diag --host 192.168.1.100 --no-sanitize
```

### Register Ranges

Default ranges cover most registers:
- Input registers: 0-399
- Holding registers: 0-299

To customize:

```bash
pylxpweb-modbus-diag --host 192.168.1.100 \
  --input-start 0 --input-count 500 \
  --holding-start 0 --holding-count 400
```

### All Options

```
Connection Options:
  --host, -H          Inverter IP address
  --port, -p          Port number (default: 502 for Modbus, 8000 for dongle)
  --transport, -t     Connection method: modbus, dongle, or both
  --serial, -s        Override auto-detected inverter serial
  --dongle-serial     WiFi dongle serial (required for dongle transport)

Cloud API Options:
  --cloud, -c         Include cloud API data for comparison
  --username, -u      Luxpower/EG4 cloud username
  --password          Cloud password (prompts if not provided)
  --base-url          API URL (default: https://monitor.eg4electronics.com)

Register Range Options:
  --input-start       Input register start address (default: 0)
  --input-count       Number of input registers (default: 400)
  --holding-start     Holding register start address (default: 0)
  --holding-count     Number of holding registers (default: 300)

Output Options:
  --output-dir, -o    Output directory (default: current directory)
  --no-sanitize       Don't mask serial numbers in output
  --no-archive        Output individual files instead of ZIP
  --quiet, -q         Suppress progress output

General:
  --version, -V       Show version
  --help              Show help
```

### Creating GitHub Issues

After collection, the tool prints instructions for creating a GitHub issue with the `gh` CLI:

```bash
gh issue create --repo joyfulhouse/pylxpweb --title "Modbus register issue - CE******78" --body "..."
```

Then attach the generated ZIP file to the issue.

### Examples

#### Debug register mapping for a new inverter model

```bash
pylxpweb-modbus-diag --host 192.168.1.100 --no-sanitize
```

#### Compare Modbus vs Cloud readings

```bash
pylxpweb-modbus-diag --host 192.168.1.100 --cloud -u myemail@example.com
```

#### Collect extended register range

```bash
pylxpweb-modbus-diag --host 192.168.1.100 \
  --input-count 600 --holding-count 500
```

#### Output to specific directory

```bash
pylxpweb-modbus-diag --host 192.168.1.100 -o ~/diagnostics/
```
