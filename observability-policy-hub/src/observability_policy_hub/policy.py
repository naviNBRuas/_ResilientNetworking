from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class PolicyDecision:
    """
    Represents the result of a policy evaluation.
    """
    allow: bool
    reason: str = ""


class PolicyEngine:
    """
    Evaluates a set of registered rules against a given context.
    """

    def __init__(self, fail_open: bool = False):
        """
        Initialize the PolicyEngine.

        Args:
            fail_open (bool): If True, rule execution errors will result in an allowed decision (logged as error).
                              If False, errors will result in a denial. Defaults to False.
        """
        self.rules: Dict[str, Callable[[Dict[str, Any]], PolicyDecision]] = {}
        self.fail_open = fail_open

    def register_rule(self, name: str, rule: Callable[[Dict[str, Any]], PolicyDecision]) -> None:
        """
        Register a new policy rule.

        Args:
            name (str): Unique name for the rule.
            rule (Callable): A function that takes a context dict and returns a PolicyDecision.
        """
        self.rules[name] = rule
        logger.debug(f"Registered rule: {name}")

    def evaluate(self, context: Dict[str, Any]) -> PolicyDecision:
        """
        Evaluate all registered rules against the context.

        Args:
            context (Dict[str, Any]): The context data to evaluate.

        Returns:
            PolicyDecision: The final decision. First rule to deny blocks the request.
        """
        for name, rule in self.rules.items():
            try:
                decision = rule(context)
                if not decision.allow:
                    logger.info(f"Policy denied by rule '{name}': {decision.reason}")
                    return PolicyDecision(allow=False, reason=f"{name}:{decision.reason}")
            except Exception as e:
                logger.error(f"Error evaluating rule '{name}': {e}", exc_info=True)
                if not self.fail_open:
                    return PolicyDecision(allow=False, reason=f"error-in-rule:{name}")
                # If fail_open is True, we log and continue to the next rule (or implicitly allow if all pass)

        return PolicyDecision(allow=True, reason="all-allow")