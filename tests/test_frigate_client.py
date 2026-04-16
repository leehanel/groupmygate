from groupme_bot.frigate_client import FrigateClient


def test_get_clip_url_uses_review_route(monkeypatch) -> None:
    monkeypatch.setattr("groupme_bot.frigate_client.time.time", lambda: 100)
    client = FrigateClient(
        api_base_url="http://frigate:5000",
        frontend_base_url="http://frigate.example.com",
        camera="gate",
        clip_seconds=30,
        request_timeout=5,
    )

    assert client.get_clip_url() == (
        "http://frigate.example.com/review?cameras=gate&after=70&before=100&time_range=custom"
    )
