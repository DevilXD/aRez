import arez
import pytest


pytestmark = [pytest.mark.vcr, pytest.mark.asyncio, pytest.mark.statuspage]


async def test_statuspage(sp: arez.StatusPage):
    status = await sp.get_status()
    assert isinstance(status, arez.statuspage.CurrentStatus)
    # repr
    repr(status)
    if status.incidents:
        incident = status.incidents[0]
        repr(incident)
        if incident.updates:
            repr(incident.updates[0])
        # property access
        incident.colour
    if status.maintenances:
        maintenance = status.maintenances[0]
        repr(maintenance)
        if maintenance.updates:
            repr(maintenance.updates[0])
        # property access
        maintenance.colour
    # test component and group getting methods
    status.component("Test")
    status.group("Test")
