#define MyAppName "BulletinPro_Prof"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Ecole"
#define MyAppExeName "BulletinPro_Prof.exe"

[Setup]
AppId={{8F9A3B2C-1D4E-5F6A-7B8C-9D0E1F2A3B4C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\dist\installers
OutputBaseFilename=BulletinPro_Setup_{#MyAppVersion}
; *** SUPPRIMÉ SetupIconFile car le fichier n'existe pas encore ***
; SetupIconFile sera géré par le package lui-même
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Creer raccourci bureau"

[Files]
; Copier tout le contenu du package
Source: "..\dist\BulletinPro_Prof_Package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
; Utiliser l'icône depuis le package installé
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent
