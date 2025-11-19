# Utilities

This directory contains utility scripts for working with the pylxpweb library and Luxpower/EG4 inverters.

## Register Mapping Tool

**`map_registers.py`** - Comprehensive register mapping utility for discovering and documenting inverter register spaces.

### Overview

This tool automatically discovers and maps the register space for Luxpower/EG4 inverters by:
- **Dynamic Block Sizing** - Automatically finds the minimum block size needed to read each register
- **Boundary Validation** - Detects leading empty registers in multi-register blocks
- **Range Merging** - Automatically consolidates overlapping register ranges
- **Device Type Detection** - Maps serial numbers to device models
- **Comprehensive Output** - Generates JSON files with register blocks, parameters, and sample values

### Installation

1. **Prerequisites**:
   ```bash
   # Ensure you have Python 3.11+ installed
   python --version

   # Install uv (if not already installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Dependencies**:
   ```bash
   # From the project root directory
   uv sync
   ```

3. **Configure Credentials**:
   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit .env with your credentials
   # LUXPOWER_USERNAME=your_username
   # LUXPOWER_PASSWORD=your_password
   # LUXPOWER_BASE_URL=https://monitor.eg4electronics.com  # Optional
   ```

### Usage

#### Basic Usage

Map your inverter's register space using the default range (0-126):

```bash
uv run python utils/map_registers.py -s YOUR_SERIAL_NUMBER
```

#### Multiple Register Ranges

Most inverters require scanning multiple register ranges for complete coverage:

```bash
# 18KPV / LXP 18K-Hybrid Gen4
uv run python utils/map_registers.py \
    -s 1234567890 \
    -r 0,127 -r 127,127 -r 240,127

# GridBOSS / Grid Boss 18K-Hybrid
uv run python utils/map_registers.py \
    -s 0987654321 \
    -r 0,381 -r 2032,127
```

#### Command-Line Authentication

Override `.env` credentials with command-line flags:

```bash
uv run python utils/map_registers.py \
    -u your_username \
    -p your_password \
    -s 1234567890 \
    -r 0,127
```

#### Custom Base URL (Regional Endpoints)

For EU or other regional endpoints:

```bash
uv run python utils/map_registers.py \
    -s 1234567890 \
    -r 0,127 \
    -b https://eu.luxpowertek.com
```

#### Fast Mode (Skip Boundary Validation)

Disable boundary validation for faster scanning (less accurate):

```bash
uv run python utils/map_registers.py \
    -s 1234567890 \
    -r 0,127 \
    --no-boundary-validation
```

#### Custom Output Filename

Specify a custom output filename:

```bash
uv run python utils/map_registers.py \
    -s 1234567890 \
    -r 0,127 \
    -o my_custom_results.json
```

### Command-Line Options

| Option | Shorthand | Description | Default |
|--------|-----------|-------------|---------|
| `--username` | `-u` | API username | From `.env` or `$LUXPOWER_USERNAME` |
| `--password` | `-p` | API password | From `.env` or `$LUXPOWER_PASSWORD` |
| `--serial-num` / `--serial` | `-s` | Inverter serial number (required) | - |
| `--range` | `-r` | Register range as `start,length` (repeatable) | `0,127` |
| `--base-url` | `-b` | API base URL | From `.env` or `monitor.eg4electronics.com` |
| `--output` | `-o` | Output JSON file | `{DeviceType}_{SerialNum}.json` |
| `--no-boundary-validation` | - | Skip leading empty register detection | Validation enabled |
| `--start` | - | Starting register (deprecated, use `--range`) | - |
| `--length` | - | Number of registers (deprecated, use `--range`) | - |

### Known Register Ranges

Based on web UI analysis, these are the known register ranges for different device types:

#### 18KPV (LXP 18K-Hybrid Gen4)
```bash
uv run python utils/map_registers.py \
    -s YOUR_SERIAL \
    -r 0,127 -r 127,127 -r 240,127
```

Ranges:
- `0-126` - Primary configuration and runtime data
- `127-253` - Extended configuration
- `240-366` - Advanced settings

#### GridBOSS (Grid Boss 18K-Hybrid)
```bash
uv run python utils/map_registers.py \
    -s YOUR_SERIAL \
    -r 0,381 -r 2032,127
```

Ranges:
- `0-380` - Standard inverter configuration and runtime data
- `2032-2158` - GridBOSS-specific features (grid management, smart loads)

