import pytest

from src import experiments
from src.grover import classical_matches


@pytest.mark.parametrize('positions', [[], [1], [0, 3]])
def test_generated_dna_has_exactly_the_requested_matches(positions):
    text = experiments.generate_dna(6, 'AC', positions, seed=54)
    assert len(text) == 6
    assert set(text) <= set('ACGT')
    assert classical_matches(text, 'AC') == positions
    assert text == experiments.generate_dna(6, 'AC', positions, seed=54)


def test_generator_supports_consistent_overlaps():
    text = experiments.generate_dna(6, 'AA', [1, 2], seed=54)
    assert classical_matches(text, 'AA') == [1, 2]


def test_generator_stops_for_incompatible_overlaps():
    with pytest.raises(ValueError):
        experiments.generate_dna(4, 'AC', [0, 1], seed=54)


def test_generated_text_can_be_searched_by_the_circuit(capsys):
    text = experiments.generate_dna(4, 'AC', [1], seed=54)
    results = experiments.run_experiment(text, 'AC', max_iterations=1, shots=32, dna=True)
    assert results[1]['classical_matches'] == [1]
    assert results[1]['success_probability'] == pytest.approx(25 / 27)
    assert results[1]['invalid_probability'] == pytest.approx(0, abs=1e-10)
