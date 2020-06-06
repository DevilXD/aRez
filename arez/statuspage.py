from __future__ import annotations

import aiohttp
from datetime import datetime, timezone
from typing import Optional, List, Dict, Literal, cast


def _convert_timestamp(stamp: str) -> datetime:
    return datetime.strptime(
        stamp[:-3] + stamp[-2:], "%Y-%m-%dT%H:%M:%S.%f%z"
    ).astimezone(timezone.utc).replace(tzinfo=None).replace(microsecond=0)


def _convert_title(text: str) -> str:
    return text.replace('_', ' ').title()


# These has been taken from the status page CSS sheet
_colors: Dict[str, int] = {
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
    def __init__(self, base_data: dict):
        self.id: str = base_data["id"]
        self.created_at = _convert_timestamp(base_data["created_at"])
        self.updated_at = _convert_timestamp(base_data["updated_at"])


class _NameBase(_Base):
    """
    Represents basic named data class.
    """
    color = 0

    def __init__(self, base_data: dict):
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
    def __init__(self, comp_data: dict):
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
        self.color = _colors[comp_data["status"]]
        self.incidents: List["Incident"] = []
        self.scheduled_maintenances: List["ScheduledMaintenance"] = []


class _BaseEvent(_NameBase):
    """
    Represents basic event data class.
    """
    def __init__(self, event_data: dict):
        super().__init__(event_data)
        self.status = _convert_title(event_data["status"])
        self.impact = _convert_title(event_data["impact"])
        self.color = _colors[event_data["impact"]]
        self.components: List["Component"] = []


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
    def __init__(self, upd_data: dict):
        super().__init__(upd_data)
        self.description: str = upd_data["body"]
        self.status: str = _convert_title(upd_data["status"])

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
    components : List[Component]
        A list of componnets affected by this incident.
    updates : List[Update]
        A list of updates this incident has.
    last_update : Update
        The most recent update this incident has.
    """
    def __init__(self, inc_data: dict, comp_mapping: Dict[str, "Component"]):
        super().__init__(inc_data)
        self.status: Literal["Investigating", "Identified", "Monitoring", "Resolved", "Postmortem"]
        self.impact: Literal["None", "Minor", "Major", "Critical"]
        self.updates: List[Update] = [Update(u) for u in inc_data["incident_updates"]]
        self.last_update = self.updates[0]
        for comp_data in inc_data["components"]:
            comp = comp_mapping.get(comp_data["id"])
            if comp:  # pragma: no branch
                self.components.append(comp)
                comp._add_incident(self)


class ScheduledMaintenance(_BaseEvent):
    """
    Represents a scheduled maintenance.

    Attributes
    ----------
    id : str
        The ID of the scheduled maintenance.
    created_at : datetime.datetime
        The time when this scheduled maintenance was created.
    updated_at : datetime.datetime
        The last time this scheduled maintenance was updated.
    name : str
        The name of the scheduled maintenance.
    status : Literal["Scheduled", "In Progress", "Verifying", "Completed"]
        The current scheduled maintenance's status.
    impact : Literal["Maintenance"]
        The impact of this scheduled maintenance.
    color : int
        The color associated with this scheduled maintenance (based on impact).\n
        There is an alias for this under ``colour``.
    components : List[Component]
        A list of componnets affected by this scheduled maintenance.
    scheduled_for : datetime.datetime
        The planned time this maintenance is scheduled to start.
    scheduled_until : datetime.datetime
        The planned time this maintenance is scheduled to end.
    updates : List[Update]
        A list of updates this scheduled maintenance has.
    last_update : Update
        The most recent update this scheduled maintenance has.
    """
    def __init__(self, main_data: dict, comp_mapping: Dict[str, "Component"]):
        super().__init__(main_data)
        self.status: Literal["Scheduled", "In Progress", "Verifying", "Completed"]
        self.impact: Literal["Maintenance"]
        self.scheduled_for = _convert_timestamp(main_data["scheduled_for"])
        self.scheduled_until = _convert_timestamp(main_data["scheduled_until"])
        self.updates: List[Update] = [Update(u) for u in main_data["incident_updates"]]
        self.last_update = self.updates[0]
        for comp_data in main_data["components"]:
            comp = comp_mapping.get(comp_data["id"])
            if comp:  # pragma: no branch
                self.components.append(comp)
                comp._add_scheduled_mainenance(self)


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
    group : Optional[ComponentGroup]
        The component group this component belongs to.\n
        Can be `None` if it belongs to no group.
    incidents : List[Incident]
        A list of incidents referring to this component.
    scheduled_maintenances : List[ScheduledMaintenance]
        A list of scheduled maintenances referring to this component.
    """
    def __init__(self, group: Optional[ComponentGroup], comp_data: dict):
        super().__init__(comp_data)
        self.group = group
        if group:  # pragma: no branch
            group._add_component(self)

    def _add_incident(self, incident: Incident):
        self.incidents.append(incident)
        if self.group:  # pragma: no branch
            self.group._add_incident(incident)

    def _add_scheduled_mainenance(self, scheduled_maintenance: ScheduledMaintenance):
        self.scheduled_maintenances.append(scheduled_maintenance)
        if self.group:  # pragma: no branch
            self.group._add_scheduled_mainenance(scheduled_maintenance)


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
    components : List[Component]
        A list of components this group has.
    incidents : List[Incident]
        A list of incidents referring to components of this group.
    scheduled_maintenances : List[ScheduledMaintenance]
        A list of scheduled maintenances referring to components of this group.
    """
    def __init__(self, group_data: dict):
        super().__init__(group_data)
        self.components: List[Component] = []

    def _add_component(self, comp: Component):
        self.components.append(comp)

    def _add_incident(self, incident: Incident):
        if incident not in self.incidents:
            self.incidents.append(incident)

    def _add_scheduled_mainenance(self, scheduled_maintenance: ScheduledMaintenance):
        if scheduled_maintenance not in self.scheduled_maintenances:
            self.scheduled_maintenances.append(scheduled_maintenance)


class CurrentStatus:
    """
    Represents the current server's status.

    Attributes
    ----------
    id : str
        The ID of the status page.
    name : str
        The name of the status page.
    timezone : str
        The timezone of the status page.
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
    components : List[Component]
        A list of components this status page contains.
        This doesn't include groups.
    groups : List[ComponentGroup]
        A list of component groups this status page contains.
        This includes groups only.
    incidents : List[Incident]
        A list of current incidents.
    scheduled_maintenances : List[ScheduledMaintenance]
        A list of scheduled maintenances.
    """
    def __init__(self, page_data):
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
        self.impact = cast(
            Literal[
                "None", "Minor", "Major", "Critical"
            ],
            _convert_title(status["indicator"]),
        )
        self.color = _colors[status["indicator"]]
        self.colour = self.color  # color alias
        page = page_data["page"]
        self.name = page["name"]
        self.id = page["id"]
        self.timezone = page["time_zone"]
        self.updated_at = _convert_timestamp(page["updated_at"])

        self.groups = [ComponentGroup(c) for c in page_data["components"] if c["group"]]
        id_groups = {g.id: g for g in self.groups}
        self.components = [
            Component(id_groups.get(c["group_id"]), c)  # group can be None
            for c in page_data["components"]
            if not c["group"]
        ]
        id_components = {c.id: c for c in self.components}

        self._groups = {g.name: g for g in self.groups}  # lookup mapping
        self._groups.update(id_groups)
        self._components = {c.name: c for c in self.components}  # lookup mapping
        self._components.update(id_components)

        self.incidents = [Incident(i, id_components) for i in page_data["incidents"]]
        self.scheduled_maintenances = [
            ScheduledMaintenance(sm, id_components) for sm in page_data["scheduled_maintenances"]
        ]

    def component(self, component: str) -> Optional[Component]:
        """
        Lookup a component of this status by either it's ID or Name.

        Parameters
        ----------
        component : str
            The component's ID or Name you want to get.

        Returns
        -------
        Optional[Component]
            The component requested.\n
            `None` is returned if no components matched.
        """
        return self._components.get(component)

    def group(self, group: str) -> Optional[ComponentGroup]:
        """
        Lookup a component group of this status by either it's ID or Name.

        Parameters
        ----------
        group : str
            The component group's ID or Name you want to get.

        Returns
        -------
        Optional[ComponentGroup]
            The component group requested.\n
            `None` is returned if no component groups matched.
        """
        return self._groups.get(group)


class StatusPage:
    def __init__(self, url: str):
        self.url = f"{url.rstrip('/')}/api/v2"
        self._session = aiohttp.ClientSession(raise_for_status=True)

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
        route = f"{self.url}/{endpoint}"
        async with self._session.get(route) as response:
            return await response.json()

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
