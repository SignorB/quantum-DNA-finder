from qiskit import QuantumCircuit

from .cyclic_shift import inverse_controlled_cyclic_shift
from .xor_compare import apply_pattern_xor


def uncompute_match(
    circuit: QuantumCircuit,
    pattern_qubits,
    text_qubits,
    shift_qubits,
    bits_per_symbol=1,
) -> None:
    """
    This reverses Steps 5 and 4 while leaving the marker qubit untouched.

    Reverse order:
        1. Undo pattern XOR (Step 5)
        2. Undo controlled cyclic shift (Step 4)
    """

    # Undo Step 5.
    # XOR/CNOT is self inverse.
    apply_pattern_xor(
        circuit,
        pattern_qubits,
        text_qubits,
    )

    # Undo Step 4.
    inverse_controlled_cyclic_shift(
        circuit,
        text_qubits,
        shift_qubits,
        bits_per_symbol,
    )
