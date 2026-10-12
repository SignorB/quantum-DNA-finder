from qiskit import QuantumCircuit


def controlled_rotate_right(
    circuit: QuantumCircuit,
    text_qubits,
    control_qubit,
) -> None:
    """
    Cyclically rotate the text register one position to the right if control_qubit is |1>.

    An example:
        1000 -> 0100
        0100 -> 0010
        0010 -> 0001
        0001 -> 1000

    Note that `text_qubits[0]` represents the first logical bit of the string.
    """
    if len(text_qubits) < 2:
        return

    for i in range(len(text_qubits) - 1, 0, -1):
        circuit.cswap(
            control_qubit,
            text_qubits[i - 1],
            text_qubits[i],
        )


def controlled_cyclic_shift(
    circuit: QuantumCircuit,
    text_qubits,
    shift_qubits,
) -> None:
    """
    Apply a cyclic right shift whose amount is encoded in the shift register.

    Here the shift register is interpreted as little endian:

        shift_qubits[0] -> weight 1
        shift_qubits[1] -> weight 2
        shift_qubits[2] -> weight 4

    Therefore, with two shift qubits:

        |00> -> shift 0
        |01> -> shift 1
        |10> -> shift 2
        |11> -> shift 3
    """
    if not text_qubits:
        return

    for bit_position, control_qubit in enumerate(shift_qubits):
        shift_amount = (2**bit_position) % len(text_qubits)

        for _ in range(shift_amount):
            controlled_rotate_right(
                circuit,
                text_qubits,
                control_qubit,
            )
