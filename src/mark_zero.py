from qiskit import QuantumCircuit
from qiskit.circuit.library import MCXGate


def mark_all_zero(
    circuit: QuantumCircuit,
    comparison_qubits,
    marker_qubit,
) -> None:
    """
    Flip marker_qubit if and only if all comparison_qubits are |0>.

    The comparison register is restored to its original state after
    the marking operation.

    Example:
        00 -> marker flips
        01 -> marker unchanged
        10 -> marker unchanged
        11 -> marker unchanged
    """

    if len(comparison_qubits) == 0:
        raise ValueError("Comparison register cannot be empty!")

    # Convert controls on |0> into controls on |1>
    for qubit in comparison_qubits:
        circuit.x(qubit)
    # Flip the marker only when all comparison qubits are |1>
    if len(comparison_qubits) == 1:
        circuit.cx(comparison_qubits[0], marker_qubit)
    else:
        circuit.mcx(comparison_qubits, marker_qubit)

    # Restore the comparison register
    for qubit in comparison_qubits:
        circuit.x(qubit)


def mark_valid_match(circuit, comparison_qubits, marker_qubit, shift_qubits, valid_count):
    controls = list(comparison_qubits) + list(shift_qubits)
    for position in range(valid_count):
        # Low control bits require comparison=0; high bits require shift=position.
        state = position << len(comparison_qubits)
        gate = MCXGate(len(controls), ctrl_state=state)
        circuit.append(gate, controls + [marker_qubit])
