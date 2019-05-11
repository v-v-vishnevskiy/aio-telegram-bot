class BotError(Exception):
    pass


class HandlerError(BotError):
    pass


class RuleError(BotError):
    pass
