#define AppName "FaccuPoint"
#ifndef AppVersion
#define AppVersion "1.0.0"
#endif
#define AppPublisher "Jackson Matiazzi"
#define AppExeName "FaccuPoint.exe"

[Setup]
AppId={{B940D16F-0C24-4C48-9E45-2FB5031C4F53}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableDirPage=no
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=FaccuPoint-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=..\frontend\assets\image\logoF.ico
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""faccupoint.exe"""; Flags: runhidden
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""FaccuPoint - alunos 8081"""; Flags: runhidden
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""FaccuPoint - alunos 8081"" dir=in action=allow program=""{app}\{#AppExeName}"" protocol=TCP localport=8081 profile=private,public remoteip=localsubnet"; Flags: runhidden
Filename: "{app}\{#AppExeName}"; Description: "Abrir o FaccuPoint"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""FaccuPoint - alunos 8081"" program=""{app}\{#AppExeName}"""; Flags: runhidden
