from __future__ import annotations

import aiohttp
import asyncio
from datetime import datetime, timezone
from typing import Any, Literal, cast


timeout = aiohttp.ClientTimeout(total=20, connect=5)


def _convert_timestamp(stamp: str) -> datetime:
    return datetime.strptime(
        stamp, "%Y-%m-%dT%H:%M:%S.%f%z"
    ).astimezone(timezone.utc).replace(microsecond=0, tzinfo=None)


def _convert_title(text: str) -> str:
    return text.replace('_', ' ').title()


# These has been taken from the status page CSS sheet
colors: dict[str, int] = {
    # Just color names
    "green": 0x26935C,
    "blue": 0x3498DB,
    "yellow": 0xFCCF2C,
    "orange": 0xE8740F,
    "red": 0xE74C3C,

    # Component statuses:
    "operational": 0x26935C,           # green
    "under_maintenance": 0x3498DB,     # blue
    "degraded_performance": 0xFCCF2C,  # yellow
    "partial_outage": 0xE8740F,        # orange
    "major_outage": 0xE74C3C,          # red

    # Incident and Scheduled Maintenance impacts:
    "none": 0x26935C,         # green
    "maintenance": 0x3498DB,  # blue
    "minor": 0xFCCF2C,        # yellow
    "major": 0xE8740F,        # orange
    "critical": 0xE74C3C,     # red
}


class _Base:
    """
    Represents basic data class.
    """
    def __init__(self, base_data: dict[str, Any]):
        self.id: str = base_data["id"]
        self.created_at: datetime = _convert_timestamp(base_data["created_at"])
        self.updated_at: datetime = _convert_timestamp(base_data["updated_at"])


class _NameBase(_Base):
    """
    Represents basic named data class.
    """
    color = 0

    def __init__(self, base_data: dict[str, Any]):
        super().__init__(base_data)
        self.name: str = base_data["name"]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.name}"

    @property
    def colour(self) -> int:
        """
        Color attribute alias.
        """
        return self.color


class _BaseComponent(_NameBase):
    """
    Represents basic component data class.
    """
    def __init__(self, comp_data: dict[str, Any]):
        super().__init__(comp_data)
        self.status = cast(
            Literal[
                "Operational",
                "Under Maintenance",
                "Degraded Performance",
                "Partial Outage",
                "Major Outage",
            ],
            _convert_title(comp_data["status"]),
        )
        self.color: int = colors[comp_data["status"]]
        self.incidents: list[Incident] = []
        self.maintenances: list[Maintenance] = []


class _BaseEvent(_NameBase):
    """
    Represents basic event data class.
    """
    def __init__(self, event_data: dict[str, Any]):
        super().__init__(event_data)
        self.status: str = _convert_title(event_data["status"])
        self.impact: str = _convert_title(event_data["impact"])
        self.color: int = colors[event_data["impact"]]
        self.components: list[Component] = []


class Update(_Base):
    """
    Represents an incident or scheduled maintenance status update.

    Attributes
    ----------
    id : str
        The ID of the update.
    created_at : datetime.datetime
        The time when this update was created.
    updated_at : datetime.datetime
        The last time this update was updated.
    description : str
        Description explaining what this update is about.
    status : str
        The status of this update.
    """
    def __init__(self, update_data: dict[str, Any]):
        super().__init__(update_data)
        self.description: str = update_data["body"]
        self.status: str = _convert_title(update_data["status"])

    def __repr__(self) -> str:
        return f"{self.status}: {self.description}"


class Incident(_BaseEvent):
    """
    Represents an incident.

    Attributes
    ----------
    id : str
        The ID of the incident.
    created_at : datetime.datetime
        The time when this incident was created.
    updated_at : datetime.datetime
        The last time this incident was updated.
    name : str
        The name of the incident.
    status : Literal["Investigating", "Identified", "Monitoring", "Resolved", "Postmortem"]
        The current incident's status.
    impact : Literal["None", "Minor", "Major", "Critical"]
        The impact of this incident.
    color : int
        The color associated with this incident (based on impact).\n
        There is an alias for this under ``colour``.
    components : list[Component]
        A list of components affected by this incident.
    updates : list[Update]
        A list of updates this incident has.
    last_update : Update
        The most recent update this incident has.
    """
    def __init__(self, inc_data: dict[str, Any], comp_mapping: dict[str, Component]):
        super().__init__(inc_data)
        self.status: Literal["Investigating", "Identified", "Monitoring", "Resolved", "Postmortem"]
        self.impact: Literal["None", "Minor", "Major", "Critical"]
        self.updates: list[Update] = [Update(u) for u in inc_data["incident_updates"]]
        self.last_update: Update = self.updates[0]
        for comp_data in inc_data["components"]:
            comp = comp_mapping.get(comp_data["id"])
            if comp:  # pragma: no branch
                self.components.append(comp)
                comp._add_incident(self)


