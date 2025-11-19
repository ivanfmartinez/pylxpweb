"""Tests for register mapping constants."""

from __future__ import annotations

from pylxpweb.registers import (
    REGISTER_BLOCKS_18KPV,
    REGISTER_BLOCKS_GRIDBOSS,
    get_all_parameters,
    get_register_block,
)


class TestRegisterBlocks:
    """Test register block constants."""

    def test_18kpv_blocks_structure(self) -> None:
        """Test that 18KPV register blocks have correct structure."""
        for register, block in REGISTER_BLOCKS_18KPV.items():
            # Verify key presence
            assert "register" in block
            assert "size" in block
            assert "read_start" in block
            assert "read_size" in block
            assert "parameters" in block

            # Verify types
            assert isinstance(block["register"], int)
            assert isinstance(block["size"], int)
            assert isinstance(block["read_start"], int)
            assert isinstance(block["read_size"], int)
            assert isinstance(block["parameters"], list)

            # Verify values
            assert block["register"] == register
            assert block["size"] > 0
            assert block["read_size"] > 0
            assert len(block["parameters"]) > 0

            # Verify read_start <= register (may have leading empty registers)
            assert block["read_start"] <= block["register"]

            # Verify read_size >= size (must include leading empty registers)
            assert block["read_size"] >= block["size"]

    def test_gridboss_blocks_structure(self) -> None:
        """Test that GridBOSS register blocks have correct structure."""
        for register, block in REGISTER_BLOCKS_GRIDBOSS.items():
            # Verify key presence
            assert "register" in block
            assert "size" in block
            assert "read_start" in block
            assert "read_size" in block
            assert "parameters" in block

            # Verify types
            assert isinstance(block["register"], int)
            assert isinstance(block["size"], int)
            assert isinstance(block["read_start"], int)
            assert isinstance(block["read_size"], int)
            assert isinstance(block["parameters"], list)

            # Verify values
            assert block["register"] == register
            assert block["size"] > 0
            assert block["read_size"] > 0
            assert len(block["parameters"]) > 0

            # Verify read_start <= register
            assert block["read_start"] <= block["register"]

            # Verify read_size >= size
            assert block["read_size"] >= block["size"]

    def test_18kpv_known_registers(self) -> None:
        """Test specific known 18KPV register blocks."""
        # HOLD_MODEL - multi-register at register 0
        block = REGISTER_BLOCKS_18KPV[0]
        assert block["register"] == 0
        assert block["size"] == 2
        assert block["read_start"] == 0
        assert block["read_size"] == 2
        assert "HOLD_MODEL" in block["parameters"]

        # HOLD_SERIAL_NUM - multi-register at register 2
        block = REGISTER_BLOCKS_18KPV[2]
        assert block["register"] == 2
        assert block["size"] == 5
        assert block["read_start"] == 2
        assert block["read_size"] == 5
        assert "HOLD_SERIAL_NUM" in block["parameters"]

        # HOLD_TIME - multi-register with leading empty
        block = REGISTER_BLOCKS_18KPV[12]
        assert block["register"] == 12
        assert block["size"] == 3
        assert block["read_start"] == 11
        assert block["read_size"] == 4
        assert "HOLD_TIME" in block["parameters"]

        # HOLD_UVF_DERATE_START_POINT - large block with many leading empty
        block = REGISTER_BLOCKS_18KPV[134]
        assert block["register"] == 134
        assert block["size"] == 1
        assert block["read_start"] == 126
        assert block["read_size"] == 9
        assert "HOLD_UVF_DERATE_START_POINT" in block["parameters"]

    def test_gridboss_known_registers(self) -> None:
        """Test specific known GridBOSS register blocks."""
        # HOLD_MODEL - multi-register at register 0
        block = REGISTER_BLOCKS_GRIDBOSS[0]
        assert block["register"] == 0
        assert block["size"] == 2
        assert block["read_start"] == 0
        assert block["read_size"] == 2
        assert "HOLD_MODEL" in block["parameters"]

        # HOLD_SERIAL_NUM - multi-register at register 2
        block = REGISTER_BLOCKS_GRIDBOSS[2]
        assert block["register"] == 2
        assert block["size"] == 5
        assert block["read_start"] == 2
        assert block["read_size"] == 5
        assert "HOLD_SERIAL_NUM" in block["parameters"]

        # HOLD_TIME - multi-register with leading empty
        block = REGISTER_BLOCKS_GRIDBOSS[12]
        assert block["register"] == 12
        assert block["size"] == 3
        assert block["read_start"] == 11
        assert block["read_size"] == 4
        assert "HOLD_TIME" in block["parameters"]

        # GridBOSS-specific parameter with large leading empty registers
        block = REGISTER_BLOCKS_GRIDBOSS[2099]
        assert block["register"] == 2099
        assert block["read_start"] == 2033
        assert block["read_size"] == 67
        assert "MIDBOX_HOLD_BUSBAR_PCS_RATING" in block["parameters"]


