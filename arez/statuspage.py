import aiohttp
from abc import ABC
from typing import List
from datetime import datetime, timezone


def convert_timestamp(stamp: str):
    return datetime.strptime(
        stamp[:-3] + stamp[-2:], "%Y-%m-%dT%H:%M:%S.%f%z"
    ).astimezone(timezone.utc).replace(tzinfo=None).replace(microsecond=0)


class BaseComponent(ABC):
    def __init__(self, comp_data: dict):
        self.id: str = comp_data["id"]
        self.name: str = comp_data["name"]
        self.status: str = comp_data["status"]
        self.created_at = convert_timestamp(comp_data["created_at"])
        self.updated_at = convert_timestamp(comp_data["updated_at"])

    def __repr__(self) -> str:
        return "{0.__class__.__name__}: {0.name}".format(self)


class Update:
    """
    Represents an incident or scheduled maintenance status update.

    Attributes
    ----------
    id : str
        The ID of the update.
    description : str
        Description explaining what this update is about.
    status : str
        The component's status of this update.
    created_at : datetime
        The time when this update was created.
    updated_at : datetime
        The last time this update was updated.
    """
    def __init__(self, upd_data: dict):
        self.id: str = upd_data["id"]
        self.description: str = upd_data["body"]
        self.status: str = upd_data["status"]
        self.created_at = convert_timestamp(upd_data["created_at"])
        self.updated_at = convert_timestamp(upd_data["updated_at"])

    def __repr__(self) -> str:
        return "{}: {}".format(self.status.replace('_', ' ').title(), self.description)


class Incident(BaseComponent):
    """
    Represents an incident.

    Attributes
    ----------
    id : str
        The ID of the incident.
    name : str
        The name of the incident.
    status : str
        The current incident's status.
    created_at : datetime
        The time when this incident was created.
    updated_at : datetime
        The last time this incident was updated.
    impact : str
        The impact of this incident.
    updates : List[Update]
        A list of updates this incident has.
    """
    def __init__(self, inc_data: dict):
        super().__init__(inc_data)
        self.impact: str = inc_data["impact"]
        self.updates: List[Update] = [Update(u) for u in inc_data["incident_updates"]]


class ScheduledMaintenance(BaseComponent):
    """
    Represents a scheduled maintenance.

    Attributes
    ----------
    id : str
        The ID of the scheduled maintenance.
    name : str
        The name of the scheduled maintenance.
    status : str
        The current scheduled maintenance's status.
    created_at : datetime
        The time when this scheduled maintenance was created.
    updated_at : datetime
        The last time this scheduled maintenance was updated.
    impact : str
        The impact of this scheduled maintenance.
    scheduled_for : datetime
        The planned time this maintenance is scheduled to start.
    scheduled_until : datetime
        The planned time this maintenance is scheduled to end.
    updates : List[Update]
        A list of updates this scheduled maintenance has.
    """
    def __init__(self, main_data: dict):
        super().__init__(main_data)
        self.impact: str = main_data["impact"]
        self.scheduled_for = convert_timestamp(main_data["scheduled_for"])
        self.scheduled_until = convert_timestamp(main_data["scheduled_until"])
        self.updates: List[Update] = [Update(u) for u in main_data["incident_updates"]]


class Component(BaseComponent):
    """
    Represents a status component.

    Attributes
    ----------
    id : str
        The ID of the component.
    name : str
        The name of the component.
    status : str
        The current component's status.
    created_at : datetime
        The time when this component was created.
    updated_at : datetime
        The last time this component was updated.
    group : ComponentGroup
        The group this component belongs to.
    incidents : List[Incident]
        A list of incidents referring to this component.
    scheduled_maintenances : List[ScheduledMaintenance]
        A list of scheduled maintenances referring to this component.
    """
    def __init__(self, group: 'ComponentGroup', comp_data: dict):
        super().__init__(comp_data)
        self.group = group
        self.incidents: List[Incident] = []
        self.scheduled_maintenances: List[ScheduledMaintenance] = []

    def _add_incident(self, incident: Incident):
        self.incidents.append(incident)
        if self.group:
            self.group._add_incident(incident)

    def _add_scheduled_mainenance(self, scheduled_maintenance: ScheduledMaintenance):
        self.scheduled_maintenances.append(scheduled_maintenance)
        if self.group:
            self.group._add_scheduled_mainenance(scheduled_maintenance)


class ComponentGroup(BaseComponent):
    """
    Represents a component's group.

    Attributes
    ----------
    id : str
        The ID of the component group.
    name : str
        The name of the component group.
    status : str
        The current component group's status.
    created_at : datetime
        The time when this component group was created.
    updated_at : datetime
        The last time this component group was updated.
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
        self.incidents: List[Incident] = []
        self.scheduled_maintenances: List[ScheduledMaintenance] = []

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
    url : str
        The URL of the status page.
    timezone : str
        The timezone of the status page.
    updated_at : datetime
        The timestamp of when the current status was updated last.
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
        page = page_data["page"]
        self.name = page["name"]
        self.id = page["id"]
        self.url = page["url"]
        self.timezone = page["time_zone"]
        self.updated_at = convert_timestamp(page["updated_at"])

        groups = {c["id"]: ComponentGroup(c) for c in page_data["components"] if c["group"]}
        self.components = []
        for c in page_data["components"]:
            if c["group"]:
                continue
            group = groups[c["group_id"]]
            comp = Component(group, c)
            group._add_component(comp)
            self.components.append(comp)
        self.groups = list(groups.values())

        components_mapping = {c.id: c for c in self.components}

        self.incidents = []
        self.scheduled_maintenances = []
        for incident_data in page_data["incidents"]:
            i = Incident(incident_data)
            self.incidents.append(i)
            for comp_data in incident_data["components"]:
                comp = components_mapping.get(comp_data["id"])
                if comp:
                    comp._add_incident(i)
        for sm_data in page_data["scheduled_maintenances"]:
            sm = ScheduledMaintenance(sm_data)
            self.scheduled_maintenances.append(sm)
            for comp_data in sm_data["components"]:
                comp = components_mapping.get(comp_data["id"])
                if comp:
                    comp._add_scheduled_mainenance(sm)


class StatusPage:
    def __init__(self, url: str):
        self.url = "{}/api/v2".format(url.rstrip('/'))
        self._session = aiohttp.ClientSession(raise_for_status=True)

    def __del__(self):
        self._session.detach()

    async def close(self):
        await self._session.close()

    # async with integration
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        await self._session.close()

    async def request(self, endpoint: str):
        route = "{}/{}".format(self.url, endpoint)
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
