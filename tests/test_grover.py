import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector

from src import grover
from src.quantum_string_finder import build_shift_superposition, encode_bits


@pytest.mark.parametrize('size, valid_count', [(1, 1), (1, 2), (2, 3), (3, 5), (3, 2)])
def test_diffusion_reflects_about_valid_positions(size, valid_count):
    qc = QuantumCircuit(size)
    grover.diffusion(qc, qc.qubits, valid_count=valid_count)
    uniform = np.zeros(2**size)
    uniform[:valid_count] = 1 / np.sqrt(valid_count)
    expected = 2 * np.outer(uniform, uniform) - np.eye(2**size)
    assert Operator(qc).equiv(Operator(expected))


@pytest.mark.parametrize('text, motif, matches', [
    ('0100', '1', [1]), ('0000', '11', []), ('101100', '10', [0, 3]),
    ('0000', '00', [0, 1, 2]), ('1', '1', [0]), ('0', '1', []),
    ('1001', '11', []),  # The circular match at position 3 is invalid.
])
@pytest.mark.parametrize('iterations', [0, 1, 2, 3])
def test_full_pipeline(text, motif, matches, iterations):
    source = build_shift_superposition(text, motif)
    original = source.copy()
    qc = grover.amplify_matches(source, iterations=iterations)
    assert source == original
    pattern, text_register, shift, marker = qc.qregs
    probabilities = grover.shift_probabilities(qc, shift)
    result = grover.compare_results(text, motif, probabilities)
    valid_count = len(text) - len(motif) + 1
    theta = np.arcsin(np.sqrt(len(matches) / valid_count))
    assert result['classical_matches'] == matches
    assert result['success_probability'] == pytest.approx(
        np.sin((2 * iterations + 1) * theta)**2, abs=1e-10)
    assert result['invalid_probability'] == pytest.approx(0, abs=1e-10)
    assert sum(probabilities.values()) == pytest.approx(1)

    if iterations:
        # The full state must have restored text/pattern and a clean marker.
        expected = QuantumCircuit(*qc.qregs)
        encode_bits(expected, pattern, motif)
        encode_bits(expected, text_register, text)
        amplitudes = np.zeros(2**len(shift))
        for position in range(valid_count):
            if position in matches:
                amplitudes[position] = np.sin((2 * iterations + 1) * theta) / np.sqrt(len(matches))
            else:
                amplitudes[position] = np.cos((2 * iterations + 1) * theta) / np.sqrt(valid_count - len(matches))
        expected.prepare_state(amplitudes, shift)
        assert Statevector.from_instruction(qc).equiv(Statevector.from_instruction(expected))


def test_measurement_reads_index_register():
    source = build_shift_superposition('0100', '1')
    qc = grover.amplify_matches(source)
    shift = next(register for register in qc.qregs if register.name == 'index')
    assert grover.measure_shift(qc, shift, shots=100) == {1: 100}
    assert qc.num_clbits == 0


def test_original_uniform_diffusion_interface():
    qc = QuantumCircuit(2)
    grover.diffusion(qc, qc.qubits)
    assert Operator(qc).equiv(Operator(np.ones((4, 4)) / 2 - np.eye(4)))
