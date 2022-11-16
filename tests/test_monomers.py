import pytest

from pore_c2.model import EnzymeCutter
from pore_c2.testing import simulate_sequence_with_cut_sites


@pytest.mark.parametrize("enzyme_id", ["EcoRI", "HindIII", "AloI"])
def test_enzyme_digest(enzyme_id):
    true_pos, seq = simulate_sequence_with_cut_sites(enzyme_id)
    if enzyme_id != "AloI":
        cutter = EnzymeCutter.from_name(enzyme_id)
        positions = cutter.get_cut_sites(seq)
        assert true_pos == positions
    else:
        with pytest.raises(NotImplementedError):
            cutter = EnzymeCutter.from_name(enzyme_id)
            cutter.get_cut_sites(seq)
