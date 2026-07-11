"""Reject unsafe browser egress before an executor receives a task grant."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urlparse


class UnsafeBrowserEgress(ValueError):
    """The requested target is outside the approved public-host allowlist."""


Resolver = Callable[[str], list[str]]


def validate_browser_url(
    url: str, allowed_hosts: tuple[str, ...], resolver: Resolver | None = None
) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise UnsafeBrowserEgress("Browser navigation requires an HTTPS URL")
    host = parsed.hostname.lower().rstrip(".")
    if host not in {item.lower().rstrip(".") for item in allowed_hosts}:
        raise UnsafeBrowserEgress("Browser host is not allowlisted")
    lookup = resolver or _resolve
    for address in lookup(host):
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise UnsafeBrowserEgress("Browser target resolves to a non-public address")


def _resolve(host: str) -> list[str]:
    return list(
        {str(item[4][0]) for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    )
