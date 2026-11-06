"""Gemeinsame Fixtures: die Handinstanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from swp_scenario import Instance  # noqa: E402

(S2, S18, S20, S29, S32, S37, S41, S45, S53, S72, S74, S148, S185) = (math.sqrt(v) for v in (2, 18, 20, 29, 32, 37, 41, 45, 53, 72, 74, 148, 185))


@pytest.fixture
def hand():
    """Planinstanz aus den Stücken 1 bis 4: Depot (0,0); Kunden 1 (6,-6), 2 (-2,5), 3 (-4,-4), 4 (0,-7), 5 (-1,-1), 6 (-6,3); Nachfragen 3, 2, 2, 4, 2, 1; Kapazität 7.

    Von Hand (Wurzeln): Optimum = Route (1 4) + Route (2 6 3 5) = (sqrt72 + sqrt37 + 7) + (sqrt29 + sqrt20 + sqrt53 + sqrt18 + sqrt2) = 44,3623; kürzeste Rundreise 38,2367."""
    return Instance(((0.0, 0.0), (6.0, -6.0), (-2.0, 5.0), (-4.0, -4.0), (0.0, -7.0), (-1.0, -1.0), (-6.0, 3.0)), (3, 2, 2, 4, 2, 1), 7)


@pytest.fixture
def corner():
    """Kleine Karte, n = 6, Depot in der Ecke (Generator `make_instance(6, 0, 1, 2, 13, 90)`): Depot (0,0); Kunden 1 (15,14), 2 (13,14), 3 (1,13), 4 (16,4), 5 (2,1), 6 (13,16); Nachfragen 3, 3, 4, 1, 4, 4; Kapazität 11.

    Winkel von Hand (atan2): 4: 14,04 Grad, 5: 26,57, 1: 43,03, 2: 47,12, 6: 50,91, 3: 85,60; Winkelfolge 4 5 1 2 6 3. Optimum 77,79 mit den Routen (2 6 1 4) und (3 5)."""
    return Instance(((0.0, 0.0), (15.0, 14.0), (13.0, 14.0), (1.0, 13.0), (16.0, 4.0), (2.0, 1.0), (13.0, 16.0)), (3, 3, 4, 1, 4, 4), 11)


OPTIMUM = (S72 + S37 + 7) + (S29 + S20 + S53 + S18 + S2)
TOUR_LENGTH = S29 + S20 + S53 + 5 + S37 + S74 + S2
