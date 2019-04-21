import re
from typing import Union

from telegrambot.errors import RuleError
from telegrambot.types import MessageType


class Rule:
    pass


# TODO: добавить And и Or


class RegExp(Rule):
    priority = 300

    def __init__(self, pattern: str):
        self._pattern = re.compile(pattern)

    def __eq__(self, other: Union[str, Rule]):
        if isinstance(other, Rule):
            return self.__hash__() == hash(other)
        return bool(self._pattern.match(other))

    def __hash__(self):
        return hash(self._pattern)


class Text(Rule):
    priority = 200

    def __init__(self, text: str, to_lower: bool = True):
        self._text = text.lower() if to_lower else text
        self._to_lower = to_lower

    def __eq__(self, other: Union[str, Rule]):
        if isinstance(other, Rule):
            return self.__hash__() == hash(other)
        return self._text == (other.lower() if self._to_lower else other)

    def __hash__(self):
        return hash((self.__class__, self._text, self._to_lower))


class Contains(Text):

    def __eq__(self, other: Union[str, Rule]):
        if isinstance(other, Rule):
            return self.__hash__() == hash(other)
        return self._text in (other.lower() if self._to_lower else other)

    def __hash__(self):
        return super().__hash__()


class Pattern(Text):
    priority = 100
    pattern = None

    def __init__(self, text: str, to_lower: bool = False):
        if not self.pattern.match(text):
            raise RuleError(
                f"The {self.__class__.__name__.lower()} should corresponds '{self.pattern.pattern}' pattern"
            )
        super().__init__(text, to_lower)


class Command(Pattern):
    pattern = re.compile(r"^/[A-Za-z0-9_]+$")


class Mention(Pattern):
    pattern = re.compile(r"^@[A-Za-z0-9_]+$")


RuleType = Union[Rule, str, int]


def prepare_rule(message_type: MessageType, rule: RuleType) -> RuleType:
    if message_type == MessageType.COMMAND and isinstance(rule, str):
        return Command(rule)
    elif message_type == MessageType.MENTION and isinstance(rule, str):
        return Mention(rule)
    elif message_type == MessageType.TEXT and isinstance(rule, (str, int)):
        return Text(str(rule))
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
