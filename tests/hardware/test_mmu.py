from gbemu.cart import Cart
from gbemu.config import BIOS, M_BOOT_ROM_MAPPING_CONTROL, MEMORY_SIZE
from gbemu.mmu import MMU


def test_mmu_uses_configured_memory_size() -> None:
    mmu = MMU()

    assert len(mmu) == MEMORY_SIZE
    assert len(mmu.memory) == MEMORY_SIZE


def test_mmu_reads_and_writes_work_for_ram_addresses() -> None:
    mmu = MMU()

    mmu[0xC000] = 0x42
    mmu[0xDFFF] = 0x99

    assert mmu[0xC000] == 0x42
    assert mmu[0xDFFF] == 0x99


def test_mmu_masks_written_values_to_8_bits() -> None:
    mmu = MMU()

    mmu[0xC123] = 0x1FF
    mmu[0xC124] = -1

    assert mmu[0xC123] == 0xFF
    assert mmu[0xC124] == 0xFF


def test_mmu_slice_reads_return_underlying_range() -> None:
    mmu = MMU()

    mmu[0xC000] = 0x12
    mmu[0xC001] = 0x34
    mmu[0xC002] = 0x56
    mmu[0xC003] = 0x78

    assert mmu[0xC000:0xC004] == [0x12, 0x34, 0x56, 0x78]


def test_mmu_exposes_mutable_memory_view() -> None:
    mmu = MMU()

    mmu.memory[0xC200] = 0xAB

    assert mmu[0xC200] == 0xAB


def test_mmu_boot_rom_overlays_cartridge_startup_region() -> None:
    cart = Cart("roms/hello.gb")
    mmu = MMU(cart)

    assert mmu[0x0000] == BIOS[0]
    assert mmu[0x00FF] == BIOS[0xFF]
    assert list(mmu[0x0100:0x0134]) == list(cart.rom[0x0100:0x0134])


def test_mmu_boot_rom_unmap_restores_cartridge_bytes() -> None:
    cart = Cart("roms/hello.gb")
    mmu = MMU(cart)

    assert list(mmu[0x0000:0x0100]) == BIOS

    mmu[M_BOOT_ROM_MAPPING_CONTROL] = 0x01

    assert list(mmu[0x0000:0x0100]) == list(cart.rom[0x0000:0x0100])
    assert mmu[M_BOOT_ROM_MAPPING_CONTROL] == 0x01


def test_mmu_boot_rom_unmap_is_one_way() -> None:
    cart = Cart("roms/hello.gb")
    mmu = MMU(cart)

    mmu[M_BOOT_ROM_MAPPING_CONTROL] = 0x01
    original_rom_prefix = list(cart.rom[0x0000:0x0010])

    mmu[0x0000] = 0x00
    mmu[M_BOOT_ROM_MAPPING_CONTROL] = 0x00

    assert mmu[0x0000] == 0x00
    assert list(mmu[0x0000:0x0010]) != BIOS[:0x10]
    assert list(cart.rom[0x0000:0x0010]) == original_rom_prefix


def test_mmu_write_to_ff50_without_cart_only_stores_register_value() -> None:
    mmu = MMU()
    bios_prefix = list(mmu[0x0000:0x0010])

    mmu[M_BOOT_ROM_MAPPING_CONTROL] = 0x01

    assert mmu[M_BOOT_ROM_MAPPING_CONTROL] == 0x01
    assert list(mmu[0x0000:0x0010]) == bios_prefix
