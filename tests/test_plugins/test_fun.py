from Yami.plugins.fun import get_video_id


def test_get_video_id_returns_id_from_id():
    assert get_video_id("U9-92lTEHyM") == "U9-92lTEHyM"


def test_get_video_id_returns_id_from_url():
    assert (
        get_video_id(
            "https://music.youtube.com/watch?v=U9-92lTEHyM&list=RDAMVMU9-92lTEHyM"
        )
        == "U9-92lTEHyM"
    )
