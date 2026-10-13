import math

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector
from .cyclic_shift import controlled_cyclic_shift
from .cyclic_shift import inverse_controlled_cyclic_shift
from .xor_compare import apply_pattern_xor
from .mark_zero import mark_all_zero
from .uncompute import uncompute_match


def encode_bits(circuit, register, value):
    """Encode a binary string into a register using one qubit per bit."""
    if len(value) != len(register) or set(value) - {"0", "1"}:
        raise ValueError(
            "Values must be binary strings matching their register length."
        )

    for qubit, bit in zip(register, value):
        if bit == "1":
            circuit.x(qubit)


def select_valid_shifts(circuit, index_register, valid_shifts):
    """Prepare an exact uniform superposition over the valid shift values."""
    number_of_shifts = len(valid_shifts)
    register_size = len(index_register)

    if number_of_shifts == 1:
        return

    if number_of_shifts & (number_of_shifts - 1) == 0:
        for qubit in index_register:
            circuit.h(qubit)
        return

    amplitudes = np.zeros(2**register_size)
    amplitudes[:number_of_shifts] = 1 / math.sqrt(number_of_shifts)
    circuit.prepare_state(amplitudes, index_register)


def build_shift_superposition(text_value, pattern_value, bits_per_symbol=1):
    """Build from binary-encoded strings; each shift advances one whole symbol."""
    if not pattern_value or len(pattern_value) > len(text_value):
        raise ValueError("Pattern must be non-empty and no longer than the text.")

    if (bits_per_symbol < 1 or len(text_value) % bits_per_symbol
            or len(pattern_value) % bits_per_symbol):
        raise ValueError("Text and pattern must contain complete symbol blocks.")
    valid_shifts = range((len(text_value) - len(pattern_value)) // bits_per_symbol + 1)
    index_size = max(1, math.ceil(math.log2(len(valid_shifts))))

    # Registers
    pattern = QuantumRegister(len(pattern_value), "pattern")
    text = QuantumRegister(len(text_value), "text")
    index = QuantumRegister(index_size, "index")
    marker = QuantumRegister(1, "marker")
    # Circuit
    circuit = QuantumCircuit(pattern, text, index, marker)
    circuit.metadata["bits_per_symbol"] = bits_per_symbol

    # Step 2
    encode_bits(circuit, pattern, pattern_value)
    encode_bits(circuit, text, text_value)
    # Step 3
    select_valid_shifts(circuit, index, valid_shifts)

    # Step 4
    controlled_cyclic_shift(circuit, text, index, bits_per_symbol)

    # Step 5
    apply_pattern_xor(circuit, pattern, text)

    # Step 6
    mark_all_zero(circuit, pattern, marker[0])

    # Step 7
    uncompute_match(circuit, pattern, text, index, bits_per_symbol)
    return circuit


def verify_structure(circuit, number_of_valid_shifts):
    """Verify the register layout and shift superposition without measurement."""
    operation_names = {instruction.operation.name for instruction in circuit.data}
    assert "measure" not in operation_names
    assert circuit.num_qubits == sum(register.size for register in circuit.qregs)

    state = Statevector.from_instruction(circuit)
    index_qubits = circuit.qregs[2]
    index_positions = [circuit.find_bit(qubit).index for qubit in index_qubits]
    probabilities = state.probabilities(qargs=index_positions)
    expected = np.zeros(len(probabilities))
    expected[:number_of_valid_shifts] = 1 / number_of_valid_shifts
    np.testing.assert_allclose(probabilities, expected, atol=1e-12)
    return state


if __name__ == "__main__":
    circuit = build_shift_superposition("101100", "10")
    verify_structure(circuit, number_of_valid_shifts=5)
    print(circuit.draw())
    print(
        "Verified: text register, pattern register, and unmeasured shift superposition."
    )