class TestRegisterHelpers:
    """Test helper functions."""

    def test_get_register_block_18kpv(self) -> None:
        """Test get_register_block for 18KPV."""
        block = get_register_block("18KPV", 0)
        assert block is not None
        assert block["register"] == 0
        assert "HOLD_MODEL" in block["parameters"]

        block = get_register_block("18KPV", 2)
        assert block is not None
        assert block["register"] == 2
        assert "HOLD_SERIAL_NUM" in block["parameters"]

        block = get_register_block("18KPV", 12)
        assert block is not None
        assert block["register"] == 12
        assert "HOLD_TIME" in block["parameters"]

    def test_get_register_block_gridboss(self) -> None:
        """Test get_register_block for GridBOSS."""
        block = get_register_block("GridBOSS", 0)
        assert block is not None
        assert block["register"] == 0
        assert "HOLD_MODEL" in block["parameters"]

        block = get_register_block("GridBOSS", 2)
        assert block is not None
        assert block["register"] == 2
        assert "HOLD_SERIAL_NUM" in block["parameters"]

        block = get_register_block("GridBOSS", 2099)
        assert block is not None
        assert block["register"] == 2099
        assert "MIDBOX_HOLD_BUSBAR_PCS_RATING" in block["parameters"]

    def test_get_register_block_not_found(self) -> None:
        """Test get_register_block with invalid register."""
        block = get_register_block("18KPV", 9999)
        assert block is None

        block = get_register_block("GridBOSS", 9999)
        assert block is None

    def test_get_register_block_invalid_device(self) -> None:
        """Test get_register_block with invalid device type."""
        block = get_register_block("INVALID", 0)
        assert block is None

    def test_get_all_parameters_18kpv(self) -> None:
        """Test get_all_parameters for 18KPV."""
        params = get_all_parameters("18KPV")
        assert isinstance(params, set)
        assert len(params) == 51
        assert "HOLD_MODEL" in params
        assert "HOLD_SERIAL_NUM" in params
        assert "HOLD_TIME" in params
        assert "HOLD_UVF_DERATE_START_POINT" in params

    def test_get_all_parameters_gridboss(self) -> None:
        """Test get_all_parameters for GridBOSS."""
        params = get_all_parameters("GridBOSS")
        assert isinstance(params, set)
        assert len(params) == 54
        assert "HOLD_MODEL" in params
        assert "HOLD_SERIAL_NUM" in params
        assert "HOLD_TIME" in params
        assert "MIDBOX_HOLD_BUSBAR_PCS_RATING" in params

    def test_get_all_parameters_invalid_device(self) -> None:
        """Test get_all_parameters with invalid device type."""
        params = get_all_parameters("INVALID")
        assert isinstance(params, set)
        assert len(params) == 0


class TestRegisterMapping:
    """Test register mapping integrity."""

    def test_no_duplicate_registers_18kpv(self) -> None:
        """Test that 18KPV has no duplicate register positions."""
        registers = list(REGISTER_BLOCKS_18KPV.keys())
        assert len(registers) == len(set(registers))

    def test_no_duplicate_registers_gridboss(self) -> None:
        """Test that GridBOSS has no duplicate register positions."""
        registers = list(REGISTER_BLOCKS_GRIDBOSS.keys())
        assert len(registers) == len(set(registers))

    def test_18kpv_register_count(self) -> None:
        """Test expected number of 18KPV register blocks."""
        assert len(REGISTER_BLOCKS_18KPV) == 26

    def test_gridboss_register_count(self) -> None:
        """Test expected number of GridBOSS register blocks."""
        assert len(REGISTER_BLOCKS_GRIDBOSS) == 22

    def test_18kpv_parameter_count(self) -> None:
        """Test expected number of unique 18KPV parameters."""
        params = get_all_parameters("18KPV")
        assert len(params) == 51

    def test_gridboss_parameter_count(self) -> None:
        """Test expected number of unique GridBOSS parameters."""
        params = get_all_parameters("GridBOSS")
        assert len(params) == 54

    def test_leading_empty_registers(self) -> None:
        """Test that blocks with leading empty registers are correctly defined."""
        # 18KPV: Register 134 has 8 leading empty registers (126-133)
        block = REGISTER_BLOCKS_18KPV[134]
        assert block["read_start"] == 126
        assert block["register"] == 134
        assert block["register"] - block["read_start"] == 8  # 8 leading empty

        # GridBOSS: Register 137 has 11 leading empty registers (126-136)
        block = REGISTER_BLOCKS_GRIDBOSS[137]
        assert block["read_start"] == 126
        assert block["register"] == 137
        assert block["register"] - block["read_start"] == 11  # 11 leading empty

    def test_common_parameters_both_devices(self) -> None:
        """Test that common parameters exist in both device types."""
        params_18kpv = get_all_parameters("18KPV")
        params_gridboss = get_all_parameters("GridBOSS")

        # Common parameters
        common = params_18kpv & params_gridboss
        assert "HOLD_SERIAL_NUM" in common
        assert "HOLD_TIME" in common
        assert "HOLD_DEVICE_TYPE_CODE" in common

    def test_device_specific_parameters(self) -> None:
        """Test that device-specific parameters are properly separated."""
        params_18kpv = get_all_parameters("18KPV")
        params_gridboss = get_all_parameters("GridBOSS")

        # GridBOSS should have MIDBOX-specific parameters
        gridboss_only = params_gridboss - params_18kpv
        midbox_params = [p for p in gridboss_only if "MIDBOX_" in p or "MID_" in p]
        assert len(midbox_params) > 0, (
            f"Expected GridBOSS to have MIDBOX/MID params, got {gridboss_only}"
        )
