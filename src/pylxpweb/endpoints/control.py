"""Device control endpoints for the Luxpower API.

This module provides device control functionality including:
- Parameter reading and writing
- Function enable/disable control
- Quick charge operations
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pylxpweb.endpoints.base import BaseEndpoint
from pylxpweb.models import (
    ParameterReadResponse,
    QuickChargeStatus,
    SuccessResponse,
)

if TYPE_CHECKING:
    from pylxpweb.client import LuxpowerClient


class ControlEndpoints(BaseEndpoint):
    """Device control endpoints for parameters, functions, and quick charge."""

    def __init__(self, client: LuxpowerClient) -> None:
        """Initialize control endpoints.

        Args:
            client: The parent LuxpowerClient instance
        """
        super().__init__(client)

    async def read_parameters(
        self,
        inverter_sn: str,
        start_register: int = 0,
        point_number: int = 127,
        auto_retry: bool = True,
    ) -> ParameterReadResponse:
        """Read configuration parameters from inverter registers.

        IMPORTANT: The API returns parameters as FLAT key-value pairs with
        descriptive names (like "HOLD_AC_CHARGE_POWER_CMD"), NOT nested under
        a 'parameters' field or using register numbers as keys!

        Common register ranges (web interface strategy):
        - 0-126 (startRegister=0, pointNumber=127) - System config, grid protection
        - 127-253 (startRegister=127, pointNumber=127) - Additional config
        - 240-366 (startRegister=240, pointNumber=127) - Extended parameters

        Critical registers (verified on 18KPV):
        - Register 21: Function enable bit field (27 bits including AC charge, EPS, standby)
        - Register 66: AC charge power command (HOLD_AC_CHARGE_POWER_CMD)
        - Register 67: AC charge SOC limit (HOLD_AC_CHARGE_SOC_LIMIT)
        - Register 70: AC charge schedule start (hour + minute)
        - Register 100: Battery discharge cutoff voltage
        - Register 110: System function bit field (14 bits including microgrid, eco mode)

        Example:
            >>> response = await client.control.read_parameters("1234567890", 66, 8)
            >>> # Access parameters directly from response
            >>> response.parameters["HOLD_AC_CHARGE_POWER_CMD"]
            50
            >>> response.parameters["HOLD_AC_CHARGE_SOC_LIMIT"]
            100
            >>> # Or access via model dump (includes all parameter keys at root level)
            >>> data = response.model_dump()
            >>> data["HOLD_AC_CHARGE_POWER_CMD"]
            50

            >>> # Read function enable register (27 bit fields)
            >>> response = await client.control.read_parameters("1234567890", 21, 1)
            >>> response.parameters["FUNC_AC_CHARGE"]
            True
            >>> response.parameters["FUNC_SET_TO_STANDBY"]
            False

        Args:
            inverter_sn: Inverter serial number (e.g., "1234567890")
            start_register: Starting register address
            point_number: Number of registers to read (max 127 in practice)
            auto_retry: Enable automatic retry on failure

        Returns:
            ParameterReadResponse: Contains inverterSn, deviceType, startRegister,
                pointNumber, and all parameter keys as flat attributes.
                Use .parameters property to get dict of parameter keys.

        See Also:
            - constants.REGISTER_TO_PARAM_KEYS_18KPV: Verified register→parameter mappings
            - research/REGISTER_NUMBER_MAPPING.md: Complete register documentation
        """
        await self.client._ensure_authenticated()

        data = {
            "inverterSn": inverter_sn,
            "startRegister": start_register,
            "pointNumber": point_number,
            "autoRetry": auto_retry,
        }

        cache_key = self._get_cache_key(
            "params", sn=inverter_sn, start=start_register, count=point_number
        )
        response = await self.client._request(
            "POST",
            "/WManage/web/maintain/remoteRead/read",
            data=data,
            cache_key=cache_key,
            cache_endpoint="parameter_read",
        )
        return ParameterReadResponse.model_validate(response)

    async def write_parameter(
        self,
        inverter_sn: str,
        hold_param: str,
        value_text: str,
        client_type: str = "WEB",
        remote_set_type: str = "NORMAL",
    ) -> SuccessResponse:
        """Write a configuration parameter to the inverter.

         WARNING: This changes device configuration!

        Common parameters:
        - HOLD_SYSTEM_CHARGE_SOC_LIMIT: Battery charge limit (%)
        - HOLD_SYSTEM_DISCHARGE_SOC_LIMIT: Battery discharge limit (%)
        - HOLD_AC_CHARGE_POWER: AC charge power limit (W)
        - HOLD_AC_DISCHARGE_POWER: AC discharge power limit (W)

        Args:
            inverter_sn: Inverter serial number
            hold_param: Parameter name to write
            value_text: Value to write (as string)
            client_type: Client type (WEB/APP)
            remote_set_type: Set type (NORMAL/QUICK)

        Returns:
            SuccessResponse: Operation result

        Example:
            # Set battery charge limit to 90%
            await client.control.write_parameter(
                "1234567890",
                "HOLD_SYSTEM_CHARGE_SOC_LIMIT",
                "90"
            )
        """
        await self.client._ensure_authenticated()

        data = {
            "inverterSn": inverter_sn,
            "holdParam": hold_param,
            "valueText": value_text,
            "clientType": client_type,
            "remoteSetType": remote_set_type,
        }

        response = await self.client._request(
            "POST", "/WManage/web/maintain/remoteSet/write", data=data
        )
        return SuccessResponse.model_validate(response)

    async def control_function(
        self,
        inverter_sn: str,
        function_param: str,
        enable: bool,
        client_type: str = "WEB",
        remote_set_type: str = "NORMAL",
    ) -> SuccessResponse:
        """Enable or disable a device function.

         WARNING: This changes device state!

        Common functions:
        - FUNC_EPS_EN: Battery backup (EPS) mode
        - FUNC_SET_TO_STANDBY: Standby mode
        - FUNC_GRID_PEAK_SHAVING: Peak shaving mode

        Args:
            inverter_sn: Inverter serial number
            function_param: Function parameter name
            enable: Enable or disable the function
            client_type: Client type (WEB/APP)
            remote_set_type: Set type (NORMAL/QUICK)

        Returns:
            SuccessResponse: Operation result

        Example:
            # Enable EPS mode
            await client.control.control_function(
                "1234567890",
                "FUNC_EPS_EN",
                True
            )

            # Disable standby mode
            await client.control.control_function(
                "1234567890",
                "FUNC_SET_TO_STANDBY",
                False
            )
        """
        await self.client._ensure_authenticated()

        data = {
            "inverterSn": inverter_sn,
            "functionParam": function_param,
            "enable": "true" if enable else "false",
            "clientType": client_type,
            "remoteSetType": remote_set_type,
        }

        response = await self.client._request(
            "POST", "/WManage/web/maintain/remoteSet/functionControl", data=data
        )
        return SuccessResponse.model_validate(response)

    async def start_quick_charge(
        self, inverter_sn: str, client_type: str = "WEB"
    ) -> SuccessResponse:
        """Start quick charge operation.

         WARNING: This starts charging!

        Args:
            inverter_sn: Inverter serial number
            client_type: Client type (WEB/APP)

        Returns:
            SuccessResponse: Operation result

        Example:
            result = await client.control.start_quick_charge("1234567890")
            if result.success:
                print("Quick charge started successfully")
        """
        await self.client._ensure_authenticated()

        data = {"inverterSn": inverter_sn, "clientType": client_type}

        response = await self.client._request(
            "POST", "/WManage/web/config/quickCharge/start", data=data
        )
        return SuccessResponse.model_validate(response)

    async def stop_quick_charge(
        self, inverter_sn: str, client_type: str = "WEB"
    ) -> SuccessResponse:
        """Stop quick charge operation.

         WARNING: This stops charging!

        Args:
            inverter_sn: Inverter serial number
            client_type: Client type (WEB/APP)

        Returns:
            SuccessResponse: Operation result

        Example:
            result = await client.control.stop_quick_charge("1234567890")
            if result.success:
                print("Quick charge stopped successfully")
        """
        await self.client._ensure_authenticated()

        data = {"inverterSn": inverter_sn, "clientType": client_type}

        response = await self.client._request(
            "POST", "/WManage/web/config/quickCharge/stop", data=data
        )
        return SuccessResponse.model_validate(response)

    async def get_quick_charge_status(self, inverter_sn: str) -> QuickChargeStatus:
        """Get current quick charge operation status.

        Args:
            inverter_sn: Inverter serial number

        Returns:
            QuickChargeStatus: Quick charge status

        Example:
            status = await client.control.get_quick_charge_status("1234567890")
            if status.is_charging:
                print("Quick charge is active")
        """
        await self.client._ensure_authenticated()

        data = {"inverterSn": inverter_sn}

        cache_key = self._get_cache_key("quick_charge", serialNum=inverter_sn)
        response = await self.client._request(
            "POST",
            "/WManage/web/config/quickCharge/getStatusInfo",
            data=data,
            cache_key=cache_key,
            cache_endpoint="quick_charge_status",
        )
        return QuickChargeStatus.model_validate(response)
