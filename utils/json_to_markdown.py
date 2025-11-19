#!/usr/bin/env python3
"""Convert register JSON files to human-readable markdown documentation.

This script takes the register discovery JSON files and creates formatted
markdown documentation with tables showing register mappings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def format_sample_value(value: Any) -> str:
    """Format a sample value for display in markdown table.

    Args:
        value: The value to format

    Returns:
        Formatted string representation
    """
    if isinstance(value, bool) or isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        return f'"{value}"'
    else:
        return str(value)


def create_register_table(register_blocks: list[dict[str, Any]]) -> str:
    """Create markdown table from register blocks.

    For registers with multiple parameters, we combine them into a single
    cell using <br> tags for line breaks within the table cell.

    Args:
        register_blocks: List of register block dictionaries

    Returns:
        Formatted markdown table string
    """
    lines = []

    # Table header
    lines.append("| Register | Start | Length | Parameters | Sample Values |")
    lines.append("|----------|-------|--------|------------|---------------|")

    for block in register_blocks:
        original_start = block["start_register"]
        original_size = block["block_size"]
        params = block["parameter_keys"]
        samples = block["sample_values"]

        # Use boundary validation data if available
        boundary = block.get("boundary_validation", {})
        actual_start = boundary.get("actual_start", original_start)
        actual_size = boundary.get("actual_size", original_size)
        leading_empty = boundary.get("leading_empty_registers", 0)

        # If there are leading empty registers, add a row for them first
        if leading_empty > 0:
            empty_start = original_start
            if leading_empty == 1:
                empty_display = str(empty_start)
            else:
                empty_end = empty_start + leading_empty - 1
                empty_display = f"{empty_start}-{empty_end}"
            lines.append(f"| {empty_display} | {empty_start} | {leading_empty} | `<EMPTY>` | - |")

        # Format the register range display for actual data
        if actual_size == 1:
            reg_display = str(actual_start)
        else:
            end_reg = actual_start + actual_size - 1
            reg_display = f"{actual_start}-{end_reg}"

        if len(params) == 0:
            # Empty block (no leading empty, whole block is empty)
            lines.append(f"| {reg_display} | {actual_start} | {actual_size} | `<EMPTY>` | - |")
        elif len(params) == 1:
            # Single parameter - one row
            param = params[0]
            value = format_sample_value(samples.get(param, "N/A"))
            lines.append(
                f"| {reg_display} | {actual_start} | {actual_size} | `{param}` | {value} |"
            )
        else:
            # Multiple parameters - combine with <br> tags
            param_list = "<br>".join([f"`{p}`" for p in params])
            value_list = "<br>".join([format_sample_value(samples.get(p, "N/A")) for p in params])
            lines.append(
                f"| {reg_display} | {actual_start} | {actual_size} | {param_list} | {value_list} |"
            )

    return "\n".join(lines)


def create_metadata_section(metadata: dict[str, Any], statistics: dict[str, Any]) -> str:
    """Create metadata section for markdown document.

    Args:
        metadata: Metadata dictionary from JSON
        statistics: Statistics dictionary from JSON

    Returns:
        Formatted markdown metadata section
    """
    lines = ["## Metadata", ""]

    lines.append(f"- **Timestamp**: {metadata.get('timestamp', 'N/A')}")
    lines.append(f"- **Base URL**: {metadata.get('base_url', 'N/A')}")
    lines.append(f"- **Serial Number**: {metadata.get('serial_num', 'N/A')}")
    lines.append(f"- **Device Type**: {metadata.get('device_type', 'N/A')}")
    lines.append("")

    # Input ranges
    if "input_ranges" in metadata:
        lines.append("### Input Ranges")
        lines.append("")
        for range_info in metadata["input_ranges"]:
            lines.append(
                f"- Start: {range_info['start']}, "
                f"Length: {range_info['length']}, "
                f"End: {range_info['end']}"
            )
        lines.append("")

    # Statistics
    lines.append("### Statistics")
    lines.append("")
    lines.append(f"- **Total Register Blocks**: {statistics.get('total_blocks', 'N/A')}")
    lines.append(f"- **Total Parameters**: {statistics.get('total_parameters', 'N/A')}")
    lines.append(
        f"- **Blocks with Leading Empty Registers**: {statistics.get('blocks_with_leading_empty', 'N/A')}"
    )
    lines.append("")

    return "\n".join(lines)


def convert_json_to_markdown(json_path: Path, output_path: Path | None = None) -> None:
    """Convert a register JSON file to markdown documentation.

    Args:
        json_path: Path to input JSON file
        output_path: Optional path to output markdown file.
                    If None, uses same name as input with .md extension
    """
    # Read JSON file
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    # Determine output path
    if output_path is None:
        output_path = json_path.with_suffix(".md")

    # Extract data
    metadata = data.get("metadata", {})
    statistics = data.get("statistics", {})
    register_blocks = data.get("register_blocks", [])

    # Build markdown content
    lines = []

    # Title
    device_type = metadata.get("device_type", "Unknown Device")
    serial_num = metadata.get("serial_num", "Unknown")
    lines.append(f"# {device_type} Register Map")
    lines.append(f"## Serial Number: {serial_num}")
    lines.append("")

    # Metadata section
    lines.append(create_metadata_section(metadata, statistics))

    # Register table
    lines.append("## Register Map")
    lines.append("")
    lines.append(create_register_table(register_blocks))
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Generated from register discovery JSON*")

    # Write markdown file
    markdown_content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"✓ Created {output_path}")
    print(f"  - {statistics.get('total_blocks', 0)} register blocks")
    print(f"  - {statistics.get('total_parameters', 0)} parameters")


def main() -> None:
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python json_to_markdown.py <input_json> [output_md]")
        print("")
        print("Examples:")
        print("  python json_to_markdown.py research/18KPV_1234567890.json")
        print(
            "  python json_to_markdown.py research/GridBoss_0987654321.json docs/registers/gridboss.md"
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    convert_json_to_markdown(input_path, output_path)


if __name__ == "__main__":
    main()
