#define MyAppName "Augur"
#define MyAppVersion "0.1.1"
#define MyAppPublisher "Augur Project"
#define MyAppURL "http://www.augur.net/"
#define MyAppExeName "augur.exe"
#define SourceDir "C:\Users\jack\Documents\Scripts\AugurProject\augur\dist\augur\"

[Setup]
AppId={{1CA950F0-C451-4688-9BC5-D25842578076}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile={#SourceDir}LICENSE.txt
OutputBaseFilename={#MyAppName}_{#MyAppVersion}
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 0,6.1

[Files]
Source: "{#SourceDir}augur.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}_bsddb.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}_ctypes.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}_hashlib.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}_multiprocessing.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}_socket.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}_ssl.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}_win32sysloader.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}augur.exe.manifest"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}augur.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}augur_ctl"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}bz2.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}cdecimal.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}gevent._semaphore.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}gevent._util.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}gevent.ares.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}gevent.core.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}greenlet.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}libiomp5md.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}markupsafe._speedups.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}mfc90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}mfc90u.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}mfcm90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}mfcm90u.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}Microsoft.VC90.CRT.manifest"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}Microsoft.VC90.MFC.manifest"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}msvcm90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}msvcp90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}msvcr90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}numpy.core._dotblas.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}numpy.core.multiarray.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}numpy.core.scalarmath.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}numpy.core.umath.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}numpy.fft.fftpack_lite.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}numpy.lib._compiled_base.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}numpy.linalg._umath_linalg.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}numpy.linalg.lapack_lite.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}numpy.random.mtrand.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}pyexpat.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}python27.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}pythoncom27.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}pywintypes27.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}README.rst"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}select.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}simplejson._speedups.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}unicodedata.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}win32api.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}win32pdh.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}win32pipe.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}win32trace.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}win32ui.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}win32wnet.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}include\*"; DestDir: "{app}\include"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}core\dist\core\*"; DestDir: "{app}\core\dist\core"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

