from qiskit import QuantumCircuit


def controlled_rotate_left(
    circuit: QuantumCircuit,
    text_qubits,
    control_qubit,
    bits_per_symbol=1,
) -> None:
    """
    Rotate one complete symbol to the left if control_qubit is |1>.

    Example:
        10100 -> 01001 (one bit per symbol)

    Note that `text_qubits[0]` represents the first logical bit of the string.
    """
    if len(text_qubits) < 2:
        return

    for start in range(0, len(text_qubits) - bits_per_symbol, bits_per_symbol):
        for bit in range(bits_per_symbol):
            circuit.cswap(control_qubit, text_qubits[start + bit],
                          text_qubits[start + bits_per_symbol + bit])


def controlled_cyclic_shift(
    circuit: QuantumCircuit,
    text_qubits,
    shift_qubits,
    bits_per_symbol=1,
) -> None:
    """
    Apply a cyclic left shift in symbols, encoded in the shift register.

    Here the shift register is interpreted as little endian:

        shift_qubits[0] -> weight 1
        shift_qubits[1] -> weight 2
        shift_qubits[2] -> weight 4
    """
    if not text_qubits:
        return

    for bit_position, control_qubit in enumerate(shift_qubits):
        shift_amount = (2**bit_position) % (len(text_qubits) // bits_per_symbol)

        for _ in range(shift_amount):
            controlled_rotate_left(
                circuit,
                text_qubits,
                control_qubit,
                bits_per_symbol,
            )


def controlled_rotate_right(
    circuit: QuantumCircuit,
    text_qubits,
    control_qubit,
    bits_per_symbol=1,
) -> None:
    """
    This is the inverse of controlled_rotate_left.

    Rotate one complete symbol to the right if control_qubit is |1>.
    """
    if len(text_qubits) < 2:
        return

    for start in range(len(text_qubits) - bits_per_symbol, 0, -bits_per_symbol):
        for bit in range(bits_per_symbol):
            circuit.cswap(control_qubit, text_qubits[start - bits_per_symbol + bit],
                          text_qubits[start + bit])


def inverse_controlled_cyclic_shift(
    circuit: QuantumCircuit,
    text_qubits,
    shift_qubits,
    bits_per_symbol=1,
) -> None:
    """
    Undo the controlled_cyclic_shift.

    The controlled shift operations are applied in reverse order, using right rotations.
    """
    if not text_qubits:
        return

    for bit_position in reversed(range(len(shift_qubits))):
        control_qubit = shift_qubits[bit_position]
        shift_amount = (2**bit_position) % (len(text_qubits) // bits_per_symbol)

        for _ in range(shift_amount):
            controlled_rotate_right(
                circuit,
                text_qubits,
                control_qubit,
                bits_per_symbol,
            )
