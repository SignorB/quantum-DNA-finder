from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector

from src.cyclic_shift import controlled_cyclic_shift
from src.xor_compare import apply_pattern_xor


def encode_bits(circuit, register, value):
    """Encode a binary string using one qubit per bit."""
    for qubit, bit in zip(register, value):
        if bit == "1":
            circuit.x(qubit)


def encode_shift(circuit, shift_register, shift):
    """Encode an integer shift using little-endian binary."""
    for bit_position, qubit in enumerate(shift_register):
        if (shift >> bit_position) & 1:
            circuit.x(qubit)


def xor_strings(first, second):
    """Classical reference implementation of bitwise XOR."""
    return "".join("1" if a != b else "0" for a, b in zip(first, second))


def rotate_left(value, shift):
    """Classical reference implementation of cyclic left rotation."""
    if not value:
        return value

    shift %= len(value)

    if shift == 0:
        return value

    return value[shift:] + value[:shift]


def test_pattern_xor_after_shift():
    text_value = "101100"
    pattern_value = "10"

    expected_xor_results = {
        0: "00",
        1: "11",
        2: "01",
        3: "00",
        4: "10",
    }

    for shift in range(5):
        pattern = QuantumRegister(len(pattern_value), "pattern")
        text = QuantumRegister(len(text_value), "text")
        index = QuantumRegister(3, "index")

        circuit = QuantumCircuit(pattern, text, index)

        # Step 2: encode pattern and text
        encode_bits(circuit, pattern, pattern_value)
        encode_bits(circuit, text, text_value)

        # Encode one classical shift value.
        encode_shift(circuit, index, shift)

        # Step 4: controlled cyclic shift
        controlled_cyclic_shift(
            circuit,
            text,
            index,
        )

        # Step 5: XOR candidate substring with pattern
        apply_pattern_xor(
            circuit,
            pattern,
            text,
        )

        shifted_text = rotate_left(text_value, shift)
        candidate = shifted_text[: len(pattern_value)]

        expected_xor = xor_strings(
            pattern_value,
            candidate,
        )

        assert expected_xor == expected_xor_results[shift]

        # Build the expected final quantum state.
        expected_circuit = QuantumCircuit(pattern, text, index)

        encode_bits(
            expected_circuit,
            pattern,
            expected_xor,
        )

        encode_bits(
            expected_circuit,
            text,
            shifted_text,
        )

        encode_shift(
            expected_circuit,
            index,
            shift,
        )

        actual_state = Statevector.from_instruction(circuit)
        expected_state = Statevector.from_instruction(expected_circuit)

        assert actual_state.equiv(expected_state), (
            f"Shift {shift} failed: "
            f"candidate={candidate}, "
            f"expected XOR={expected_xor}"
        )

        print(
            f"shift {shift}: "
            f"candidate={candidate}, "
            f"pattern={pattern_value}, "
            f"xor={expected_xor}"
        )


if __name__ == "__main__":
    test_pattern_xor_after_shift()

    print("\nAll XOR comparison tests passed.")