### Output Format

The tool generates a comprehensive JSON file with the following structure:

```json
{
  "metadata": {
    "timestamp": "2025-11-19T04:57:12.325673Z",
    "base_url": "https://monitor.eg4electronics.com",
    "serial_num": "0987654321",
    "device_type": "Grid Boss",
    "input_ranges": [
      {"start": 0, "length": 381, "end": 380},
      {"start": 2032, "length": 127, "end": 2158}
    ],
    "merged_ranges": [
      {"start": 0, "length": 381, "end": 380},
      {"start": 2032, "length": 127, "end": 2158}
    ],
    "boundary_validation_enabled": true
  },
  "statistics": {
    "total_blocks": 241,
    "total_parameters": 579,
    "blocks_with_leading_empty": 19
  },
  "device_type_map": {
    "0987654321": "Grid Boss"
  },
  "register_blocks": [
    {
      "start_register": 0,
      "block_size": 2,
      "end_register": 1,
      "parameter_count": 12,
      "parameter_keys": ["HOLD_MODEL", "HOLD_MODEL_batteryType", ...],
      "sample_values": {"HOLD_MODEL": 18, ...},
      "boundary_validation": {
        "original_start": 0,
        "original_size": 2,
        "actual_start": 0,
        "actual_size": 2,
        "leading_empty_registers": 0
      }
    }
  ],
  "all_parameter_names": ["HOLD_MODEL", "HOLD_SERIAL_NUM", ...]
}
```

### How It Works

The tool uses a multi-phase process to accurately map registers:

1. **Dynamic Block Sizing**
   - Tests block sizes from 1 to 127 to find minimum size needed
   - Identifies multi-register parameters (e.g., serial numbers, timestamps)

2. **Boundary Validation** (optional, enabled by default)
   - For multi-register blocks, tests if data is in last register(s)
   - Detects leading empty registers
   - Determines actual data location within block

3. **Range Merging**
   - Automatically merges overlapping or adjacent register ranges
   - Example: `[0,127] [127,127] [240,127] [269,7]` → `[0,367]`
   - Prevents duplicate scanning

### Performance

- **With boundary validation**: ~0.2 seconds per register
  - Example: 381 registers ≈ 75 seconds

- **Without boundary validation**: ~0.1 seconds per register
  - Example: 381 registers ≈ 40 seconds

The tool includes automatic:
- Rate limiting (0.1s delay between requests)
- Exponential backoff on errors
- Session management and auto-reauthentication

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `Error: Username and password required` | Create `.env` file with credentials or use `-u` and `-p` flags |
| `No data - stopping scan` | Normal - indicates end of register space reached |
| `API error (HTTP 200): EXCEPTION_ERROR` | API rate limiting or temporary error - tool will retry automatically |
| `Got 401 Unauthorized` | Session expired - tool auto-reauthenticates |
| File not found errors | Run from project root: `uv run python utils/map_registers.py ...` |

### Authentication Priority

Credentials are loaded in this order:

1. **Command-line flags**: `--username/-u` and `--password/-p`
2. **Environment file**: `LUXPOWER_USERNAME` and `LUXPOWER_PASSWORD` in `.env`
3. **Environment variables**: `$LUXPOWER_USERNAME` and `$LUXPOWER_PASSWORD`

### Examples

**Example 1: Quick test scan (first 10 registers, no validation)**
```bash
uv run python utils/map_registers.py \
    -s 0987654321 \
    -r 0,10 \
    --no-boundary-validation
```

**Example 2: Full 18KPV scan with custom filename**
```bash
uv run python utils/map_registers.py \
    -s 1234567890 \
    -r 0,127 -r 127,127 -r 240,127 \
    -o 18kpv_complete_map.json
```

**Example 3: GridBOSS scan with CLI credentials**
```bash
uv run python utils/map_registers.py \
    -u my_username \
    -p my_password \
    -s 0987654321 \
    -r 0,381 -r 2032,127
```

**Example 4: EU region endpoint**
```bash
uv run python utils/map_registers.py \
    -s 1234567890 \
    -r 0,127 \
    -b https://eu.luxpowertek.com
```

### Output Files

By default, output files are named: `{DeviceType}_{SerialNum}.json`

Examples:
- `LXP18KHybridGen4_1234567890.json`
- `GridBoss_0987654321.json`
- `FlexBOSS21_1234567890.json`