class Maintenance(_BaseEvent):
    """
    Represents a (scheduled) maintenance.

    Attributes
    ----------
    id : str
        The ID of the maintenance.
    created_at : datetime.datetime
        The time when this maintenance was created.
    updated_at : datetime.datetime
        The last time this maintenance was updated.
    name : str
        The name of the maintenance.
    status : Literal["Scheduled", "In Progress", "Verifying", "Completed"]
        The current maintenance's status.
    impact : Literal["Maintenance"]
        The impact of this maintenance.
    color : int
        The color associated with this maintenance (based on impact).\n
        There is an alias for this under ``colour``.
    components : list[Component]
        A list of components affected by this maintenance.
    scheduled_for : datetime.datetime
        The planned time this maintenance is to start.
    scheduled_until : datetime.datetime
        The planned time this maintenance is to end.
    updates : list[Update]
        A list of updates this maintenance has.
    last_update : Update
        The most recent update this maintenance has.
    """
    def __init__(self, main_data: dict[str, Any], comp_mapping: dict[str, Component]):
        super().__init__(main_data)
        self.status: Literal["Scheduled", "In Progress", "Verifying", "Completed"]
        self.impact: Literal["Maintenance"]
        self.scheduled_for: datetime = _convert_timestamp(main_data["scheduled_for"])
        self.scheduled_until: datetime = _convert_timestamp(main_data["scheduled_until"])
        self.updates: list[Update] = [Update(u) for u in main_data["incident_updates"]]
        self.last_update: Update = self.updates[0]
        for comp_data in main_data["components"]:
            comp = comp_mapping.get(comp_data["id"])
            if comp:  # pragma: no branch
                self.components.append(comp)
                comp._add_mainenance(self)


class Component(_BaseComponent):
    """
    Represents a status component.

    Attributes
    ----------
    id : str
        The ID of the component.
    created_at : datetime.datetime
        The time when this component was created.
    updated_at : datetime.datetime
        The last time this component was updated.
    name : str
        The name of the component.
    status : Literal["Operational",\
        "Under Maintenance",\
        "Degraded Performance",\
        "Partial Outage",\
        "Major Outage"]
        The current component's status.
    color : int
        The color associated with this component (based on status).\n
        There is an alias for this under ``colour``.
    group : ComponentGroup | None
        The component group this component belongs to.\n
        Can be `None` if it belongs to no group.
    incidents : list[Incident]
        A list of incidents referring to this component.
    maintenances : list[Maintenance]
        A list of maintenances referring to this component.
    """
    def __init__(self, group: ComponentGroup | None, comp_data: dict[str, Any]):
        super().__init__(comp_data)
        self.group: ComponentGroup | None = group
        if group:  # pragma: no branch
            group._add_component(self)

    def _add_incident(self, incident: Incident):
        self.incidents.append(incident)
        if self.group:  # pragma: no branch
            self.group._add_incident(incident)

    def _add_mainenance(self, maintenance: Maintenance):
        self.maintenances.append(maintenance)
        if self.group:  # pragma: no branch
            self.group._add_mainenance(maintenance)


class ComponentGroup(_BaseComponent):
    """
    Represents a component's group.

    Attributes
    ----------
    id : str
        The ID of the component group.
    created_at : datetime.datetime
        The time when this component group was created.
    updated_at : datetime.datetime
        The last time this component group was updated.
    name : str
        The name of the component group.
    status : Literal["Operational",\
        "Under Maintenance",\
        "Degraded Performance",\
        "Partial Outage",\
        "Major Outage"]
        The current component group's status.\n
        This represents the worst status of all of the components in a group.\n
        ``Under Maintenance`` is considered second worst.
    color : int
        The color associated with this component (based on status).\n
        There is an alias for this under ``colour``.
    components : list[Component]
        A list of components this group has.
    incidents : list[Incident]
        A list of incidents referring to components of this group.
    maintenances : list[Maintenance]
        A list of scheduled maintenances referring to components of this group.
    """
    def __init__(self, group_data: dict[str, Any]):
        super().__init__(group_data)
        self.components: list[Component] = []

    def _add_component(self, comp: Component):
        self.components.append(comp)

    def _add_incident(self, incident: Incident):
        if incident not in self.incidents:
            self.incidents.append(incident)

    def _add_mainenance(self, maintenance: Maintenance):
        if maintenance not in self.maintenances:
            self.maintenances.append(maintenance)


