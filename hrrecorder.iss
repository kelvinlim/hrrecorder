; HR Recorder Inno Setup Script
; Builds a Windows installer for the HR Recorder application

#define MyAppName "HR Recorder"
#define MyAppVersion "1.0.17"
#define MyAppPublisher "Kelvin Lim"
#define MyAppURL "https://github.com/kelvinlim/hrrecorder"
#define MyAppExeName "hrrecorder.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application
AppId={{A8B7C6D5-E4F3-2G1H-0I9J-8K7L6M5N4O3P}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=dist
OutputBaseFilename=HRRecorder-Installer
SetupIconFile=hrrecorder.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
CloseApplications=yes
CloseApplicationsFilter=hrrecorder.exe
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\hrrecorder.exe"; DestDir: "{app}"; Flags: ignoreversion restartreplace; BeforeInstall: CloseApp
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CloseApp();
var
  ResultCode: Integer;
begin
  // Try to close the app gracefully using taskkill
  Exec('taskkill.exe', '/F /IM hrrecorder.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
