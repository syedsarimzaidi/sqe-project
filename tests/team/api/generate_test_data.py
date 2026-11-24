"""Automated test-data generator (assignment Section 2, "Automated test data generation").

Reads the project's trimmed OpenAPI spec (docs/openapi_stock_workflows.json) and, from the
`quantity` field's declared constraints on the `StockAdjustmentItem` schema, produces:

  - Equivalence Partitioning (EP) classes for `quantity`
  - 3-point Boundary Value Analysis (BVA) triples for each numeric boundary found

The `--available-quantity` option supplies the one boundary that is a *business* value
(the stock currently available on the target item) rather than something declared in the
static OpenAPI schema — the schema only constrains quantity's shape (a decimal string,
max 10 integer digits / 5 decimal places), not any particular stock level.

API tests (test_stock_api.py) import and use this module's output directly, so that
"API tests must use its [the generator's] output" (assignment requirement).

Usage:
    python generate_test_data.py --spec ../../../docs/openapi_stock_workflows.json \
        --available-quantity 10
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EPClass:
    name: str
    description: str
    example: str
    valid: bool


@dataclass
class BVATriple:
    boundary_name: str
    just_below: str
    at_boundary: str
    just_above: str


@dataclass
class GeneratedData:
    ep_classes: list[EPClass] = field(default_factory=list)
    bva_triples: list[BVATriple] = field(default_factory=list)
    constraints_used: dict = field(default_factory=dict)


def load_quantity_constraints(spec_path: Path) -> dict:
    """Pull the quantity field's constraints out of the StockAdjustmentItem schema."""
    spec = json.loads(spec_path.read_text())
    quantity_schema = spec['components']['schemas']['StockAdjustmentItem']['properties'][
        'quantity'
    ]
    pattern = quantity_schema['pattern']
    # Pattern looks like: ^-?\d{0,10}(?:\.\d{0,5})?$  -> extract the two digit-count limits
    m = re.search(r'\\d\{0,(\d+)\}.*\\\.\\d\{0,(\d+)\}', pattern)
    max_integer_digits = int(m.group(1)) if m else 10
    max_decimal_places = int(m.group(2)) if m else 5
    return {
        'pattern': pattern,
        'max_integer_digits': max_integer_digits,
        'max_decimal_places': max_decimal_places,
    }


def generate(spec_path: Path, available_quantity: str) -> GeneratedData:
    constraints = load_quantity_constraints(spec_path)
    data = GeneratedData(constraints_used=constraints)

    max_int_digits = constraints['max_integer_digits']
    max_dec_places = constraints['max_decimal_places']

    # --- Equivalence Partitions -------------------------------------------------
    data.ep_classes = [
        EPClass('valid_positive', 'A valid positive decimal within schema limits', '5', True),
        EPClass('invalid_zero', 'Zero is syntactically valid but business-rejected', '0', False),
        EPClass(
            'invalid_negative', 'Negative value (schema permits the sign, business rejects)',
            '-3', False,
        ),
        EPClass('invalid_non_numeric', 'Not a decimal at all', 'abc', False),
        EPClass(
            'invalid_too_many_integer_digits',
            f'More than {max_int_digits} integer digits (exceeds schema pattern)',
            '1' * (max_int_digits + 1),
            False,
        ),
        EPClass(
            'invalid_too_many_decimal_places',
            f'More than {max_dec_places} decimal places (exceeds schema pattern)',
            '1.' + '1' * (max_dec_places + 1),
            False,
        ),
    ]

    # --- 3-point BVA -------------------------------------------------------------
    # Boundary 1: business rule BR-1 (the available-quantity clamp in take_stock())
    avail = available_quantity
    try:
        avail_num = float(avail)
    except ValueError:
        avail_num = 0.0
    data.bva_triples.append(
        BVATriple(
            boundary_name='available_quantity (BR-1 clamp, take_stock)',
            just_below=str(avail_num - 1),
            at_boundary=str(avail_num),
            just_above=str(avail_num + 1),
        )
    )

    # Boundary 2: zero (the "must be > 0" business rule, same for add_stock/take_stock)
    data.bva_triples.append(
        BVATriple(boundary_name='zero (must be > 0)', just_below='-1', at_boundary='0', just_above='1')
    )

    # Boundary 3: max integer digits allowed by the OpenAPI schema itself
    at = '9' * max_int_digits
    above = '9' * (max_int_digits + 1)
    below = '9' * (max_int_digits - 1)
    data.bva_triples.append(
        BVATriple(
            boundary_name=f'max_integer_digits (schema={max_int_digits})',
            just_below=below,
            at_boundary=at,
            just_above=above,
        )
    )

    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--spec',
        default=str(Path(__file__).parent.parent.parent.parent / 'docs' / 'openapi_stock_workflows.json'),
    )
    parser.add_argument('--available-quantity', default='10')
    parser.add_argument('--out', default=None, help='Optional: write JSON result to this path')
    args = parser.parse_args()

    data = generate(Path(args.spec), args.available_quantity)
    result = {
        'constraints_used': data.constraints_used,
        'ep_classes': [vars(e) for e in data.ep_classes],
        'bva_triples': [vars(b) for b in data.bva_triples],
    }
    text = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(text)
        print(f'Wrote {args.out}')
    else:
        print(text)


if __name__ == '__main__':
    main()
