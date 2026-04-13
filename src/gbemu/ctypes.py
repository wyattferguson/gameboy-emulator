class CallableDict(dict):
    """Run callable values when accessed."""

    def __getitem__(self, key: str) -> int:
        val = super().__getitem__(key)
        if callable(val):
            return val()
        return val

    def __setitem__(self, key: str, value: int) -> None:
        existing_value = super().get(key)
        if callable(existing_value):
            register_a = (value >> 8) & 0xFF
            register_b = value & 0xFF
            super().__setitem__(key[0], register_a)
            super().__setitem__(key[1], register_b)
        else:
            super().__setitem__(key, value)
