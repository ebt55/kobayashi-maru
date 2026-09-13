import os
import sys

# Make the sandbox work dir importable so `from solution import <function>` works
# regardless of where pytest is invoked from.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
