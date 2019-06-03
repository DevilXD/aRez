import aiohttp
import asyncio
from datetime import datetime, timezone

def convert_timestamp(stamp: str):
    return datetime.strptime(stamp[:-3] + stamp[-2:], "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(timezone.utc).replace(tzinfo=None).replace(microsecond=0)

class BaseComponent:
    def __init__(self, comp_data: dict):
        self.id = comp_data["id"]
        self.name = comp_data["name"]
        self.status = comp_data["status"]
        self.created_at = convert_timestamp(comp_data["created_at"])
        self.updated_at = convert_timestamp(comp_data["updated_at"])
    
    def __repr__(self) -> str:
        return "{0.__class__.__name__}: {0.name}".format(self)

class Component(BaseComponent):
    def __init__(self, group: 'ComponentGroup', comp_data: dict):
        super().__init__(comp_data)
        self.group = group

class ComponentGroup(BaseComponent):
    def __init__(self, group_data: dict):
        super().__init__(group_data)
        self.components = []
    
    def _add_component(self, comp: Component):
        self.components.append(comp)

class Update:
    def __init__(self, upd_data: dict):
        self.id = upd_data["id"]
        self.description = upd_data["body"]
        self.status = upd_data["status"]
        self.created_at = convert_timestamp(upd_data["created_at"])
        self.updated_at = convert_timestamp(upd_data["updated_at"])
    
    def __repr__(self) -> str:
        return "{}: {}".format(self.status.replace('_', ' ').title(), self.description)

class Incident(BaseComponent):
    def __init__(self, inc_data: dict):
        super().__init__(inc_data)
        self.impact = inc_data["impact"]
        self.updates = [Update(u) for u in inc_data["incident_updates"]]

class ScheduledMaintenance(BaseComponent):
    def __init__(self, main_data: dict):
        super().__init__(main_data)
        self.impact = main_data["impact"]
        self.scheduled_for = convert_timestamp(main_data["scheduled_for"])
        self.scheduled_until = convert_timestamp(main_data["scheduled_until"])
        self.updates = [Update(u) for u in main_data["incident_updates"]]

class Status:

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
        
        self.incidents = [Incident(i) for i in page_data["incidents"]]
        self.scheduled_maintenances = [ScheduledMaintenance(s) for s in page_data["scheduled_maintenances"]]

class StatusPage:
    def __init__(self, url: str):
        self.url = "{}/api/v2/summary.json".format(url.rstrip('/'))
        self._http_session = aiohttp.ClientSession(raise_for_status=True)
    
    def __del__(self):
        self._http_session.detach()
    
    async def close(self):
        await self._http_session.close()
    
    # async with integration
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc, traceback):
        await self._http_session.close()
    
    async def request(self):
        async with self._http_session.get(self.url) as response:
            return await response.json()
    
    async def get_status(self):
        response = await self.request()
        return Status(response)
