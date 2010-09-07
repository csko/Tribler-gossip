REM @echo off
set LIBRARYNAME=Tribler

set PYTHONHOME=\Python254
REM Arno: Add . to find our core (py 2.5)
set PYTHONPATH=.;%PYTHONHOME%
echo PYTHONPATH SET TO %PYTHONPATH%

set NSIS="\Program Files\NSIS\makensis.exe"

REM ----- Check for Python and essential site-packages

IF NOT EXIST %PYTHONHOME%\python.exe (
  echo .
  echo Could not locate Python in %PYTHONHOME%.
  echo Please modify this script or install python [www.python.org]
  exit /b
)

IF NOT EXIST %PYTHONHOME%\Lib\site-packages\wx-*-unicode (
  echo .
  echo Could not locate wxPython in %PYTHONHOME%\Lib\site-packages.
  echo Please modify this script or install wxPython [www.wxpython.org]
  exit /b
)

IF NOT EXIST %PYTHONHOME%\Lib\site-packages\py2exe (
  echo .
  echo Could not locate py2exe in %PYTHONHOME%\Lib\site-packages.
  echo Please modify this script or install wxPython [www.py2exe.org]
  exit /b
)

REM ----- Check for NSIS installer

IF NOT EXIST %NSIS% (
  echo .
  echo Could not locate the NSIS installer at %NSIS%.
  echo Please modify this script or install NSIS [nsis.sf.net]
  exit /b
)

REM ----- Clean up

call clean.bat

REM ----- Build

REM Arno: When adding files here, make sure tribler.nsi actually
REM packs them in the installer .EXE

REM Diego: building the deepest dir we get all of them.
mkdir dist\installdir\bgprocess\%LIBRARYNAME%\Images

%PYTHONHOME%\python.exe -O %LIBRARYNAME%\Plugin\Build\Win32\setupBGexe.py py2exe

REM Arno: Move py2exe results to installdir
move dist\*.* dist\installdir\bgprocess
copy %LIBRARYNAME%\Images\SwarmPluginIcon.ico dist\installdir\bgprocess\%LIBRARYNAME%\Images

xcopy vlc4plugin\* dist\installdir /E /I

REM Riccardo:  move the files needed for the WebUI
xcopy %LIBRARYNAME%\WebUI dist\installdir\bgprocess\%LIBRARYNAME%\WebUI /S /I
del dist\installdir\bgprocess\%LIBRARYNAME%\WebUI\*.py

REM Diego: replace vlc *.txt with P2P-Next License.txt
del dist\installdir\*.txt
type %LIBRARYNAME%\ns-LICENSE.txt %LIBRARYNAME%\binary-LICENSE-postfix.txt > %LIBRARYNAME%\binary-LICENSE.txt
copy %LIBRARYNAME%\binary-LICENSE.txt dist\installdir

copy %LIBRARYNAME%\Plugin\Build\Win32\heading.bmp dist\installdir
REM TODO Diego: manifest?
copy %LIBRARYNAME%\Plugin\Build\Win32\swarmplugin_FX_only.nsi dist\installdir
REM copy %LIBRARYNAME%\Plugin\Build\Win32\swarmplugin.exe.manifest dist\installdir

copy %PYTHONHOME%\Lib\site-packages\wx-2.8-msw-unicode\wx\msvcp71.dll dist\installdir\bgprocess

copy reset*.bat dist\installdir


cd dist\installdir

REM Arno: Win7 gives popup if SwarmEngine is not signed
"C:\Program Files\Microsoft Platform SDK for Windows Server 2003 R2\Bin\signtool.exe" sign /f c:\build\certs\swarmplayerprivatekey.pfx /p "" /d "SwarmPlugin for Internet Explorer and Firefox" /du "http://www.pds.ewi.tudelft.nl/code.html" /t "http://timestamp.verisign.com/scripts/timestamp.dll" bgprocess\SwarmEngine.exe


:makeinstaller
%NSIS% swarmplugin_FX_only.nsi

rename SwarmPlugin_*.exe SwarmPlugin_FX_*.exe
move SwarmPlugin_FX_*.exe ..
cd ..
REM Diego : sign SwarmPlugin_*.exe
"C:\Program Files\Microsoft Platform SDK for Windows Server 2003 R2\Bin\signtool.exe" sign /f c:\build\certs\swarmplayerprivatekey.pfx /p "" /d "SwarmPlugin for Firefox" /du "http://www.pds.ewi.tudelft.nl/code.html" /t "http://timestamp.verisign.com/scripts/timestamp.dll" "SwarmPlugin_FX*.exe"
cd ..
