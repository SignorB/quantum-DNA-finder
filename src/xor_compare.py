from qiskit import QuantumCircuit


def apply_pattern_xor(circuit: QuantumCircuit, pattern_qubits, text_qubits) -> None:
    """
    XOR the pattern register with the first part of the shifted text.

    For each pattern qubit:
        pattern[i] <- pattern[i] XOR text[i]

    Therefore, the pattern register becomes composed by only zeros when the
    pattern matches the beginning of the shifted text register.

    This operation is (self)invertible and so can be applied again during the
    uncomputation step (7).
    """
    if len(pattern_qubits) > len(text_qubits):
        raise ValueError("Pattern register cannot be longer thant the text register!")

    for pattern_qubits, text_qubits in zip(
        pattern_qubits,
        text_qubits[: len(pattern_qubits)],
    ):
        circuit.cx(text_qubits, pattern_qubits)
