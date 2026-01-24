"""Tests for Modbus transport implementation."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pylxpweb.transports.exceptions import (
    TransportConnectionError,
    TransportReadError,
    TransportWriteError,
)
from pylxpweb.transports.modbus import ModbusTransport


class TestModbusTransport:
    """Tests for ModbusTransport class."""

    def test_init_default_values(self) -> None:
        """Test Modbus transport initialization with defaults."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        assert transport.serial == "CE12345678"
        assert transport._host == "192.168.1.100"
        assert transport._port == 502
        assert transport._unit_id == 1
        assert transport._timeout == 10.0
        assert transport.is_connected is False

    def test_init_custom_values(self) -> None:
        """Test Modbus transport initialization with custom values."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
            port=8502,
            unit_id=2,
            timeout=30.0,
        )

        assert transport._port == 8502
        assert transport._unit_id == 2
        assert transport._timeout == 30.0

    def test_capabilities(self) -> None:
        """Test Modbus transport capabilities."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        caps = transport.capabilities
        assert caps.can_read_runtime is True
        assert caps.can_read_energy is True
        assert caps.can_read_battery is True
        assert caps.is_local is True
        assert caps.requires_authentication is False

    @pytest.mark.asyncio
    async def test_connect_success(self) -> None:
        """Test successful Modbus connection."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        # Mock the Modbus client - import is done inside connect()
        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client_class.return_value = mock_client

            await transport.connect()

            assert transport.is_connected is True
            mock_client.connect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self) -> None:
        """Test Modbus connection failure."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            with pytest.raises(TransportConnectionError, match="Failed to connect"):
                await transport.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        """Test Modbus disconnection."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.close = MagicMock()
            mock_client_class.return_value = mock_client

            await transport.connect()
            assert transport.is_connected is True

            await transport.disconnect()
            assert transport.is_connected is False
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_runtime_not_connected(self) -> None:
        """Test runtime read when not connected."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        # The ModbusTransport wraps TransportConnectionError in TransportReadError

        with pytest.raises(TransportReadError):
            await transport.read_runtime()

    @pytest.mark.asyncio
    async def test_read_runtime_success(self) -> None:
        """Test successful runtime read via Modbus.

        Uses the corrected PV_SERIES register layout:
        - PV power at regs 7-9 (16-bit)
        - Charge/discharge at regs 10-11 (16-bit)
        - Grid voltages at regs 12-14
        - Grid frequency at reg 15
        - Inverter power at reg 16
        - EPS power at reg 24
        - Load power at reg 27
        """
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.close = MagicMock()

            # Mock register read response with correct PV_SERIES layout
            mock_response = MagicMock()
            mock_response.isError.return_value = False
            # 128 registers for runtime data - using new layout
            mock_response.registers = [
                0,  # 0: Status
                5100,  # 1: PV1 voltage (×10 = 510V)
                5050,  # 2: PV2 voltage
                0,  # 3: PV3 voltage
                530,  # 4: Battery voltage (×10 = 53V)
                (100 << 8) | 85,  # 5: SOC=85 (low), SOH=100 (high)
                0,  # 6: (unused in new layout)
                1000,  # 7: PV1 power (16-bit)
                1500,  # 8: PV2 power (16-bit)
                0,  # 9: PV3 power (16-bit)
                500,  # 10: Charge power (16-bit)
                0,  # 11: Discharge power (16-bit)
                2410,  # 12: Grid voltage R (×10)
                2415,  # 13: Grid voltage S
                2420,  # 14: Grid voltage T
                5998,  # 15: Grid frequency (×100 = 59.98Hz)
                2300,  # 16: Inverter power (16-bit)
                100,  # 17: Grid power/AC charge (16-bit)
                50,  # 18: IinvRMS (×100 = 0.5A)
                990,  # 19: Power factor (×1000 = 0.99)
                2400,  # 20: EPS voltage R
                2405,  # 21: EPS voltage S
                2410,  # 22: EPS voltage T
                5999,  # 23: EPS frequency
                300,  # 24: EPS power (16-bit)
                1,  # 25: EPS status
                200,  # 26: Power to grid (16-bit)
                1500,  # 27: Load power (16-bit)
            ] + [0] * 100  # Fill remaining registers

            mock_client.read_input_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await transport.connect()
            runtime = await transport.read_runtime()

            assert runtime.pv1_voltage == pytest.approx(510.0, rel=0.01)
            assert runtime.battery_soc == 85
            assert runtime.grid_frequency == pytest.approx(59.98, rel=0.01)
            assert runtime.pv1_power == 1000.0
            assert runtime.load_power == 1500.0

    @pytest.mark.asyncio
    async def test_manual_connect_disconnect(self) -> None:
        """Test manual connect and disconnect."""
        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.close = MagicMock()
            mock_client_class.return_value = mock_client

            transport = ModbusTransport(
                host="192.168.1.100",
                serial="CE12345678",
            )

            await transport.connect()
            assert transport.is_connected is True

            await transport.disconnect()
            assert transport.is_connected is False
            mock_client.close.assert_called_once()


