# -*- mode: python -*-

a = Analysis(['augur\\augur.py'],
             pathex=['C:\\Users\\jack\\Documents\\Scripts\\AugurProject\\augur'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)

a.datas += [('augur_ctl', 'augur_ctl', 'DATA')]
a.datas += [('augur.html', 'augur\\augur.html', 'DATA')]
a.datas += [('README.rst', 'README.rst', 'DATA')]
a.datas += [('LICENSE.txt', 'LICENSE.txt', 'DATA')]

pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='augur.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True)

static_tree = Tree('augur\\static', prefix='static')
core_tree = Tree('augur\\core', prefix='core')

dist = COLLECT(exe,
               a.binaries,
               a.datas,
               static_tree,
               core_tree,
               strip=None,
               upx=True,
               name='augur')
