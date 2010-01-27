!define PRODUCT "SwarmPlayer"
!define VERSION "1.1.0"
!define LIBRARYNAME "Tribler"


!include "MUI.nsh"

;--------------------------------
;Configuration

;General
 Name "${PRODUCT} ${VERSION}"
OutFile "${PRODUCT}_${VERSION}.exe"

;Folder selection page
InstallDir "$PROGRAMFILES\${PRODUCT}"
 
;Remember install folder
InstallDirRegKey HKCU "Software\${PRODUCT}" ""

;
; Uncomment for smaller file size
;
SetCompressor "lzma"
;
; Uncomment for quick built time
;
;SetCompress "off"

CompletedText "Installation completed. Thank you for choosing ${PRODUCT}"

BrandingText "${PRODUCT}"

;--------------------------------
;Modern UI Configuration

!define MUI_ABORTWARNING
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "heading.bmp"

;--------------------------------
;Pages

!define MUI_LICENSEPAGE_RADIOBUTTONS
!define MUI_LICENSEPAGE_RADIOBUTTONS_TEXT_ACCEPT "I accept"
!define MUI_LICENSEPAGE_RADIOBUTTONS_TEXT_DECLINE "I decline"
;   !define MUI_FINISHPAGE_RUN "$INSTDIR\swarmplayer.exe"

!insertmacro MUI_PAGE_LICENSE "binary-LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;!insertmacro MUI_DEFAULT UMUI_HEADERIMAGE_BMP heading.bmp"

;--------------------------------
;Languages

!insertmacro MUI_LANGUAGE "English"
 
;--------------------------------
;Language Strings

;Description
LangString DESC_SecMain ${LANG_ENGLISH} "Install ${PRODUCT}"
LangString DESC_SecDesk ${LANG_ENGLISH} "Create Desktop Shortcuts"
LangString DESC_SecStart ${LANG_ENGLISH} "Create Start Menu Shortcuts"
LangString DESC_SecDefaultTStream ${LANG_ENGLISH} "Associate .tstream files with ${PRODUCT}"
LangString DESC_SecDefaultTorrent ${LANG_ENGLISH} "Associate .torrent files with ${PRODUCT}"

;--------------------------------
;Installer Sections

Section "!Main EXE" SecMain
 SectionIn RO
 SetOutPath "$INSTDIR"
 File *.txt
 File swarmplayer.exe.manifest
 File swarmplayer.exe
 File ffmpeg.exe
 File /r vlc
 File *.bat
 Delete "$INSTDIR\*.pyd"
 File *.pyd
 Delete "$INSTDIR\python*.dll"
 Delete "$INSTDIR\wx*.dll"
 File *.dll
 Delete "$INSTDIR\*.zip"
 File *.zip
 CreateDirectory "$INSTDIR\${LIBRARYNAME}"
 CreateDirectory "$INSTDIR\${LIBRARYNAME}\Core"
 SetOutPath "$INSTDIR\${LIBRARYNAME}\Core"
 File ${LIBRARYNAME}\Core\*.txt
 CreateDirectory "$INSTDIR\${LIBRARYNAME}\Core\Statistics"
 SetOutPath "$INSTDIR\${LIBRARYNAME}\Core\Statistics"
 File ${LIBRARYNAME}\Core\Statistics\*.txt
 File ${LIBRARYNAME}\Core\Statistics\*.sql
 CreateDirectory "$INSTDIR\${LIBRARYNAME}\Images"
 SetOutPath "$INSTDIR\${LIBRARYNAME}\Images"
 File ${LIBRARYNAME}\Images\*.*
 CreateDirectory "$INSTDIR\${LIBRARYNAME}\Video"
 CreateDirectory "$INSTDIR\${LIBRARYNAME}\Video\Images"
 SetOutPath "$INSTDIR\${LIBRARYNAME}\Video\Images"
 File ${LIBRARYNAME}\Video\Images\*.*
 CreateDirectory "$INSTDIR\${LIBRARYNAME}\Lang"
 SetOutPath "$INSTDIR\${LIBRARYNAME}\Lang"
 IfFileExists user.lang userlang
 File ${LIBRARYNAME}\Lang\*.*
 userlang:
 File /x user.lang ${LIBRARYNAME}\Lang\*.*
 SetOutPath "$INSTDIR"
 WriteRegStr HKEY_LOCAL_MACHINE "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" "DisplayName" "${PRODUCT} (remove only)"
 WriteRegStr HKEY_LOCAL_MACHINE "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" "UninstallString" "$INSTDIR\Uninstall.exe"

