from yt_auto.tts import spoken


def test_units_are_spoken_in_full():
    assert spoken("114 TH at 14.92 W/TH") == "114 terahash at 14.92 watts per terahash"
    assert spoken("up to 25 TH.") == "up to 25 terahash."
    assert spoken("1 TH/s and 15 J/TH") == "1 terahash per second and 15 joules per terahash"
    assert spoken("a 500 W heater") == "a 500 watts heater"
    assert spoken("Watch the path") == "Watch the path"
