from __future__ import annotations

import json

import pytest

from gluetun_rotate.servers import locations
from gluetun_rotate.web import ApiError, Response

LIST = {
    "version": 4,
    "timestamp": 1785990877,
    "servers": [
        {"vpn": "openvpn", "country": "Germany", "hostname": "de-fra.example"},
        {"vpn": "openvpn", "country": "albania", "hostname": "al-tia.example"},
        {"vpn": "openvpn", "country": "Germany", "hostname": "de-ber.example"},
        {"vpn": "wireguard", "country": "Japan", "hostname": "jp-tok.example"},
        {"vpn": "openvpn", "hostname": "nowhere.example"},
    ],
}


def serving(body: object, status: int = 200):
    asked = []

    def fetcher(url: str, timeout: float = 0.0) -> Response:
        asked.append(url)
        return Response(status=status, body=json.dumps(body).encode())

    return fetcher, asked


def test_the_countries_are_unique_sorted_and_of_the_vpn_type_in_use():
    fetcher, _ = serving(LIST)
    assert locations("surfshark", "openvpn", fetcher) == ("countries", ["albania", "Germany"])


def test_no_vpn_type_keeps_every_country():
    fetcher, _ = serving(LIST)
    assert locations("surfshark", "", fetcher) == ("countries", ["albania", "Germany", "Japan"])


def test_a_provider_name_with_spaces_is_quoted_in_the_url():
    fetcher, asked = serving(LIST)
    locations("private internet access", "openvpn", fetcher)
    assert asked == [
        "https://raw.githubusercontent.com/qdm12/gluetun-servers/main/pkg/servers/"
        "private%20internet%20access.json"
    ]


def test_a_missing_list_says_which_provider():
    fetcher, _ = serving({}, status=404)
    with pytest.raises(ApiError, match="nordvpn returned 404"):
        locations("nordvpn", "openvpn", fetcher)


def test_a_provider_without_countries_falls_back_to_regions():
    fetcher, _ = serving(
        {"servers": [{"vpn": "openvpn", "region": "DE Frankfurt", "server_name": "frankfurt402"}]}
    )
    assert locations("private internet access", "openvpn", fetcher) == (
        "regions",
        ["DE Frankfurt"],
    )
