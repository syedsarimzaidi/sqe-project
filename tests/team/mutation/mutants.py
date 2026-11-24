"""Mutant definitions for StockItem.add_stock() / take_stock().

Rather than mutating the whole 3,800-line stock/models.py file with a generic tool
(which would generate an unmanageable number of irrelevant mutants across unrelated
model classes), this targets exactly the two selected-workflow methods with a mix of:

  - standard mutation operators (relational, arithmetic/boundary, constant replacement)
  - 2 CUSTOM operators written specifically for this project's business rules:
      * ClampInversion   -> targets BR-1 (the min() clamp that prevents negative stock)
      * SerializedGuardRemoval -> targets BR-2 (the "not serialized" guard condition)

Each mutant is a (search, replace) substitution applied to the *source text* of the
target method before it is recompiled and monkey-patched onto StockItem for one test run.
"""
from dataclasses import dataclass


@dataclass
class Mutant:
    id: str
    target: str  # 'add_stock' or 'take_stock'
    operator: str
    description: str
    search: str
    replace: str


MUTANTS = [
    # --- Standard operator: relational operator replacement (ROR) ---------------
    Mutant('M01', 'add_stock', 'ROR', 'quantity <= 0  ->  quantity < 0',
           'if quantity <= 0:', 'if quantity < 0:'),
    Mutant('M02', 'take_stock', 'ROR', 'quantity <= 0  ->  quantity < 0 (pre-clamp)',
           'if quantity <= 0:\n            return False\n\n        # Lock',
           'if quantity < 0:\n            return False\n\n        # Lock'),
    Mutant('M03', 'take_stock', 'ROR', 'post-clamp quantity <= 0  ->  quantity < 0',
           'quantity = min(quantity, self.quantity)\n\n        if quantity <= 0:',
           'quantity = min(quantity, self.quantity)\n\n        if quantity < 0:'),

    # --- Standard operator: negation removal (guard deletion) -------------------
    Mutant('M04', 'add_stock', 'NR', 'remove serialized guard entirely',
           'if self.serialized:\n            return False\n\n        try:',
           'try:'),
    Mutant('M05', 'take_stock', 'NR', 'remove serialized guard entirely',
           'if self.serialized:\n            return False\n\n        try:',
           'try:'),

    # --- Standard operator: constant replacement ---------------------------------
    Mutant('M06', 'add_stock', 'CR', 'return True  ->  return False (always fail)',
           'self.updateQuantity(self.quantity + quantity)\n\n        return True',
           'self.updateQuantity(self.quantity + quantity)\n\n        return False'),
    Mutant('M07', 'take_stock', 'CR', 'return True  ->  return False (always fail)',
           'self.updateQuantity(self.quantity - quantity)\n\n        return True',
           'self.updateQuantity(self.quantity - quantity)\n\n        return False'),

    # --- Standard operator: arithmetic operator replacement (AOR) ---------------
    Mutant('M08', 'add_stock', 'AOR', 'self.quantity + quantity  ->  self.quantity - quantity',
           'self.updateQuantity(self.quantity + quantity)',
           'self.updateQuantity(self.quantity - quantity)'),
    Mutant('M09', 'take_stock', 'AOR', 'self.quantity - quantity  ->  self.quantity + quantity',
           'self.updateQuantity(self.quantity - quantity)',
           'self.updateQuantity(self.quantity + quantity)'),

    # --- CUSTOM operator 1: ClampInversion (targets BR-1) ------------------------
    # BR-1 says removal must never take quantity below zero; InvenTree enforces this
    # with `quantity = min(requested, available)`. Flipping min->max would let a removal
    # request EXCEED available stock, driving quantity negative - exactly the defect
    # BR-1 exists to prevent.
    Mutant('M10', 'take_stock', 'ClampInversion (custom, BR-1)',
           'min(requested, available) -> max(requested, available): would allow removal '
           'beyond available stock, violating the "never go negative" business rule',
           'quantity = min(quantity, self.quantity)',
           'quantity = max(quantity, self.quantity)'),

    # --- CUSTOM operator 2: SerializedGuardRemoval (targets BR-2, condition (b)) --
    # BR-2 is a 2-condition decision rule: (a) quantity valid AND (b) item not serialized.
    # This operator specifically inverts condition (b) alone (not a blanket guard
    # deletion like M04/M05), simulating a developer accidentally allowing adjustment
    # of serialized items - a realistic defect for a trackable-inventory business rule.
    Mutant('M11', 'add_stock', 'SerializedGuardRemoval (custom, BR-2b)',
           'self.serialized  ->  not self.serialized (inverted condition b)',
           'if self.serialized:\n            return False',
           'if not self.serialized:\n            return False'),
    Mutant('M12', 'take_stock', 'SerializedGuardRemoval (custom, BR-2b)',
           'self.serialized  ->  not self.serialized (inverted condition b)',
           'if self.serialized:\n            return False',
           'if not self.serialized:\n            return False'),

    # --- Standard operator: boundary off-by-one on BR-3 (delete_on_deplete) -----
    Mutant('M13', 'take_stock', 'Boundary', 'remove the record_tracking conditional branch',
           "if record_tracking:\n            event = self.tracking_event(\n                code, user, notes=kwargs.get('notes', ''), deltas=deltas\n            )\n        else:\n            event = nullcontext()",
           "event = self.tracking_event(\n            code, user, notes=kwargs.get('notes', ''), deltas=deltas\n        )"),

    # --- Standard operator: statement deletion (lock guard) ----------------------
    Mutant('M14', 'add_stock', 'StatementDeletion', 'remove lock_quantity() guard',
           'if not self.lock_quantity():\n            return False\n\n        tracking_info = {}',
           'tracking_info = {}'),
    Mutant('M15', 'take_stock', 'StatementDeletion', 'remove lock_quantity() guard',
           'if not self.lock_quantity():\n            return False\n\n        # Cannot remove more',
           '# Cannot remove more'),
]
