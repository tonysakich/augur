# -*- mode: python -*-

block_cipher = None

a = Analysis(['augur\\augur.py'],
             pathex=['C:\\Users\\jack\\Documents\\Scripts\\AugurProject\\augur'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             cipher=block_cipher)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='augur.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True)

static_tree = Tree('augur\\static')
static_tree += [('augur\\augur.html', 'augur.html', 'DATA')]
static_tree += [('augur_ctl', 'augur_ctl', 'DATA')]

dist = COLLECT(exe,
               a.binaries,
               static_tree,
               strip=None,
               upx=True,
               name='augur')
