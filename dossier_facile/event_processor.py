from django.db import transaction
from dossier_facile.rules import DossierFacileEventRule, RULES
import logging

logger = logging.getLogger(__name__)


class DossierFacileEventRuleDispatcher:
    def __init__(self, event: dict, rules: list[DossierFacileEventRule]):
        pass

    def dispatch(self):
        for rule in self.rules:
            if rule.matches(self.event):
                rule.handle(self.event)
                return True
        return False


class DossierFacileWebhookEventProcessor:
    def __init__(self, event: dict):
        self.event = event
        self.rules = []
        self._init_rules()
        self.dispatcher = DossierFacileEventRuleDispatcher(event, self.rules)

    def _init_rules(self):
        for rule in RULES:
            try:
                self.rules.append(rule(self.event))
            except Exception as e:
                logger.error("[DossierFacile] Error creating rule %s: %s", rule.__name__, e)
                logger.info(f"Event: {self.event}")
                continue

    @transaction.atomic
    def process_event(self, event):
        dispatcher = DossierFacileEventRuleDispatcher(event, self.rules)
        handled = dispatcher.dispatch()
        if not handled:
            logger.error("[DossierFacile] No rule matched for event: %s", event)
            return False
        return True
