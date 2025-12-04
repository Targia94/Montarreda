[Setup]
AppName=Gestione Timbrature
AppVersion=1.0
DefaultDirName={pf}\GestioneTimbrature
DefaultGroupName=Gestione Timbrature
OutputDir=.
OutputBaseFilename=SetupTimbrature
Compression=lzma2
SolidCompression=yes

[Files]
Source: "C:\Users\Giacomo\Documents\Personale\MONTARREDA\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Gestione Timbrature"; Filename: "{app}\start.bat"

[Run]
Filename: "{app}\start.bat"; Description: "Avvia il programma"; Flags: nowait postinstall skipifsilent
