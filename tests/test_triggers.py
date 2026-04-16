from groupme_bot.handlers.triggers import HELP_TEXT, route_message


def test_help_trigger() -> None:
    reply, name, topic = route_message({"name": "Alex"}, "!help")
    assert reply == HELP_TEXT
    assert name == "help"
    assert topic is None


def test_ping_trigger() -> None:
    reply, name, topic = route_message({"name": "Alex"}, "!ping")
    assert reply == "pong"
    assert name == "ping"
    assert topic is None


def test_greeting_trigger() -> None:
    reply, name, topic = route_message({"name": "Alex"}, "hello everyone")
    assert reply == "Hey Alex!"
    assert name == "greeting"
    assert topic is None


def test_non_matching_text() -> None:
    reply, name, topic = route_message({"name": "Alex"}, "nothing to see")
    assert reply is None
    assert name is None
    assert topic is None


def test_roll_default() -> None:
    reply, name, topic = route_message({}, "!roll")
    assert name == "roll"
    assert topic is None
    assert reply.startswith("\U0001f3b2 Rolled a d6:")
    result = int(reply.split(": ")[1])
    assert 1 <= result <= 6


def test_roll_custom_sides() -> None:
    reply, name, _topic = route_message({}, "!roll 20")
    assert name == "roll"
    result = int(reply.split(": ")[1])
    assert 1 <= result <= 20


def test_8ball() -> None:
    reply, name, _topic = route_message({}, "!8ball Will it work?")
    assert name == "8ball"
    assert "\U0001f3b1" in reply
    assert "Will it work?" in reply


def test_choose() -> None:
    reply, name, _topic = route_message({}, "!choose pizza or tacos")
    assert name == "choose"
    assert reply in ("I choose: pizza", "I choose: tacos")


def test_say() -> None:
    reply, name, _topic = route_message({}, "!say hello world")
    assert name == "say"
    assert reply == "hello world"


def test_uptime() -> None:
    reply, name, _topic = route_message({}, "!uptime")
    assert name == "uptime"
    assert "\u23f1 Uptime:" in reply


def test_gate_open_trigger() -> None:
    from groupme_bot.handlers.triggers import configure_gate_topic

    configure_gate_topic("/test/gate/open")
    reply, name, topic = route_message({"name": "Alex"}, "!gate open")
    assert name == "gate_open"
    assert topic == "/test/gate/open"
    assert "Alex" in reply
    configure_gate_topic("/home-commands/gate/open")


def test_gate_video_trigger() -> None:
    reply, name, topic = route_message({"name": "Alex"}, "!gate video")
    assert name == "gate_video"
    assert topic is None
    assert "latest gate clip" in reply.lower()
