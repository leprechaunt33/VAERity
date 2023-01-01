# -*- mode: python ; coding: utf-8 -*-

from kivy_deps import sdl2, glew
import pkg_resources

# Helper function to make iter_entry_points work e.g. for vaex
# copied and modified from https://github.com/pyinstaller/pyinstaller/issues/3050
def prepare_entrypoints(ep_packages):

    hook_ep_packages = dict()
    hiddenimports = set()
    runtime_hooks = list()

    if not ep_packages:
        return list(hiddenimports), runtime_hooks

    for ep_package in ep_packages:
        for ep in pkg_resources.iter_entry_points(ep_package):
            if 'astro' in ep.module_name:
                continue
            if ep_package in hook_ep_packages:
                package_entry_point = hook_ep_packages[ep_package]
            else:
                package_entry_point = []
                hook_ep_packages[ep_package] = package_entry_point
            package_entry_point.append("{} = {}:{}".format(ep.name, ep.module_name, ep.attrs[0]))
            hiddenimports.add(ep.module_name)

    try:
        os.mkdir('./generated')
    except FileExistsError:
        pass

    with open("./generated/pkg_resources_hook.py", "w") as f:
        f.write("""# Runtime hook generated from spec file to support pkg_resources entrypoints.
ep_packages = {}

if ep_packages:
    import pkg_resources
    default_iter_entry_points = pkg_resources.iter_entry_points

    def hook_iter_entry_points(group, name=None):
        if group in ep_packages and ep_packages[group]:
            eps = ep_packages[group]
            for ep in eps:
                parsedEp = pkg_resources.EntryPoint.parse(ep)
                parsedEp.dist = pkg_resources.Distribution()
                yield parsedEp
        else:
            return default_iter_entry_points(group, name)

    pkg_resources.iter_entry_points = hook_iter_entry_points
""".format(hook_ep_packages))

    runtime_hooks.append("./generated/pkg_resources_hook.py")

    return list(hiddenimports), runtime_hooks

# List of packages that should have their "Distutils entrypoints" included.
ep_packages = ["vaex.memory.tracker", 'vaex.dataset.opener']

hiddenimports, runtime_hooks = prepare_entrypoints(ep_packages)
hiddenimports.append('frozendict')
hiddenimports.append('vaex.viz')
hiddenimports.extend(['win32file','win32timezone'])
block_cipher = None

print(hiddenimports)
print(runtime_hooks)
input("Press a key to continue")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=['astropy','bokeh'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.datas += a.binaries
a.binaries=[]
a.onefile=False

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='vaerity',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    strip=False,
    upx=False,
    upx_exclude=[],
    name='vaerity',
)
