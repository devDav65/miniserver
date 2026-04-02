# build.spec
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static',    'static'),
        ('config.json', '.'),
    ],
    hiddenimports=[
        'flask', 'werkzeug', 'qrcode', 'PIL',
        'zeroconf', 'ifaddr', 'engineio', 'jinja2',
    ],
    hookspath=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name='Droply',
    debug=False,
    console=False,       # pas de terminal noir qui s'ouvre
    onefile=True,        # tout dans un seul fichier
)
