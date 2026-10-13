import numpy as np
import pytest

from src import experiments


def test_dna_encoding():
    assert experiments.encode_dna('ACGT') == '00011011'
    assert experiments.encode_dna('acgt') == '00011011'


@pytest.mark.parametrize('text, motif, matches', [
    ('ACGT', 'TA', []), ('ACGT', 'CG', [1]), ('ACAC', 'AC', [0, 2]),
])
def test_dna_experiments(text, motif, matches, capsys):
    results = experiments.run_experiment(text, motif, max_iterations=3, shots=32, dna=True)
    theta = np.arcsin(np.sqrt(len(matches) / 3))
    for iteration, result in enumerate(results):
        assert result['classical_matches'] == matches
        assert result['success_probability'] == pytest.approx(
            np.sin((2 * iteration + 1) * theta)**2, abs=1e-10)
        assert result['invalid_probability'] == pytest.approx(0, abs=1e-10)
    output = capsys.readouterr().out
    assert f'Text: {text} | Motif: {motif} | Qubits: 15' in output
