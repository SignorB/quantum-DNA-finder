import math

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector


def encode_bits(circuit, register, value):
    """Encode a binary string into a register using one qubit per bit."""
    if len(value) != len(register) or set(value) - {"0", "1"}:
        raise ValueError("Values must be binary strings matching their register length.")

    for qubit, bit in zip(register, value):
        if bit == "1":
            circuit.x(qubit)


def controlled_swap(circuit, control, first, second):
    """Apply a Fredkin gate without allocating a fan-out ancilla."""
    circuit.cswap(control, first, second)


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


def apply_controlled_power_shift(circuit, control, text_register, shift):
    """Rotate text right by shift, controlled by one index qubit."""
    shift %= len(text_register)
    for _ in range(shift):
        for position in range(len(text_register) - 1, 0, -1):
            controlled_swap(circuit, control, text_register[position], text_register[position - 1])


def build_shift_superposition(text_value, pattern_value):
    """Build the unmeasured register-and-shift portion of the matcher."""
    if not pattern_value or len(pattern_value) > len(text_value):
        raise ValueError("Pattern must be non-empty and no longer than the text.")

    valid_shifts = range(len(text_value) - len(pattern_value) + 1)
    index_size = max(1, math.ceil(math.log2(len(valid_shifts))))

    pattern = QuantumRegister(len(pattern_value), "pattern")
    text = QuantumRegister(len(text_value), "text")
    index = QuantumRegister(index_size, "index")
    circuit = QuantumCircuit(pattern, text, index)

    encode_bits(circuit, pattern, pattern_value)
    encode_bits(circuit, text, text_value)
    select_valid_shifts(circuit, index, valid_shifts)

    for bit_position, control in enumerate(index):
        apply_controlled_power_shift(circuit, control, text, 2**bit_position)

    return circuit


def verify_structure(circuit, number_of_valid_shifts):
    """Verify the register layout and shift superposition without measurement."""
    operation_names = {instruction.operation.name for instruction in circuit.data}
    assert "measure" not in operation_names
    assert circuit.num_qubits == sum(circuit.qregs[i].size for i in range(3))

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
    print("Verified: text register, pattern register, and unmeasured shift superposition.")




