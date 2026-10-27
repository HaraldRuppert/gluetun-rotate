from __future__ import annotations

import json
import urllib.parse
from collections.abc import Callable

from .constants import SERVERS_TIMEOUT_SECONDS, SERVERS_URL
from .web import ApiError, Response, fetch

# Gluetun's server selection, and the server field it filters on. Private Internet Access,
# Windscribe, VyprVPN and Giganews list regions only.
LOCATIONS = (("countries", "country"), ("regions", "region"))


def locations(
    provider: str, vpn_type: str, fetcher: Callable[..., Response] = fetch
) -> tuple[str, list[str]]:
    url = SERVERS_URL.format(provider=urllib.parse.quote(provider))
    response = fetcher(url, timeout=SERVERS_TIMEOUT_SECONDS)
    if response.status != 200:
        raise ApiError(f"the server list for {provider} returned {response.status}")
    try:
        loaded = json.loads(response.body)
    except ValueError as error:
        raise ApiError(f"the server list for {provider} is not JSON") from error
    listed = loaded.get("servers") if isinstance(loaded, dict) else None
    servers = [
        server
        for server in listed or []
        if isinstance(server, dict) and (not vpn_type or server.get("vpn") == vpn_type)
    ]
    for selection, key in LOCATIONS:
        found = {str(server[key]).strip() for server in servers if server.get(key)}
        if found:
            return selection, sorted(found, key=str.casefold)
    return LOCATIONS[0][0], []
