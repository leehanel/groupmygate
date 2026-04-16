import pytest

from groupme_bot.app import app, build_startup_announcement, process_groupme_message, validate_required_config
from groupme_bot.config import Config


def test_process_groupme_message_ignores_non_text(monkeypatch) -> None:
    called = {"send": 0}

    monkeypatch.setattr("groupme_bot.app.client.send_message", lambda _text: called.__setitem__("send", 1))
    process_groupme_message({"name": "Alex", "sender_type": "user"})

    assert called["send"] == 0


def test_process_groupme_message_sends_reply_and_mqtt(monkeypatch) -> None:
    sent = {"messages": [], "topic": ""}
    sent_videos: list[str] = []

    monkeypatch.setattr("groupme_bot.app.client.send_message", lambda text: sent["messages"].append(text))
    monkeypatch.setattr("groupme_bot.app.client.send_image_message", lambda _text, _bytes, _type: None)
    monkeypatch.setattr("groupme_bot.app.client.send_video_link_message", lambda _text, url: sent_videos.append(url))
    monkeypatch.setattr("groupme_bot.app.mqtt.publish", lambda topic: sent.__setitem__("topic", topic))
    monkeypatch.setattr("groupme_bot.app.frigate.get_snapshot", lambda: None)
    monkeypatch.setattr("groupme_bot.app.frigate.get_clip_url", lambda: "http://frigate.local/review?cameras=gate")

    process_groupme_message(
        {
            "text": "!gate open",
            "name": "Alex",
            "sender_id": "another-user",
            "sender_type": "user",
        }
    )

    assert any("Opening gate" in msg for msg in sent["messages"])
    assert sent["topic"] == "/home-commands/gate/open"
    assert sent_videos == ["http://frigate.local/review?cameras=gate"]


def test_process_groupme_message_posts_frigate_snapshot_for_gate(monkeypatch) -> None:
    sent_messages: list[str] = []
    sent_images: list[str] = []
    sent_videos: list[str] = []

    monkeypatch.setattr("groupme_bot.app.client.send_message", lambda text: sent_messages.append(text))
    monkeypatch.setattr("groupme_bot.app.client.send_image_message", lambda text, _bytes, _type: sent_images.append(text))
    monkeypatch.setattr("groupme_bot.app.client.send_video_link_message", lambda _text, url: sent_videos.append(url))
    monkeypatch.setattr("groupme_bot.app.mqtt.publish", lambda _topic: None)
    monkeypatch.setattr(
        "groupme_bot.app.frigate.get_snapshot",
        lambda: (b"fake-image", "image/jpeg"),
    )
    monkeypatch.setattr("groupme_bot.app.frigate.get_clip_url", lambda: "http://frigate.local/review?cameras=gate")

    process_groupme_message(
        {
            "text": "!gate open",
            "name": "Alex",
            "sender_id": "another-user",
            "sender_type": "user",
        }
    )

    assert len(sent_messages) == 1
    assert "Opening gate" in sent_messages[0]
    assert sent_images == ["Gate snapshot"]
    assert sent_videos == ["http://frigate.local/review?cameras=gate"]


def test_process_groupme_message_posts_frigate_video_and_snapshot(monkeypatch) -> None:
    sent_messages: list[str] = []
    sent_images: list[str] = []
    sent_videos: list[str] = []

    monkeypatch.setattr("groupme_bot.app.client.send_message", lambda text: sent_messages.append(text))
    monkeypatch.setattr("groupme_bot.app.client.send_image_message", lambda text, _bytes, _type: sent_images.append(text))
    monkeypatch.setattr("groupme_bot.app.client.send_video_link_message", lambda _text, url: sent_videos.append(url))
    monkeypatch.setattr("groupme_bot.app.frigate.get_snapshot", lambda: (b"fake-image", "image/jpeg"))
    monkeypatch.setattr("groupme_bot.app.frigate.get_clip_url", lambda: "http://frigate.local/review?cameras=gate")

    process_groupme_message(
        {
            "text": "!gate video",
            "name": "Alex",
            "sender_id": "another-user",
            "sender_type": "user",
        }
    )

    assert any("Fetching the latest gate clip" in msg for msg in sent_messages)
    assert sent_images == ["Gate snapshot"]
    assert sent_videos == ["http://frigate.local/review?cameras=gate"]


def test_groupme_webhook_returns_200(monkeypatch) -> None:
    sent = {"messages": [], "topic": ""}

    monkeypatch.setattr("groupme_bot.app.client.send_message", lambda text: sent["messages"].append(text))
    monkeypatch.setattr("groupme_bot.app.client.send_image_message", lambda _text, _bytes, _type: None)
    monkeypatch.setattr("groupme_bot.app.client.send_video_link_message", lambda _text, _url: None)
    monkeypatch.setattr("groupme_bot.app.mqtt.publish", lambda topic: sent.__setitem__("topic", topic))
    monkeypatch.setattr("groupme_bot.app.frigate.get_snapshot", lambda: None)
    monkeypatch.setattr("groupme_bot.app.frigate.get_clip_url", lambda: None)

    response = app.test_client().post(
        "/groupme/webhook",
        json={"text": "!gate open", "name": "Alex", "sender_type": "user"},
    )

    assert response.status_code == 200
    assert sent["topic"] == "/home-commands/gate/open"


def test_validate_required_config_raises_for_missing_values(monkeypatch) -> None:
    bad_cfg = Config(
        port=3000,
        groupme_bot_id="",
        groupme_access_token="",
        mqtt_broker="localhost",
        mqtt_port=1883,
        mqtt_username="",
        mqtt_password="",
        gate_mqtt_topic="",
        frigate_api_base_url="",
        frigate_frontend_base_url="",
        frigate_camera="",
        frigate_clip_seconds=30,
        frigate_request_timeout=5,
    )
    monkeypatch.setattr("groupme_bot.app.cfg", bad_cfg)

    with pytest.raises(ValueError, match="GROUPME_BOT_ID"):
        validate_required_config()


def test_build_startup_announcement_lists_commands() -> None:
    message = build_startup_announcement()

    assert message.startswith("GroupMyGate is listening.")
    assert "!gate" in message
    assert "!help" in message
