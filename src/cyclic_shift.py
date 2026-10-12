from qiskit import QuantumCircuit


def controlled_rotate_left(
    circuit: QuantumCircuit,
    text_qubits,
    control_qubit,
) -> None:
    """
    Cyclically rotate the text register one position to the left if control_qubit is |1>.

    Example:
        10100 -> 011001

    Note that `text_qubits[0]` represents the first logical bit of the string.
    """
    if len(text_qubits) < 2:
        return

    for i in range(len(text_qubits) - 1):
        circuit.cswap(
            control_qubit,
            text_qubits[i],
            text_qubits[i + 1],
        )


def controlled_cyclic_shift(
    circuit: QuantumCircuit,
    text_qubits,
    shift_qubits,
) -> None:
    """
    Apply a cyclic left shift whose amount is encoded in the shift register.

    Here the shift register is interpreted as little endian:

        shift_qubits[0] -> weight 1
        shift_qubits[1] -> weight 2
        shift_qubits[2] -> weight 4
    """
    if not text_qubits:
        return

    for bit_position, control_qubit in enumerate(shift_qubits):
        shift_amount = (2**bit_position) % len(text_qubits)

        for _ in range(shift_amount):
            controlled_rotate_left(
                circuit,
                text_qubits,
                control_qubit,
            )