class TestModbusRegisterReading:
    """Tests for Modbus register reading."""

    @pytest.mark.asyncio
    async def test_read_parameters(self) -> None:
        """Test reading holding registers (parameters)."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.close = MagicMock()

            # Mock holding register response
            mock_response = MagicMock()
            mock_response.isError.return_value = False
            mock_response.registers = [100, 200, 300, 400, 500]

            mock_client.read_holding_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await transport.connect()
            params = await transport.read_parameters(0, 5)

            assert params[0] == 100
            assert params[1] == 200
            assert params[2] == 300
            assert params[3] == 400
            assert params[4] == 500

    @pytest.mark.asyncio
    async def test_read_parameters_chunked(self) -> None:
        """Test reading parameters in chunks (>40 registers)."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.close = MagicMock()

            # Each read returns 40 registers
            call_count = 0

            async def make_response(**kwargs: int) -> MagicMock:
                nonlocal call_count
                response = MagicMock()
                response.isError.return_value = False
                # Return different values for each chunk
                start = call_count * 40
                response.registers = list(range(start, start + 40))
                call_count += 1
                return response

            mock_client.read_holding_registers = make_response
            mock_client_class.return_value = mock_client

            await transport.connect()
            params = await transport.read_parameters(0, 80)

            # Verify we got 80 parameter values
            assert len(params) == 80

            # Check first chunk values (0-39)
            assert params[0] == 0
            assert params[39] == 39

            # Check second chunk values (40-79)
            assert params[40] == 40
            assert params[79] == 79

            # Verify call_count tracks the 2 calls
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_read_parameters_not_connected(self) -> None:
        """Test parameter read when not connected."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        with pytest.raises(TransportConnectionError, match="Transport not connected"):
            await transport.read_parameters(0, 10)

    @pytest.mark.asyncio
    async def test_read_parameters_modbus_error(self) -> None:
        """Test parameter read with Modbus error."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)

            # Mock error response
            mock_response = MagicMock()
            mock_response.isError.return_value = True

            mock_client.read_holding_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await transport.connect()

            with pytest.raises(TransportReadError, match="Modbus read error"):
                await transport.read_parameters(0, 10)

    @pytest.mark.asyncio
    async def test_write_parameters_success(self) -> None:
        """Test successful parameter write."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)

            # Mock successful write response
            mock_response = MagicMock()
            mock_response.isError.return_value = False

            mock_client.write_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await transport.connect()
            result = await transport.write_parameters({0: 100, 1: 200})

            assert result is True
            mock_client.write_registers.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_write_parameters_not_connected(self) -> None:
        """Test parameter write when not connected."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        with pytest.raises(TransportConnectionError, match="Transport not connected"):
            await transport.write_parameters({0: 100})

    @pytest.mark.asyncio
    async def test_write_parameters_modbus_error(self) -> None:
        """Test parameter write with Modbus error."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)

            # Mock error response
            mock_response = MagicMock()
            mock_response.isError.return_value = True

            mock_client.write_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await transport.connect()

            with pytest.raises(TransportWriteError, match="Modbus write error"):
                await transport.write_parameters({0: 100})

    @pytest.mark.asyncio
    async def test_write_parameters_consecutive_batching(self) -> None:
        """Test that consecutive parameters are batched into single writes."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)

            mock_response = MagicMock()
            mock_response.isError.return_value = False

            mock_client.write_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await transport.connect()

            # Write consecutive addresses - should be batched
            result = await transport.write_parameters({0: 100, 1: 200, 2: 300})
            assert result is True

            # Should be called once with all 3 values
            mock_client.write_registers.assert_awaited_once()
            call_args = mock_client.write_registers.call_args
            assert call_args.kwargs["address"] == 0
            assert call_args.kwargs["values"] == [100, 200, 300]

    @pytest.mark.asyncio
    async def test_write_parameters_non_consecutive_multiple_calls(self) -> None:
        """Test that non-consecutive parameters result in multiple writes."""
        transport = ModbusTransport(
            host="192.168.1.100",
            serial="CE12345678",
        )

        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)

            mock_response = MagicMock()
            mock_response.isError.return_value = False

            mock_client.write_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await transport.connect()

            # Write non-consecutive addresses - should result in multiple calls
            result = await transport.write_parameters({0: 100, 5: 500, 10: 1000})
            assert result is True

            # Should be called 3 times (one for each non-consecutive address)
            assert mock_client.write_registers.await_count == 3

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        """Test async context manager (async with)."""
        with patch("pymodbus.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.close = MagicMock()
            mock_client_class.return_value = mock_client

            transport = ModbusTransport(
                host="192.168.1.100",
                serial="CE12345678",
            )

            async with transport as t:
                assert t is transport
                assert transport.is_connected is True

            assert transport.is_connected is False
            mock_client.close.assert_called_once()
