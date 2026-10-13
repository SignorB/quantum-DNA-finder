import pytest
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector

from src import mark_zero
from src.cyclic_shift import controlled_cyclic_shift
from src.experiments import encode_dna
from src.quantum_string_finder import encode_bits
from src.uncompute import uncompute_match
from src.xor_compare import apply_pattern_xor


@pytest.mark.parametrize('valid_count', [1, 3, 5, 8])
def test_marker_checks_index_and_comparison_and_preserves_controls(valid_count):
    comparison = QuantumRegister(2, 'comparison')
    shift = QuantumRegister(3, 'shift')
    marker = QuantumRegister(1, 'marker')
    for position in range(8):
        for value in ['00', '01', '10', '11']:
            for initial_marker in [0, 1]:
                qc = QuantumCircuit(comparison, shift, marker)
                encode_bits(qc, comparison, value)
                for bit in range(3):
                    if (position >> bit) & 1:
                        qc.x(shift[bit])
                if initial_marker:
                    qc.x(marker[0])
                expected = qc.copy()
                if value == '00' and position < valid_count:
                    expected.x(marker[0])
                mark_zero.mark_valid_match(qc, comparison, marker[0], shift, valid_count)
                assert Statevector.from_instruction(qc).equiv(Statevector.from_instruction(expected))
                assert qc.num_qubits == 6


@pytest.mark.parametrize('motif, matching_positions', [('TA', []), ('CG', [1])])
def test_dna_oracle_rejects_forced_circular_match(motif, matching_positions):
    pattern, text = QuantumRegister(4, 'pattern'), QuantumRegister(8, 'text')
    shift, marker = QuantumRegister(2, 'index'), QuantumRegister(1, 'marker')
    for position in range(4):  # Includes invalid index 3, even though preparation excludes it.
        qc = QuantumCircuit(pattern, text, shift, marker)
        encode_bits(qc, pattern, encode_dna(motif))
        encode_bits(qc, text, encode_dna('ACGT'))
        for bit in range(2):
            if (position >> bit) & 1:
                qc.x(shift[bit])
        expected = qc.copy()
        if position in matching_positions:
            expected.x(marker[0])
        controlled_cyclic_shift(qc, text, shift, 2)
        apply_pattern_xor(qc, pattern, text)
        mark_zero.mark_valid_match(qc, pattern, marker[0], shift, valid_count=3)
        uncompute_match(qc, pattern, text, shift, 2)
        assert Statevector.from_instruction(qc).equiv(Statevector.from_instruction(expected))
