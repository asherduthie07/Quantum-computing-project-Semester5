"""Measurement-only recovery and paper-style XOR explanations shared by CLI/API."""

def recover_from_measurements(samples, n, P, ciphertexts):
    """No secret-key arguments: only observations and public/known cipher data."""
    observed = list(dict.fromkeys(b for b in samples if not isinstance(samples, dict) or samples[b] > 0))
    if any(len(b) != n or set(b) - {'0', '1'} for b in observed):
        raise ValueError('Measurements must be n-bit binary strings')
    preferred = ['010', '101'] if n == 3 else []
    ordered = [b for b in preferred if b in observed] + [b for b in observed if b not in preferred]
    possible = list(range(1 << n))
    selected = []
    for b in ordered:
        remaining = [s for s in possible if (int(b, 2) & s).bit_count() % 2 == 0]
        if len(remaining) < len(possible):
            selected.append(b)
            possible = remaining
    names = list('abcdef')[:n]
    expression = lambda terms: ' XOR '.join(names[i] for i in sorted(terms)) or '0'
    equations = [{i for i, v in enumerate(b) if v == '1'} for b in selected]
    lines = [f"Let k1 = ({', '.join(names)}), from most significant to least significant bit.",
             'Each measured y gives y dot k1 = 0 (mod 2). XOR means addition modulo 2.']
    for i, (b, terms) in enumerate(zip(selected, equations), 1):
        lines.extend([f'Measurement {i}: y = {b}',
                      ' XOR '.join(f'{v}({name})' for v, name in zip(b, names)) + ' = 0',
                      f'Therefore: {expression(terms)} = 0'])
        if len(terms) == 2:
            a, b_index = sorted(terms)
            lines.append(f'This means {names[a]} = {names[b_index]}: equal bits XOR to zero.')
    lines.append('Combine the equations using substitution:')
    # Isolate one variable, substitute it in the remaining equations, and later
    # evaluate the free bits. This produces ordinary symbolic equations only.
    pending = [set(eq) for eq in equations]
    relations = []
    while pending:
        pending = [eq for eq in pending if eq]
        if not pending:
            break
        eq = min(pending, key=lambda value: (len(value), sorted(value)))
        pending.remove(eq)
        variable = min(eq)
        rhs = eq - {variable}
        relations.append((variable, rhs))
        lines.append(f'{names[variable]} = {expression(rhs)}')
        updated = []
        for other in pending:
            if variable in other:
                rest = other - {variable}
                substituted = ' XOR '.join(filter(None, [expression(rest) if rest else '', f'({expression(rhs)})']))
                reduced = rest ^ rhs
                lines.append(f'Substitute {names[variable]} = {expression(rhs)} into {expression(other)} = 0: {substituted} = 0; hence {expression(reduced)} = 0.')
                if len(reduced) == 2:
                    a, b = sorted(reduced)
                    lines.append(f'Therefore {names[a]} = {names[b]}.')
                updated.append(reduced)
            else:
                updated.append(other)
        pending = updated
    free = [i for i in range(n) if i not in [v for v, _ in relations]]
    lines.append('Try the possible values of the free bits: ' + (', '.join(names[i] for i in free) or 'none') + '.')
    assignments = []
    for choice in range(1 << len(free)):
        values = dict(zip(free, map(int, format(choice, f'0{len(free)}b')))) if free else {}
        calculations = []
        for variable, rhs in reversed(relations):
            terms = [values[i] for i in sorted(rhs)]
            values[variable] = sum(terms) % 2
            calculations.append(f"{names[variable]} = {' XOR '.join(map(str, terms)) or '0'} = {values[variable]}")
        binary = ''.join(str(values[i]) for i in range(n))
        assignments.append(int(binary, 2))
        given = ', '.join(f'{names[i]} = {values[i]}' for i in free) or 'No free bits'
        lines.append(f"{given}: {'; '.join(calculations)}. ({', '.join(str(values[i]) for i in range(n))}) = {binary} (binary).")
    assert sorted(assignments) == possible
    lines.append('Computational verification: test every n-bit value against all actual measured equations; the same possibilities remain: ' + ', '.join(format(s, f'0{n}b') for s in possible) + '.')
    candidates = [s for s in possible if s != 0]
    lines.append('Simon’s nonzero-period promise excludes ' + '0' * n + '.')
    first = candidates[0] if len(candidates) == 1 else None
    lines.append(f'Recovered first key: k1 = {first:0{n}b}' if first is not None else 'The measurements do not identify a unique nonzero period. Collect more independent measurements or check the promise.')
    second = ciphertexts[0] ^ P[first] if first is not None else None
    verification = [] if first is None else [dict(x=x, original=e, recovered=P[x ^ first] ^ second, match=e == (P[x ^ first] ^ second)) for x, e in enumerate(ciphertexts)]
    return dict(selected=selected, explanation=lines, candidates=candidates, possible=possible,
                recovered_k1=first, recovered_k2=second, verification=verification,
                all_match=bool(verification) and all(v['match'] for v in verification))
