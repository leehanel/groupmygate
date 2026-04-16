from __future__ import annotations

import logging
import random
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

_START_TIME = time.time()
logger = logging.getLogger(__name__)

Message = dict
MatchFn = Callable[[str, Message], bool]
ReplyFn = Callable[[Message, str], str]


@dataclass(frozen=True)
class Trigger:
    name: str
    matches: MatchFn
    reply: ReplyFn
    mqtt_topic: Optional[str] = field(default=None)


HELP_TEXT = "Commands: !help, !ping, !joke, !roll [sides], !8ball <question>, !choose <a> or <b>, !say <text>, !uptime, !gate open, !gate video"


TRIGGERS: list[Trigger] = [
    Trigger(
        name="help",
        matches=lambda text, _msg: text.strip().lower() == "!help",
        reply=lambda _msg, _text: HELP_TEXT,
    ),
    Trigger(
        name="ping",
        matches=lambda text, _msg: text.strip().lower() == "!ping",
        reply=lambda _msg, _text: "pong",
    ),
    Trigger(
        name="say",
        matches=lambda text, _msg: text.strip().lower().startswith("!say "),
        reply=lambda _msg, text: text.strip()[5:],
    ),
    Trigger(
        name="greeting",
        matches=lambda text, _msg: bool(re.search(r"\b(hi|hello|hey)\b", text, re.IGNORECASE)),
        reply=lambda msg, _text: f"Hey {msg.get('name', 'there')}!",
    ),
    Trigger(
        name="joke",
        matches=lambda text, _msg: text.strip().lower() == "!joke",
        reply=lambda _msg, _text: random.choice(
            [
                "Why do programmers prefer dark mode? Because light attracts bugs.",
                "I would tell you a UDP joke, but you might not get it.",
                "There are 10 kinds of people: those who understand binary and those who do not.",
            ]
        ),
    ),
    Trigger(
        name="roll",
        matches=lambda text, _msg: re.match(r"^!roll(\s+\d+)?$", text.strip(), re.IGNORECASE) is not None,
        reply=lambda msg, text: _reply_roll(msg, text),
    ),
    Trigger(
        name="8ball",
        matches=lambda text, _msg: text.strip().lower().startswith("!8ball "),
        reply=lambda msg, text: _reply_8ball(msg, text),
    ),
    Trigger(
        name="choose",
        matches=lambda text, _msg: re.search(r"^!choose .+ or .+", text.strip(), re.IGNORECASE) is not None,
        reply=lambda _msg, text: _reply_choose(text),
    ),
    Trigger(
        name="uptime",
        matches=lambda text, _msg: text.strip().lower() == "!uptime",
        reply=lambda _msg, _text: _reply_uptime(),
    ),
    Trigger(
        name="gate_open",
        matches=lambda text, _msg: text.strip().lower() == "!gate open",
        reply=lambda msg, _text: f"Opening gate for {msg.get('name', 'someone')}...",
        mqtt_topic=None,  # overridden at startup via configure_gate_topic()
    ),
    Trigger(
        name="gate_video",
        matches=lambda text, _msg: text.strip().lower() == "!gate video",
        reply=lambda _msg, _text: "Fetching the latest gate clip and snapshot...",
    ),
    Trigger(
        name="gate_help",
        matches=lambda text, _msg: text.strip().lower() == "!gate",
        reply=lambda _msg, _text: "Use '!gate open' or '!gate video'.",
    ),
]


_8BALL_RESPONSES = [
    "It is certain.", "Without a doubt.", "Yes, definitely.", "You may rely on it.",
    "As I see it, yes.", "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
    "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
    "Cannot predict now.", "Concentrate and ask again.",
    "Don't count on it.", "My reply is no.", "My sources say no.",
    "Outlook not so good.", "Very doubtful.",
]


def _reply_roll(_msg: Message, text: str) -> str:
    parts = text.strip().split()
    sides = int(parts[1]) if len(parts) == 2 else 6
    if sides < 2:
        return "Please roll at least a 2-sided die."
    result = random.randint(1, sides)
    return f"🎲 Rolled a d{sides}: {result}"


def _reply_8ball(_msg: Message, text: str) -> str:
    question = text.strip()[7:].strip()
    answer = random.choice(_8BALL_RESPONSES)
    return f"🎱 {question!r} → {answer}"


def _reply_choose(text: str) -> str:
    # strip "!choose " prefix then split on " or "
    body = re.sub(r"^!choose\s+", "", text.strip(), flags=re.IGNORECASE)
    options = re.split(r"\s+or\s+", body, flags=re.IGNORECASE)
    return f"I choose: {random.choice(options).strip()}"


def _reply_uptime() -> str:
    seconds = int(time.time() - _START_TIME)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"⏱ Uptime: {hours}h {minutes}m {secs}s"



def route_message(message: Message, text: str) -> tuple[str, str, Optional[str]] | tuple[None, None, None]:
    """Return (reply_text, trigger_name, mqtt_topic) or (None, None, None) if no trigger matched."""
    for trigger in TRIGGERS:
        if trigger.matches(text, message):
            reply = trigger.reply(message, text)
            logger.info(
                "Matched trigger name=%s sender=%r mqtt_topic=%r text=%r",
                trigger.name,
                message.get("name"),
                trigger.mqtt_topic,
                text,
            )
            return reply, trigger.name, trigger.mqtt_topic
    logger.info("No trigger matched sender=%r text=%r", message.get("name"), text)
    return None, None, None


def configure_gate_topic(topic: str) -> None:
    """Set the MQTT topic for the gate_open trigger at startup from config."""
    for i, trigger in enumerate(TRIGGERS):
        if trigger.name == "gate_open":
            TRIGGERS[i] = Trigger(
                name=trigger.name,
                matches=trigger.matches,
                reply=trigger.reply,
                mqtt_topic=topic,
            )
            logger.info("Configured gate MQTT topic=%r", topic)
            return