; Now writing to KHEY_LOCAL_MACHINE only -- remove references to uninstall from current user
 DeleteRegKey HKEY_CURRENT_USER "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}"
; Remove old error log if present
 Delete "$INSTDIR\swarmplayer.exe.log"

 WriteUninstaller "$INSTDIR\Uninstall.exe"

 ; Add an application to the firewall exception list - All Networks - All IP Version - Enabled
 SimpleFC::AddApplication "Tribler" "$INSTDIR\${PRODUCT}.exe" 0 2 "" 1
 ; Pop $0 ; return error(1)/success(0)

SectionEnd


Section "Desktop Icons" SecDesk
   CreateShortCut "$DESKTOP\${PRODUCT}.lnk" "$INSTDIR\${PRODUCT}.exe" ""
SectionEnd


Section "Startmenu Icons" SecStart
   CreateDirectory "$SMPROGRAMS\${PRODUCT}"
   CreateShortCut "$SMPROGRAMS\${PRODUCT}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
   CreateShortCut "$SMPROGRAMS\${PRODUCT}\${PRODUCT}.lnk" "$INSTDIR\${PRODUCT}.exe" "" "$INSTDIR\${PRODUCT}.exe" 0
SectionEnd


Section "Make Default For .tstream" SecDefaultTStream
   WriteRegStr HKCR .tstream "" tstream
   WriteRegStr HKCR .tstream "Content Type" application/x-tribler-stream
   WriteRegStr HKCR "MIME\Database\Content Type\application/x-tribler-stream" Extension .tstream
   WriteRegStr HKCR tstream "" "TSTREAM File"
   WriteRegBin HKCR tstream EditFlags 00000100
   WriteRegStr HKCR "tstream\shell" "" open
   WriteRegStr HKCR "tstream\shell\open\command" "" '"$INSTDIR\${PRODUCT}.exe" "%1"'
   WriteRegStr HKCR "tstream\DefaultIcon" "" "$INSTDIR\${LIBRARYNAME}\Images\SwarmPlayerIcon.ico"
SectionEnd


Section /o "Make Default For .torrent" SecDefaultTorrent
   ; Delete ddeexec key if it exists
   DeleteRegKey HKCR "bittorrent\shell\open\ddeexec"
   WriteRegStr HKCR .torrent "" bittorrent
   WriteRegStr HKCR .torrent "Content Type" application/x-bittorrent
   WriteRegStr HKCR "MIME\Database\Content Type\application/x-bittorrent" Extension .torrent
   WriteRegStr HKCR bittorrent "" "TORRENT File"
   WriteRegBin HKCR bittorrent EditFlags 00000100
   WriteRegStr HKCR "bittorrent\shell" "" open
   WriteRegStr HKCR "bittorrent\shell\open\command" "" '"$INSTDIR\${PRODUCT}.exe" "%1"'
   WriteRegStr HKCR "bittorrent\DefaultIcon" "" "$INSTDIR\${LIBRARYNAME}\Images\torrenticon.ico"
SectionEnd



;--------------------------------
;Descriptions

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
!insertmacro MUI_DESCRIPTION_TEXT ${SecDesk} $(DESC_SecDesk)
!insertmacro MUI_DESCRIPTION_TEXT ${SecStart} $(DESC_SecStart)
;!insertmacro MUI_DESCRIPTION_TEXT ${SecLang} $(DESC_SecLang)
!insertmacro MUI_DESCRIPTION_TEXT ${SecDefaultTStream} $(DESC_SecDefaultTStream)
!insertmacro MUI_DESCRIPTION_TEXT ${SecDefaultTorrent} $(DESC_SecDefaultTorrent)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section "Uninstall"

 RMDir /r "$INSTDIR"

 Delete "$DESKTOP\${PRODUCT}.lnk"
 Delete "$SMPROGRAMS\${PRODUCT}\*.*"
 RmDir  "$SMPROGRAMS\${PRODUCT}"

 DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\${PRODUCT}"
 DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}"

 ; Remove an application from the firewall exception list
 SimpleFC::RemoveApplication "$INSTDIR\${PRODUCT}.exe"
 ; Pop $0 ; return error(1)/success(0)

SectionEnd


;--------------------------------
;Functions Section

Function .onInit
  System::Call 'kernel32::CreateMutexA(i 0, i 0, t "SwarmPlayer") i .r1 ?e' 

  Pop $R0 

  StrCmp $R0 0 +3 

  MessageBox MB_OK "The installer is already running."

  Abort 
FunctionEnd
