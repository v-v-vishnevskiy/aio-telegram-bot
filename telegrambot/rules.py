import re
from typing import Union

from telegrambot.errors import RuleError
from telegrambot.types import MessageType


class Rule:
    pass


# TODO: добавить And и Or


class RegExp(Rule):
    def __init__(self, pattern: str):
        self._pattern = re.compile(pattern)

    def __eq__(self, other: Union[str, "RegExp"]):
        if isinstance(other, str):
            return bool(self._pattern.match(other))
        return self.__hash__() == hash(other)

    def __hash__(self):
        return hash(self._pattern)


class TextEntity(Rule):
    pattern = None

    def __init__(self, entity: str):
        if not self.pattern.match(entity):
            raise RuleError(
                f"The {self.__class__.__name__.lower()} should corresponds '{self.pattern.pattern}' pattern"
            )

        self._entity = entity

    def __eq__(self, other: str):
        return self._entity == other


class Command(TextEntity):
    pattern = re.compile(r"^/[A-Za-z0-9_]+$")


class Mention(TextEntity):
    pattern = re.compile(r"^@[A-Za-z0-9_]+$")


RuleType = Union[Rule, str, int]


def prepare_rule(message_type: MessageType, rule: RuleType) -> RuleType:
    if message_type == MessageType.COMMAND and isinstance(rule, str):
        return Command(rule)
    elif message_type == MessageType.MENTION and isinstance(rule, str):
        return Mention(rule)
    return rule


def is_match(rule: RuleType, message_type: MessageType, message: dict) -> bool:
    if isinstance(message_type.value, tuple):
        key, entity_key, _ = message_type.value
        entity = message[entity_key][0]
        offset = entity["offset"]
        length = entity["length"]
        value = message[key][offset:length]
    else:
        key = message_type.value
        value = message[key]
    return rule == value