class CurrentStatus:
    """
    Represents the current server's status.

    Attributes
    ----------
    id : str
        The ID of the status page.
    name : str
        The name of the status page.
    updated_at : datetime.datetime
        The timestamp of when the current status was last updated.
    status : Literal["All Systems Operational",\
        "Major System Outage",\
        "Partial System Outage",\
        "Minor Service Outage",\
        "Degraded System Service",\
        "Partially Degraded Service",\
        "Service Under Maintenance"]
        The current overall page's status.
    impact : Literal["None", "Minor", "Major", "Critical"]
        The current overall page's impact.
    color : int
        The color associated with this status (based on impact).\n
        There is an alias for this under ``colour``.
    components : list[Component]
        A list of components this status page contains.
        This doesn't include groups.
    groups : list[ComponentGroup]
        A list of component groups this status page contains.
        This includes groups only.
    incidents : list[Incident]
        A list of current incidents.
    maintenances : list[Maintenance]
        A list of scheduled maintenances.
    """
    def __init__(self, page_data: dict[str, Any]):
        status = page_data["status"]
        self.status: Literal[
            "All Systems Operational",
            "Major System Outage",
            "Partial System Outage",
            "Minor Service Outage",
            "Degraded System Service",
            "Partially Degraded Service",
            "Service Under Maintenance",
        ] = status["description"]
        self.impact: Literal["None", "Minor", "Major", "Critical"] = cast(
            Literal["None", "Minor", "Major", "Critical"],
            _convert_title(status["indicator"]),
        )
        self.color = colors[status["indicator"]]
        self.colour = self.color  # color alias
        page: dict[str, Any] = page_data["page"]
        self.id: str = page["id"]
        self.name: str = page["name"]
        self.updated_at: datetime = _convert_timestamp(page["updated_at"])

        self.groups: list[ComponentGroup] = [
            ComponentGroup(c) for c in page_data["components"] if c["group"]
        ]
        id_groups: dict[str, ComponentGroup] = {g.id: g for g in self.groups}
        self.components: list[Component] = [
            Component(id_groups.get(c["group_id"]), c)  # group can be None
            for c in page_data["components"]
            if not c["group"]
        ]
        id_components: dict[str, Component] = {c.id: c for c in self.components}

        # lookup mappings
        self._groups: dict[str, ComponentGroup] = {g.name: g for g in self.groups}
        self._groups.update(id_groups)
        self._components: dict[str, Component] = {c.name: c for c in self.components}
        self._components.update(id_components)

        self.incidents: list[Incident] = [
            Incident(i, id_components) for i in page_data["incidents"]
        ]
        self.maintenances: list[Maintenance] = [
            Maintenance(sm, id_components) for sm in page_data["scheduled_maintenances"]
        ]

    def component(self, component: str) -> Component | None:
        """
        Lookup a component of this status by either it's ID or Name.

        Parameters
        ----------
        component : str
            The component's ID or Name you want to get.

        Returns
        -------
        Component | None
            The component requested.\n
            `None` is returned if no components matched.
        """
        return self._components.get(component)

    def group(self, group: str) -> ComponentGroup | None:
        """
        Lookup a component group of this status by either it's ID or Name.

        Parameters
        ----------
        group : str
            The component group's ID or Name you want to get.

        Returns
        -------
        ComponentGroup | None
            The component group requested.\n
            `None` is returned if no component groups matched.
        """
        return self._groups.get(group)


class StatusPage:
    """
    An object representing StatusPage access.

    Parameters
    ----------
    url : str
        The URL of the StatusPage you want to get this object for.
    """
    def __init__(self, url: str, *, loop: asyncio.AbstractEventLoop | None = None):
        if loop is None:  # pragma: no cover
            loop = asyncio.get_event_loop()
        self.url: str = url.rstrip('/')
        self._session = aiohttp.ClientSession(timeout=timeout, loop=loop)

    def __del__(self):
        self._session.detach()

    async def close(self):
        await self._session.close()  # pragma: no cover

    # async with integration
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        await self._session.close()

    async def request(self, endpoint: str):
        for tries in range(5):  # pragma: no branch
            try:
                async with self._session.get(f"{self.url}/api/v2/{endpoint}") as response:
                    response.raise_for_status()
                    return await response.json()
            except (
                aiohttp.ClientConnectionError, asyncio.TimeoutError
            ) as exc:  # pragma: no cover
                last_exc = exc
                await asyncio.sleep(0.5)
        raise last_exc  # pragma: no cover

    async def get_status(self) -> CurrentStatus:
        """
        Fetches the current statuspage's status.

        Returns
        -------
        CurrentStatus
            The current status requested.

        Raises
        ------
        aiohttp.ClientError
            When there was an error while fetching the current status.
        """
        response = await self.request("summary.json")
        return CurrentStatus(response)
