"""Assignment experiments. Configure below and run: python -m src.experiments."""

from random import Random

from .grover import amplify_matches, classical_matches, compare_results, measure_shift, shift_probabilities
from .quantum_string_finder import build_shift_superposition


# Edit these settings directly; no command-line arguments are needed.
RUN_BINARY = True
RUN_DNA = True
RUN_GENERATED_DNA = True
MAX_ITERATIONS = 3
SHOTS = 512
RANDOM_SEED = 54
GENERATED_TEXT_LENGTH = 6
GENERATED_MOTIF = "AC"
GENERATED_MATCH_POSITIONS = [[], [1], [0, 3]]  # Zero, one, two matches.

# Small circuit example followed by larger binary cases (at most 20 qubits).
BINARY_EXAMPLES = [
    ("101100", "10"),         # Small binary example: positions 0 and 3.
    ("000000000000", "11"),   # No match.
    ("000001100000", "110"),  # One match: position 5.
    ("000100010000", "10"),   # Two matches: positions 3 and 7.
]

# The three required examples (15 qubits), then longer cases (20 qubits).
DNA_EXAMPLES = [
    ("ACGT", "TA"),    # Required: no match.
    ("ACGT", "CG"),    # Required: position 1.
    ("ACAC", "AC"),    # Required: positions 0 and 2.
    ("ACGTAC", "CA"),  # No match: CA would wrap around the end.
    ("ACGTAC", "CG"),  # One match: position 1.
    ("ACACGT", "AC"),  # Two matches: positions 0 and 2.
]

DNA_ENCODING = {"A": "00", "C": "01", "G": "10", "T": "11"}


def encode_dna(sequence):
    return "".join(DNA_ENCODING[base] for base in sequence.upper())


def generate_dna(text_length, motif, positions, seed=54):
    """Insert a motif at chosen positions; reject unintended or missing matches."""
    motif = motif.upper()
    positions = sorted(positions)
    if (not motif or len(motif) > text_length
            or any(not 0 <= i <= text_length - len(motif) for i in positions)):
        raise ValueError("Motif and positions must fit inside the text.")
    rng = Random(seed)
    for _ in range(1000):
        text = [rng.choice("ACGT") for _ in range(text_length)]
        for position in positions:
            text[position:position + len(motif)] = motif
        text = "".join(text)
        if classical_matches(text, motif) == positions:
            return text
    raise ValueError("Could not generate exactly the requested matches in 1000 attempts.")


def run_experiment(text, motif, max_iterations=3, shots=512, bits_per_symbol=1, dna=False):
    text_bits, motif_bits = text, motif
    if dna:
        text, motif = text.upper(), motif.upper()
        text_bits, motif_bits = encode_dna(text), encode_dna(motif)
        bits_per_symbol = 2
    base = build_shift_superposition(text_bits, motif_bits, bits_per_symbol)
    if base.num_qubits > 20:
        raise ValueError("These experiments are limited to 20 total qubits.")
    shift = base.qregs[2]
    text_symbols = text if dna else [text[i:i + bits_per_symbol] for i in range(0, len(text), bits_per_symbol)]
    motif_symbols = motif if dna else [motif[i:i + bits_per_symbol] for i in range(0, len(motif), bits_per_symbol)]
    print(f"\nText: {text} | Motif: {motif} | Qubits: {base.num_qubits} | "
          f"Bits/symbol: {bits_per_symbol}", flush=True)
    results = []

    for iterations in range(max_iterations + 1):
        # Always start from the original circuit, not the previous iteration.
        qc = amplify_matches(base, iterations)
        probabilities = shift_probabilities(qc, shift)
        result = compare_results(text_symbols, motif_symbols, probabilities)
        result["iterations"] = iterations
        results.append(result)

        print(f"\nIterations: {iterations} | Matches: {result['classical_matches']}")
        print(f"Success: {result['success_probability']:.4%} | "
              f"Invalid positions: {result['invalid_probability']:.4%}")
        print("Position probabilities:",
              {i: round(p, 6) for i, p in probabilities.items()}, flush=True)

    # Sample the last circuit; more iterations do not necessarily work better.
    counts = measure_shift(qc, shift, shots=shots)
    frequencies = {i: count / shots for i, count in counts.items()}
    measured = compare_results(text_symbols, motif_symbols, frequencies)
    print(f"\nCounts at {max_iterations} iterations ({shots} shots): {counts}")
    print(f"Measured success: {measured['success_probability']:.4%}", flush=True)
    return results


if __name__ == "__main__":
    if RUN_BINARY:
        print("\n=== BINARY EXAMPLES ===", flush=True)
        for text, motif in BINARY_EXAMPLES:
            run_experiment(text, motif, MAX_ITERATIONS, SHOTS)
    if RUN_DNA:
        print("\n=== DNA: REQUIRED AND LONGER EXAMPLES ===", flush=True)
        for text, motif in DNA_EXAMPLES:
            run_experiment(text, motif, MAX_ITERATIONS, SHOTS, dna=True)
    if RUN_GENERATED_DNA:
        print("\n=== GENERATED DNA WITH VERIFIED MATCHES ===", flush=True)
        for case, positions in enumerate(GENERATED_MATCH_POSITIONS):
            seed = RANDOM_SEED + case
            text = generate_dna(GENERATED_TEXT_LENGTH, GENERATED_MOTIF, positions, seed)
            print(f"\nSeed: {seed} | Intended positions: {positions}", flush=True)
            run_experiment(text, GENERATED_MOTIF, MAX_ITERATIONS, SHOTS, dna=True)
