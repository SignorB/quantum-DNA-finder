def controlled_rotate_right(qc, text_qubits, control):
    """Controlled cyclic right rotation by one position."""

    n = len(text_qubits)

    for i in range(n - 1, 0, -1):
        qc.cswap(control, text_qubits[i - 1], text_qubits[i])


def controlled_cyclic_shift(qc, text_qubits, shift_qubits):
    """
    Controlled cyclic rotation.

    shift_qubits encode the rotation amount in binary, least significant bit first.
    """

    for j, control in enumerate(shift_qubits):

        repetitions = 2**j

        for _ in range(repetitions):
            controlled_rotate_right(qc, text_qubits, control)
