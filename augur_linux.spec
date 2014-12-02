# -*- mode: python -*-

a = Analysis(['augur/augur.py'],
             pathex=['/home/jack/src/augur'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)

a.datas += [('augur_ctl', 'augur_ctl', 'DATA')]
a.datas += [('augur.html', 'augur/augur.html', 'DATA')]
a.datas += [('README.rst', 'README.rst', 'DATA')]
a.datas += [('LICENSE.txt', 'LICENSE.txt', 'DATA')]

pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='augur',
          debug=False,
          strip=None,
          upx=True,
          console=True)

static_tree = Tree('augur/static', prefix='static')
core_tree = Tree('../frozen-core/dist/core', prefix='core')

dist = COLLECT(exe,
               a.binaries,
               a.datas,
               static_tree,
               core_tree,
               strip=None,
               upx=True,
               name='augur')
