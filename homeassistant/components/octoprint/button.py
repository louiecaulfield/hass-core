"""Support for Octoprint buttons."""
from pyoctoprintapi import OctoprintClient, OctoprintPrinterInfo

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import OctoprintDataUpdateCoordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Octoprint control buttons."""
    coordinator: OctoprintDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]
    client: OctoprintClient = hass.data[DOMAIN][config_entry.entry_id]["client"]
    device_id = config_entry.unique_id
    assert device_id is not None

    async_add_entities(
        [
            OctoprintResumeJobButton(coordinator, device_id, client),
            OctoprintPauseJobButton(coordinator, device_id, client),
            OctoprintStopJobButton(coordinator, device_id, client),
            OctoprintConnectButton(coordinator, device_id, client),
        ]
    )


class OctoprintButton(CoordinatorEntity[OctoprintDataUpdateCoordinator], ButtonEntity):
    """Represent an OctoPrint binary sensor."""

    client: OctoprintClient

    def __init__(
        self,
        coordinator: OctoprintDataUpdateCoordinator,
        button_type: str,
        device_id: str,
        client: OctoprintClient,
    ) -> None:
        """Initialize a new OctoPrint button."""
        super().__init__(coordinator)
        self.client = client
        self._device_id = device_id
        self._attr_name = f"OctoPrint {button_type}"
        self._attr_unique_id = f"{button_type}-{device_id}"
        self._attr_device_info = coordinator.device_info

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data["printer"]


class OctoprintPauseJobButton(OctoprintButton):
    """Pause the active job."""

    def __init__(
        self,
        coordinator: OctoprintDataUpdateCoordinator,
        device_id: str,
        client: OctoprintClient,
    ) -> None:
        """Initialize a new OctoPrint button."""
        super().__init__(coordinator, "Pause Job", device_id, client)

    async def async_press(self) -> None:
        """Handle the button press."""
        printer: OctoprintPrinterInfo = self.coordinator.data["printer"]

        if printer.state.flags.printing:
            await self.client.pause_job()
        elif not printer.state.flags.paused and not printer.state.flags.pausing:
            raise InvalidPrinterState("Printer is not printing")


class OctoprintResumeJobButton(OctoprintButton):
    """Resume the active job."""

    def __init__(
        self,
        coordinator: OctoprintDataUpdateCoordinator,
        device_id: str,
        client: OctoprintClient,
    ) -> None:
        """Initialize a new OctoPrint button."""
        super().__init__(coordinator, "Resume Job", device_id, client)

    async def async_press(self) -> None:
        """Handle the button press."""
        printer: OctoprintPrinterInfo = self.coordinator.data["printer"]

        if printer.state.flags.paused:
            await self.client.resume_job()
        elif not printer.state.flags.printing and not printer.state.flags.resuming:
            raise InvalidPrinterState("Printer is not currently paused")


class OctoprintStopJobButton(OctoprintButton):
    """Resume the active job."""

    def __init__(
        self,
        coordinator: OctoprintDataUpdateCoordinator,
        device_id: str,
        client: OctoprintClient,
    ) -> None:
        """Initialize a new OctoPrint button."""
        super().__init__(coordinator, "Stop Job", device_id, client)

    async def async_press(self) -> None:
        """Handle the button press."""
        printer: OctoprintPrinterInfo = self.coordinator.data["printer"]

        if printer.state.flags.printing or printer.state.flags.paused:
            await self.client.cancel_job()


class OctoprintConnectButton(OctoprintButton):
    """Connect to printer."""

    def __init__(
        self,
        coordinator: OctoprintDataUpdateCoordinator,
        device_id: str,
        client: OctoprintClient,
    ) -> None:
        """Initialize a new OctoPrint button."""
        super().__init__(coordinator, "Connect Printer", device_id, client)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data["printer"] is None
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        printer: OctoprintPrinterInfo = self.coordinator.data["printer"]

        if printer is None:
            await self.client.connect()
            await self.coordinator.async_refresh()


class InvalidPrinterState(HomeAssistantError):
    """Service attempted in invalid state."""
