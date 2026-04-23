from gbemu.cart import Cart
from gbemu.constants import BIOS, M_BOOT_ROM_MAPPING_CONTROL, MEMORY_SIZE, MMU_ROM_BANK_SIZE
from gbemu.mmu import MMU


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


def test_mmu_boot_rom_overlays_mbc1_cartridge_startup_region() -> None:
    cart = Cart("roms/sml.gb")
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

    assert mmu[0x0000] == original_rom_prefix[0]
    assert list(mmu[0x0000:0x0010]) != BIOS[:0x10]
    assert list(cart.rom[0x0000:0x0010]) == original_rom_prefix


def test_mmu_mbc1_bank_writes_do_not_hide_boot_rom_before_ff50() -> None:
    cart = Cart("roms/sml.gb")
    mmu = MMU(cart)

    mmu[0x2000] = 0x02
    mmu[0x4000] = 0x01
    mmu[0x6000] = 0x01

    assert mmu[0x0000] == BIOS[0]
    assert mmu[0x00FF] == BIOS[0xFF]


def test_mmu_mbc1_ff50_unmap_restores_current_rom_mapping() -> None:
    cart = Cart("roms/sml2.gb")
    cart.rom = bytearray(MMU_ROM_BANK_SIZE * 64)
    for bank in range(64):
        cart.rom[bank * MMU_ROM_BANK_SIZE] = bank

    mmu = MMU(cart)

    mmu[0x4000] = 0x01
    mmu[0x6000] = 0x01
    mmu[M_BOOT_ROM_MAPPING_CONTROL] = 0x01

    assert mmu[0x0000] == 0x20
    assert mmu[0x4000] == 0x21


def test_mmu_ignores_writes_to_cartridge_rom_region() -> None:
    cart = Cart("roms/hello.gb")
    mmu = MMU(cart)

    mmu[M_BOOT_ROM_MAPPING_CONTROL] = 0x01
    original = mmu[0x5234]

    mmu[0x5234] = original ^ 0xFF

    assert mmu[0x5234] == original


def test_mmu_write_to_ff50_without_cart_only_stores_register_value() -> None:
    mmu = MMU()
    bios_prefix = list(mmu[0x0000:0x0010])

    mmu[M_BOOT_ROM_MAPPING_CONTROL] = 0x01

    assert mmu[M_BOOT_ROM_MAPPING_CONTROL] == 0x01
    assert list(mmu[0x0000:0x0010]) == bios_prefix


def test_mmu_oam_dma_copies_160_bytes_from_selected_page() -> None:
    mmu = MMU()

    src_base = 0xC300
    for i in range(160):
        mmu[src_base + i] = (i * 3) & 0xFF

    mmu[0xFF46] = 0xC3

    assert list(mmu[0xFE00:0xFEA0]) == list(mmu[src_base : src_base + 160])


def test_mmu_blocks_cpu_access_to_oam_when_locked() -> None:
    mmu = MMU()
    mmu.set_ppu_bus_access(oam_locked=True, vram_locked=False)

    mmu[0xFE00] = 0x42

    assert mmu[0xFE00] == 0xFF
    assert mmu.memory[0xFE00] == 0x00


def test_mmu_blocks_cpu_access_to_vram_when_locked() -> None:
    mmu = MMU()
    mmu.set_ppu_bus_access(oam_locked=False, vram_locked=True)

    mmu[0x8000] = 0x77

    assert mmu[0x8000] == 0xFF
    assert mmu.memory[0x8000] == 0x00


def test_mmu_unblocks_cpu_access_when_ppu_bus_open() -> None:
    mmu = MMU()
    mmu.set_ppu_bus_access(oam_locked=False, vram_locked=False)

    mmu[0xFE00] = 0x11
    mmu[0x8000] = 0x22

    assert mmu[0xFE00] == 0x11
    assert mmu[0x8000] == 0x22


def test_mmu_bank_switch_write_does_not_crash_when_cart_reports_zero_banks() -> None:
    cart = Cart("roms/hello.gb")
    mmu = MMU(cart)

    # Reproduces old crash path where `value % cart.banks` raised ZeroDivisionError.
    cart.banks = 0
    mmu[0x2000] = 0x01

    assert mmu[0x4000] == cart.rom[0x4000]


def test_mmu_bank_zero_request_maps_to_bank_one() -> None:
    cart = Cart("roms/hello.gb")
    mmu = MMU(cart)

    mmu.load_bank(0)

    assert mmu[0x4000] == cart.rom[0x4000]
