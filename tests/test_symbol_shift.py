import numpy as np
import pytest
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector

from src.cyclic_shift import controlled_cyclic_shift, inverse_controlled_cyclic_shift
from src.experiments import run_experiment
from src.grover import amplify_matches, compare_results, shift_probabilities
from src.quantum_string_finder import build_shift_superposition, encode_bits


@pytest.mark.parametrize('amount', range(4))
def test_shift_rotates_complete_blocks_and_inverse_restores_them(amount):
    text, index = QuantumRegister(6), QuantumRegister(2)
    qc = QuantumCircuit(text, index)
    encode_bits(qc, text, '001011')  # Three two-qubit symbols.
    for bit in range(2):
        if (amount >> bit) & 1:
            qc.x(index[bit])
    original = qc.copy()
    controlled_cyclic_shift(qc, text, index, bits_per_symbol=2)
    expected = QuantumCircuit(text, index)
    blocks = ['00', '10', '11']
    offset = amount % 3
    encode_bits(expected, text, ''.join(blocks[offset:] + blocks[:offset]))
    for bit in range(2):
        if (amount >> bit) & 1:
            expected.x(index[bit])
    assert Statevector.from_instruction(qc).equiv(Statevector.from_instruction(expected))
    inverse_controlled_cyclic_shift(qc, text, index, bits_per_symbol=2)
    assert Statevector.from_instruction(qc).equiv(Statevector.from_instruction(original))


@pytest.mark.parametrize('text, motif, matches', [
    ('00011011', '1100', []),  # ACGT / TA: circular match is invalid.
    ('00011011', '0110', [1]),  # ACGT / CG.
    ('00010001', '0001', [0, 2]),  # ACAC / AC.
    ('0110', '11', []),  # CG / T: a match across symbol boundaries is invalid.
])
def test_two_bit_experiments_use_symbol_positions(text, motif, matches, capsys):
    results = run_experiment(text, motif, max_iterations=2, shots=32, bits_per_symbol=2)
    valid_count = len(text) // 2 - len(motif) // 2 + 1
    theta = np.arcsin(np.sqrt(len(matches) / valid_count))
    for iteration, result in enumerate(results):
        assert result['classical_matches'] == matches
        assert result['success_probability'] == pytest.approx(
            np.sin((2 * iteration + 1) * theta)**2, abs=1e-10)
        assert result['invalid_probability'] == pytest.approx(0, abs=1e-10)


def test_builder_retains_symbol_size_for_grover():
    qc = build_shift_superposition('00011011', '0110', bits_per_symbol=2)
    assert qc.num_qubits == 15
    assert len(qc.qregs[2]) == 2
    amplified = amplify_matches(qc)
    probabilities = shift_probabilities(amplified, amplified.qregs[2])
    assert compare_results('ACGT', 'CG', probabilities)['success_probability'] == pytest.approx(25 / 27)


@pytest.mark.parametrize('text, motif, width', [('001', '00', 2), ('0011', '0', 2), ('00', '0', 0)])
def test_incomplete_blocks_are_rejected(text, motif, width):
    with pytest.raises(ValueError):
        build_shift_superposition(text, motif, bits_per_symbol=width)
