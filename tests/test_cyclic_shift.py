# Used to test the step 4.

from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector

from src.cyclic_shift import controlled_cyclic_shift


def encode_bits(circuit, register, value):
    """Encode a binary string using one qubit per bit."""
    for qubit, bit in zip(register, value):
        if bit == "1":
            circuit.x(qubit)


def encode_shift(circuit, shift_register, shift):
    """Encode an integer shift using little endian binary."""
    for bit_position, qubit in enumerate(shift_register):
        if (shift >> bit_position) & 1:
            circuit.x(qubit)


def rotate_right(value, shift):
    """Classical reference implementation of a cyclic right rotation."""
    if not value:
        return value

    shift %= len(value)

    if shift == 0:
        return value

    return value[-shift:] + value[:-shift]


def test_controlled_cyclic_shift():
    text_value = "101100"

    # For text length 6 and pattern length 2, the valid shifts are 0, 1, 2, 3, 4.
    for shift in range(5):
        text = QuantumRegister(len(text_value), "text")
        index = QuantumRegister(3, "index")

        circuit = QuantumCircuit(text, index)

        encode_bits(circuit, text, text_value)
        encode_shift(circuit, index, shift)

        controlled_cyclic_shift(
            circuit,
            text,
            index,
        )

        # Build the state that we expect to obtain.
        expected_text = rotate_right(text_value, shift)

        expected_circuit = QuantumCircuit(text, index)

        encode_bits(
            expected_circuit,
            text,
            expected_text,
        )

        encode_shift(
            expected_circuit,
            index,
            shift,
        )

        actual_state = Statevector.from_instruction(circuit)
        expected_state = Statevector.from_instruction(expected_circuit)

        assert actual_state.equiv(expected_state), (
            f"Shift {shift} failed: " f"expected {expected_text}"
        )

        print(f"shift {shift}: " f"{text_value} -> {expected_text} ✓")


if __name__ == "__main__":
    test_controlled_cyclic_shift()

    print("\nAll cyclic shift tests passed.")
