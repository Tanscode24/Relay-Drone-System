"""
routing_manager.py

Decides where a decoded MAVLink message should be forwarded.

Rules, in priority order:

  1. Never forward a message back out the link it arrived on.
  2. If the message carries a `target_system` field and that system id
     is known (learned via DroneManager from HEARTBEAT traffic), forward
     ONLY to the link that system lives on. This avoids unnecessary
     rebroadcast and is what lets the design scale to multiple relay /
     main drones without an explosion of duplicate traffic.
  3. Otherwise (broadcast-style messages: HEARTBEAT, telemetry streams,
     STATUSTEXT, etc.) forward to every other link. In the current 3-link
     star topology (ground / own Pixhawk / remote Pixhawk) "every other
     link" is exactly correct. See README.md ("Scaling to multiple
     drones") for how to scope this further on a multi-relay mesh.
"""


class RoutingManager:
    def __init__(self, links, drone_manager):
        self._links = {link.name: link for link in links}
        self._drones = drone_manager

    def destinations_for(self, source_link, msg):
        target_system = getattr(msg, "target_system", None)

        if target_system:
            dest_link_name = self._drones.link_for_system(target_system)
            if dest_link_name and dest_link_name != source_link.name:
                return [self._links[dest_link_name]]

        return [
            link for name, link in self._links.items()
            if name != source_link.name
        ]