To use a custom filename, specify `-o custom_name.json`.

### Contributing Mappings

To contribute register mappings for new device types:

1. Map all known ranges for your device
2. Verify the output JSON is complete
3. Submit via GitHub issue or pull request with:
   - Device model and firmware version
   - Serial number (last 4 digits only for privacy)
   - Generated JSON file
   - Any device-specific notes

### Advanced Usage

**Watching output in real-time:**
```bash
# Run in foreground to see live output
uv run python utils/map_registers.py -s 0987654321 -r 0,381 -r 2032,127

# Or run in background and monitor
uv run python utils/map_registers.py -s 0987654321 -r 0,381 -r 2032,127 &
tail -f {DeviceType}_{SerialNum}.json  # After completion
```

**Analyzing output:**
```bash
# View statistics
jq '.statistics' GridBoss_0987654321.json

# List all parameters
jq '.all_parameter_names' GridBoss_0987654321.json

# Find blocks with leading empty registers
jq '.register_blocks[] | select(.boundary_validation.leading_empty_registers > 0)' GridBoss_0987654321.json

# Export parameters to CSV
jq -r '.all_parameter_names[]' GridBoss_0987654321.json > parameters.csv
```

## Register Map to Markdown Converter

**`json_to_markdown.py`** - Converts register discovery JSON files into human-readable markdown documentation.

### Overview

This tool takes the JSON output from `map_registers.py` and creates formatted markdown tables for easy viewing and documentation.

### Usage

```bash
# Basic usage - output to same directory with .md extension
python3 utils/json_to_markdown.py <input_json>

# Specify custom output path
python3 utils/json_to_markdown.py <input_json> <output_md>
```

### Examples

```bash
# Convert 18KPV register map
python3 utils/json_to_markdown.py research/18KPV_1234567890.json

# Convert GridBoss register map with custom output
python3 utils/json_to_markdown.py research/GridBoss_0987654321.json docs/registers/gridboss.md

# Convert both device types
python3 utils/json_to_markdown.py research/18KPV_1234567890.json docs/registers/18KPV_1234567890.md
python3 utils/json_to_markdown.py research/GridBoss_0987654321.json docs/registers/GridBoss_0987654321.md
```

### Output Format

The generated markdown includes:

1. **Metadata Section**
   - Timestamp of discovery
   - Base URL used
   - Device serial number and type
   - Input register ranges
   - Statistics (total blocks, parameters, etc.)

2. **Register Map Table**
   - Register number
   - Start address
   - Block length (number of registers)
   - Parameter names (code-formatted)
   - Sample values

For registers with multiple parameters, all parameters are combined in a single row with `<br>` tags creating line breaks within the table cells.

### Example Output

```markdown
| Register | Start | Length | Parameters | Sample Values |
|----------|-------|--------|------------|---------------|
| 0 | 0 | 2 | `HOLD_MODEL`<br>`HOLD_MODEL_batteryType`<br>`HOLD_MODEL_lithiumType` | "0x986C0"<br>2<br>1 |
| 2 | 2 | 5 | `HOLD_SERIAL_NUM` | "1234567890" |
| 21 | 21 | 1 | `FUNC_EPS_EN`<br>`FUNC_AC_CHARGE` | True<br>True |
```

### Features

- Handles single and multiple parameters per register block
- Uses `<br>` tags for line breaks within table cells (true merged cell effect)
- Formats different value types appropriately (strings, numbers, booleans)
- Preserves all metadata and statistics from the JSON
- Type-safe implementation with full type hints
- One row per register for easy scanning

### Workflow

The typical workflow combines both utilities:

```bash
# Step 1: Discover register map
uv run python utils/map_registers.py -s 0987654321 -r 0,381 -r 2032,127

# Step 2: Convert to markdown for documentation
python3 utils/json_to_markdown.py GridBoss_0987654321.json docs/registers/GridBoss_0987654321.md
```

## Additional Utilities

Future utilities will be added to this directory for tasks such as:
- Parameter reading and writing
- Firmware version checking
- Batch operations across multiple devices
- Data logging and analysis

Check back for updates!

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/yourusername/pylxpweb/issues
- Documentation: See `../docs/` directory
- API Reference: See `../docs/api/LUXPOWER_API.md`

## License

See the main project LICENSE file.
