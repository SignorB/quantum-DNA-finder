from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector

from src.mark_zero import mark_all_zero


def encode_bits(circuit, register, value):
    """Encode a binary string using one qubit per bit."""
    for qubit, bit in zip(register, value):
        if bit == "1":
            circuit.x(qubit)


def test_mark_all_zero():
    test_cases = {
        "00": "1",
        "01": "0",
        "10": "0",
        "11": "0",
    }

    for comparison_value, expected_marker in test_cases.items():
        comparison = QuantumRegister(
            len(comparison_value),
            "comparison",
        )
        marker = QuantumRegister(1, "marker")

        circuit = QuantumCircuit(comparison, marker)

        encode_bits(
            circuit,
            comparison,
            comparison_value,
        )

        mark_all_zero(
            circuit,
            comparison,
            marker[0],
        )

        expected_circuit = QuantumCircuit(
            comparison,
            marker,
        )

        # The comparison register must be preserved.
        encode_bits(
            expected_circuit,
            comparison,
            comparison_value,
        )

        if expected_marker == "1":
            expected_circuit.x(marker[0])

        actual_state = Statevector.from_instruction(circuit)
        expected_state = Statevector.from_instruction(expected_circuit)

        assert actual_state.equiv(expected_state), (
            f"Failed for comparison={comparison_value}: "
            f"expected marker={expected_marker}"
        )

        print(f"comparison={comparison_value} " f"-> marker={expected_marker}")


if __name__ == "__main__":
    test_mark_all_zero()

    print("\nAll zero-marker tests passed.")
