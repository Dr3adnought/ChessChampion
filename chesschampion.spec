# PyInstaller spec for ChessChampion Windows builds.
# Build command: pyinstaller --noconfirm --clean chesschampion.spec

from pathlib import Path

spec_path = globals().get("__file__") or globals().get("SPEC") or "chesschampion.spec"
PROJECT_ROOT = Path(spec_path).resolve().parent

block_cipher = None

added_assets = [
    (str(PROJECT_ROOT / "assets"), "assets"),
]

a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=added_assets,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ChessChampion",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ChessChampion",
)
