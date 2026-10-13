from qiskit import ClassicalRegister, QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit.quantum_info import Statevector

from .cyclic_shift import controlled_cyclic_shift
from .mark_zero import mark_all_zero
from .quantum_string_finder import select_valid_shifts
from .uncompute import uncompute_match
from .xor_compare import apply_pattern_xor


def diffusion(qc, shift, valid_count=None):
    shift = list(shift)
    if valid_count is None:
        valid_count = 2**len(shift)
    preparation = QuantumCircuit(len(shift))
    active_size = max(1, (valid_count - 1).bit_length())
    select_valid_shifts(preparation, preparation.qubits[:active_size], range(valid_count))

    qc.compose(preparation.inverse(), qubits=shift, inplace=True)
    qc.x(shift)
    if len(shift) == 1:
        qc.z(shift[0])
    else:
        qc.h(shift[-1])
        qc.mcx(shift[:-1], shift[-1])
        qc.h(shift[-1])
    qc.x(shift)
    qc.compose(preparation, qubits=shift, inplace=True)


def amplify_matches(qc, iterations=1):
    pattern, text, shift, marker = qc.qregs
    valid_count = len(text) - len(pattern) + 1

    check = QuantumCircuit(*qc.qregs)
    controlled_cyclic_shift(check, text, shift)
    apply_pattern_xor(check, pattern, text)
    mark_all_zero(check, pattern, marker[0])
    uncompute_match(check, pattern, text, shift)

    result = qc.copy()
    for iteration in range(iterations):
        if iteration > 0: 
            result.compose(check, inplace=True)
        result.z(marker[0])
        result.compose(check.inverse(), inplace=True)
        diffusion(result, shift, valid_count=valid_count)
    return result


def shift_probabilities(qc, shift):
    indices = [qc.find_bit(qubit).index for qubit in shift]
    probabilities = Statevector.from_instruction(qc).probabilities(qargs=indices)
    return {position: float(p) for position, p in enumerate(probabilities)}


def measure_shift(qc, shift, shots=4096, seed=54):
    measured = qc.copy()
    bits = ClassicalRegister(len(shift))
    measured.add_register(bits)
    measured.measure(shift, bits)
    result = StatevectorSampler(seed=seed).run([measured], shots=shots).result()[0]
    counts = getattr(result.data, bits.name).get_counts()
    return {int(bitstring, 2): count for bitstring, count in counts.items()}


def classical_matches(text, motif):
    return [i for i in range(len(text) - len(motif) + 1)
            if text[i:i + len(motif)] == motif]


def compare_results(text, motif, probabilities):
    matches = classical_matches(text, motif)
    last_valid = len(text) - len(motif)
    return {
        "classical_matches": matches,
        "probabilities": dict(probabilities),
        "success_probability": sum(probabilities.get(i, 0.0) for i in matches),
        "invalid_probability": sum(p for i, p in probabilities.items()
                                   if not 0 <= i <= last_valid),
    }
