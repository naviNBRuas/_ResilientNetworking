from __future__ import annotations

import logging
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class ServiceEndpoint:
    """Represents a single instance of a service."""
    address: str
    metadata: dict[str, str] = field(default_factory=dict)
    healthy: bool = True
    last_checked: float = field(default_factory=time.time)
    ttl: float = 0.0  # 0.0 means no expiration


class ServiceRegistry:
    """
    Thread-safe registry for managing service endpoints and their health status.
    """

    def __init__(self) -> None:
        self._services: dict[str, list[ServiceEndpoint]] = {}
        self._lock = threading.RLock()

    def register(self, name: str, endpoint: ServiceEndpoint) -> None:
        """
        Register a new service endpoint.

        Args:
            name: The name of the service.
            endpoint: The ServiceEndpoint instance to register.
        """
        with self._lock:
            endpoints = self._services.setdefault(name, [])
            # Prevent duplicate registration by address
            for ep in endpoints:
                if ep.address == endpoint.address:
                    logger.warning(
                        "Endpoint %s already registered for service %s. Skipping.",
                        endpoint.address,
                        name,
                    )
                    return
            endpoints.append(endpoint)
            logger.info("Registered endpoint %s for service %s", endpoint.address, name)

    def unregister(self, name: str, address: str) -> bool:
        """
        Remove a service endpoint from the registry.

        Args:
            name: The name of the service.
            address: The address of the endpoint to remove.

        Returns:
            True if the endpoint was found and removed, False otherwise.
        """
        with self._lock:
            if name not in self._services:
                return False

            original_count = len(self._services[name])
            self._services[name] = [
                ep for ep in self._services[name] if ep.address != address
            ]
            
            # Clean up empty service keys
            if not self._services[name]:
                del self._services[name]

            if len(self._services.get(name, [])) < original_count:
                logger.info("Unregistered endpoint %s for service %s", address, name)
                return True
            return False

    def prune(self, name: Optional[str] = None) -> int:
        """
        Remove expired endpoints from the registry.

        Args:
            name: Optional service name to prune. If None, prunes all services.

        Returns:
            The number of endpoints removed.
        """
        now = time.time()
        removed_count = 0
        with self._lock:
            services_to_check = [name] if name else list(self._services.keys())

            for svc_name in services_to_check:
                if svc_name not in self._services:
                    continue

                endpoints = self._services[svc_name]
                valid_endpoints = []
                for ep in endpoints:
                    if ep.ttl > 0 and (now - ep.last_checked) > ep.ttl:
                        logger.info(
                            "Pruning expired endpoint %s for service %s",
                            ep.address,
                            svc_name,
                        )
                        removed_count += 1
                        continue
                    valid_endpoints.append(ep)

                if not valid_endpoints:
                    del self._services[svc_name]
                else:
                    self._services[svc_name] = valid_endpoints

        return removed_count

    def resolve(
        self, name: str, filter_metadata: Optional[dict[str, str]] = None
    ) -> list[ServiceEndpoint]:
        """
        Get all healthy endpoints for a service.

        Args:
            name: The name of the service.
            filter_metadata: Optional dictionary of metadata key-value pairs to match.

        Returns:
            A list of healthy ServiceEndpoint objects.
        """
        now = time.time()
        with self._lock:
            candidates = self._services.get(name, [])
            results = []
            for ep in candidates:
                # Check health
                if not ep.healthy:
                    continue

                # Check TTL
                if ep.ttl > 0 and (now - ep.last_checked) > ep.ttl:
                    continue

                # Check metadata
                if filter_metadata:
                    match = True
                    for k, v in filter_metadata.items():
                        if ep.metadata.get(k) != v:
                            match = False
                            break
                    if not match:
                        continue

                results.append(ep)
            return results

    def get_service_names(self) -> list[str]:
        """Return a list of all registered service names."""
        with self._lock:
            return list(self._services.keys())

    def active_check(self, name: str, checker: Callable[[ServiceEndpoint], bool]) -> None:
        """
        Perform an active health check on all endpoints of a service.

        Args:
            name: The name of the service.
            checker: A function that takes an endpoint and returns True if healthy.
        """
        with self._lock:
            endpoints = self._services.get(name, [])
            for ep in endpoints:
                try:
                    is_healthy = checker(ep)
                    if ep.healthy != is_healthy:
                        logger.info(
                            "Health status changed for %s/%s: %s -> %s",
                            name,
                            ep.address,
                            ep.healthy,
                            is_healthy,
                        )
                    ep.healthy = is_healthy
                except Exception as e:
                    logger.error(
                        "Error checking health for %s/%s: %s", name, ep.address, e
                    )
                    ep.healthy = False
                finally:
                    ep.last_checked = time.time()

    def passive_mark(self, name: str, address: str, success: bool) -> None:
        """
        Update the health status of an endpoint based on external observation.

        Args:
            name: The name of the service.
            address: The address of the endpoint.
            success: True if the interaction was successful, False otherwise.
        """
        with self._lock:
            for ep in self._services.get(name, []):
                if ep.address == address:
                    if ep.healthy != success:
                        logger.info(
                            "Passive health update for %s/%s: %s -> %s",
                            name,
                            address,
                            ep.healthy,
                            success,
                        )
                    ep.healthy = success
                    ep.last_checked = time.time()
                    return
            logger.debug("Attempted passive mark for unknown endpoint %s/%s", name, address)

    def random_endpoint(self, name: str) -> Optional[ServiceEndpoint]:
        """
        Get a random healthy endpoint for a service.

        Args:
            name: The name of the service.

        Returns:
            A ServiceEndpoint or None if no healthy endpoints are available.
        """
        # resolve() already acquires the lock
        healthy = self.resolve(name)
        if not healthy:
            return None
        return random.choice(healthy)
