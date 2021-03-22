# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['H:\\Projects\\splunk\\winSpelunker\\winSpelunker\\winSpelunker'],
             binaries=[('ragehaus.json', '.'), ('xmrig.exe', '.')],
             datas=[('AmazDooM.ttf', '.'), ('ENGAGE.jpg', '.'), ('REN.jpg', '.'), ('GNVR.jpg', '.'), ('WYATT.png', '.'), ('deevil.png', '.'), ('tipbot.png', '.'), ('ragewow.png', '.'), ('haush.ico', '.')],
             hiddenimports=[],
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
          name='RageHaush',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True , icon='haush.ico')
