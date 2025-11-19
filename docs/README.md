# pylxpweb Documentation

Welcome to the **pylxpweb** documentation. This directory contains comprehensive documentation for the Luxpower/EG4 inverter Python API client library.

## Documentation Structure

### API Documentation
- **[Luxpower API Reference](api/LUXPOWER_API.md)** - Complete API endpoint documentation
  - Authentication and session management
  - Station/plant management
  - Device discovery
  - Runtime data retrieval
  - Energy statistics
  - Battery information
  - GridBOSS/MID device operations
  - Control operations
  - Data scaling reference
  - Error handling and retry strategies

### Architecture Documentation
*Coming soon*
- System design and patterns
- Authentication flow diagrams
- Data model documentation
- Caching strategies

### Examples
*Coming soon*
- Basic usage examples
- Advanced integration patterns
- Home Assistant integration guide
- Error handling examples

## Quick Start

For getting started with the pylxpweb library, see:
1. [Luxpower API Reference](api/LUXPOWER_API.md) - Understand the underlying API
2. Project README.md (root) - Installation and basic usage
3. Examples directory - Code samples and patterns

## Research Materials

The `research/` directory at the project root contains reference implementations:
- **eg4_web_monitor/** - Production-quality Home Assistant integration
- **eg4_inverter_ha/** - Earlier implementation for comparison

**IMPORTANT**: Research materials are for reference only and should not be imported or used in production code.

## Contributing to Documentation

When adding new documentation:
1. Choose the appropriate category (api/, architecture/, examples/)
2. Use clear, descriptive filenames in UPPER_CASE.md format
3. Update this README.md index
4. Cross-reference related documentation
5. Include code examples where applicable
6. Document any API findings with evidence from sample responses

## Documentation Status

- ✅ **API Reference** - Complete comprehensive documentation
- ⏳ **Architecture** - To be created
- ⏳ **Examples** - To be created

## Additional Resources

- [CLAUDE.md](../CLAUDE.md) - Project guidelines for Claude Code
- Research Materials: `research/eg4_web_monitor/` - Reference implementation
- Sample API Responses: `research/eg4_web_monitor/.../samples/` - Real API data

---

Last Updated: 2025-11-18
