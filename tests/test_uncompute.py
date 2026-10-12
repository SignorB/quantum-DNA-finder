from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector

from src.cyclic_shift import controlled_cyclic_shift
from src.mark_zero import mark_all_zero
from src.uncompute import uncompute_match
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


def test_uncompute_preserves_marker_and_restores_registers():
    text_value = "101100"
    pattern_value = "10"

    # Classical matches of "10" inside "101100".
    matching_shifts = {0, 3}

    for shift in range(5):
        pattern = QuantumRegister(len(pattern_value), "pattern")
        text = QuantumRegister(len(text_value), "text")
        index = QuantumRegister(3, "index")
        marker = QuantumRegister(1, "marker")

        circuit = QuantumCircuit(
            pattern,
            text,
            index,
            marker,
        )

        # Step 2
        encode_bits(circuit, pattern, pattern_value)
        encode_bits(circuit, text, text_value)

        # Test one classical branch of the shift register.
        encode_shift(circuit, index, shift)

        # Step 4
        controlled_cyclic_shift(
            circuit,
            text,
            index,
        )

        # Step 5
        apply_pattern_xor(
            circuit,
            pattern,
            text,
        )

        # Step 6
        mark_all_zero(
            circuit,
            pattern,
            marker[0],
        )

        # Step 7
        uncompute_match(
            circuit,
            pattern,
            text,
            index,
        )

        expected_circuit = QuantumCircuit(
            pattern,
            text,
            index,
            marker,
        )

        # After uncomputation, text and pattern must be restored.
        encode_bits(
            expected_circuit,
            pattern,
            pattern_value,
        )

        encode_bits(
            expected_circuit,
            text,
            text_value,
        )

        # Shift register must also remain unchanged.
        encode_shift(
            expected_circuit,
            index,
            shift,
        )

        # Marker must preserve the comparison result.
        expected_marker = 1 if shift in matching_shifts else 0

        if expected_marker:
            expected_circuit.x(marker[0])

        actual_state = Statevector.from_instruction(circuit)
        expected_state = Statevector.from_instruction(expected_circuit)

        assert actual_state.equiv(expected_state), (
            f"Shift {shift} failed: "
            f"expected marker={expected_marker}, "
            f"text={text_value}, "
            f"pattern={pattern_value}"
        )

        print(
            f"shift {shift}: "
            f"text restored={text_value}, "
            f"pattern restored={pattern_value}, "
            f"marker={expected_marker}"
        )


if __name__ == "__main__":
    test_uncompute_preserves_marker_and_restores_registers()

    print("\nAll uncompute tests passed.")
