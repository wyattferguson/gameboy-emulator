"""

This package initializer exposes the primary emulator entry points for imports.

Step-by-step:
1. Define package-level documentation and stable exported names.
2. Import the public emulator class from the runtime module.
3. Re-export symbols so callers can use concise package imports.
4. Avoid package import side effects beyond symbol exposure.
5. Keep this module lightweight for fast startup.
"""

"""Game Boy emulator package."""

from gbemu.gbemu import Gbemu

__all__ = ["Gbemu"]
