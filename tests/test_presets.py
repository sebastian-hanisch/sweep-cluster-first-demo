"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; die Zahlen in den Hilfetexten stehen in test_claims.py."""

import swp_constants as C
import swp_evaluation as ev
import swp_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            assert spec.lo <= preset[key] <= spec.hi, (name, key)
        assert (preset["fill"] - C.FILL_MIN) % C.FILL_STEP == 0, name              # Auslastung liegt auf dem Raster des Reglers


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**next(iter(C.PRESETS.values()))) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_every_preset_has_a_distinct_configuration():
    assert len({tuple(sorted(p.items())) for p in C.PRESETS.values()}) == len(C.PRESETS)


def test_the_band_utilizations_lie_inside_the_slider_range_and_n12_is_the_live_limit():
    assert all(C.FILL_MIN <= f <= C.FILL_MAX for fills in C.BAND_FILLS.values() for f in fills) and all(f in range(C.FILL_MIN, C.FILL_MAX + 1, 1) for f in C.SHORT_FILLS)
    assert max(C.BAND_SIZES) > C.N_MAX and C.N_MAX in C.BAND_SIZES and set(C.BAND_FILLS) == set(C.BAND_SIZES)  # n = 12 ist die Live-Grenze und eine Bandgröße
    assert set(C.EXACT_SIZES) <= set(C.BAND_SIZES) and max(C.EXACT_SIZES) == C.N_MAX
