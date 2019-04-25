import re
from typing import Optional, Union

from telegrambot.errors import RuleError
from telegrambot.types import Incoming, MessageType


class Rule:
    pass


# TODO: добавить And и Or


class RegExp(Rule):
    priority = 400

    def __init__(self, pattern: str):
        self._pattern = re.compile(pattern)

    def __eq__(self, other: Union[str, Rule]):
        if isinstance(other, Rule):
            return self.__hash__() == hash(other)
        return bool(self._pattern.match(other))

    def __hash__(self):
        return hash(self._pattern)

    def __repr__(self):
        return f'RegExp("{self._pattern.pattern}")'


class Text(Rule):
    priority = 200

    def __init__(self, text: str, insensitive: bool = True):
        self._text = text.lower() if insensitive else text
        self._insensitive = insensitive

    def __eq__(self, other: Union[str, Rule]):
        if isinstance(other, Rule):
            return self.__hash__() == hash(other)
        return self._text == (other.lower() if self._insensitive else other)

    def __hash__(self):
        return hash((self.__class__, self._text, self._insensitive))

    def __repr__(self):
        return f'{self.__class__.__name__}("{self._text}", {self._insensitive})'


class Contains(Text):
    priority = 300

    def __eq__(self, other: Union[str, Rule]):
        if isinstance(other, Rule):
            return self.__hash__() == hash(other)
        return self._text in (other.lower() if self._insensitive else other)

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


_RuleType = Union[Rule, str, int]


def _prepare_rule(message_type: Optional[MessageType], rule: _RuleType) -> _RuleType:
    if message_type == MessageType.COMMAND and isinstance(rule, str):
        return Command(rule)
    elif message_type == MessageType.MENTION and isinstance(rule, str):
        return Mention(rule)
    elif message_type == MessageType.TEXT and isinstance(rule, (str, int)):
        return Text(str(rule))
    return rule


def _is_match(rule: Optional[_RuleType], incoming: Incoming, message_type: MessageType, raw: dict) -> bool:
    if rule is None:
        return True
    elif incoming.is_message_or_post:
        raw = raw[incoming.value]
        if message_type.has_entity:
            key, entity_key, _ = message_type.value
            entity = raw[entity_key][0]
            offset = entity["offset"]
            length = entity["length"]
            value = raw[key][offset:length]
        else:
            key = message_type.value
            value = raw[key]
        return rule == value

    # TODO: check other incoming types
    return False
