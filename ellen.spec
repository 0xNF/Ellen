# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['src\\server.py'],
             pathex=['C:\\Users\\nflower\\Documents\\NickDocs\\projects\\Ellen'],
             binaries=[],
             datas=[
                 ('./src/lib', 'lib'),
                 ('./src/static', 'static'),
                 ('./src/templates', 'templates')
                ],
             hiddenimports=['pkg_resources.py2_warn'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='ellen',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
