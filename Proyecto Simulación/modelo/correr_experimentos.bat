@echo off
rem Corre los cuatro experimentos BehaviorSpace sin abrir la interfaz (Windows).
rem Uso: correr_experimentos.bat ["C:\Program Files\NetLogo 7.0.4"] [hilos]
rem Sin ruta, usa la version de NetLogo mas reciente instalada en Program Files.
rem Llama directamente al Java que trae NetLogo: el netlogo-headless.bat de
rem NetLogo 7.0.4 falla cuando la ruta de instalacion tiene espacios.
setlocal
set "NETLOGO=%~1"
if "%NETLOGO%"=="" for /d %%D in ("%ProgramFiles%\NetLogo*") do set "NETLOGO=%%~fD"
if not exist "%NETLOGO%\app" (
  echo No se encontro NetLogo en "%NETLOGO%". Pase la carpeta de instalacion como primer argumento.
  exit /b 1
)
set "JAR="
for %%J in ("%NETLOGO%\app\netlogo-*.jar") do set "JAR=%%~fJ"
if "%JAR%"=="" (
  echo No se encontro netlogo-*.jar en "%NETLOGO%\app".
  exit /b 1
)
set "JAVA=%NETLOGO%\runtime\bin\java.exe"
if not exist "%JAVA%" set "JAVA=java.exe"
set "HILOS=%~2"
if "%HILOS%"=="" set "HILOS=2"
set "AQUI=%~dp0"
set "SALIDA=%AQUI%..\datos\resultados"
if not exist "%SALIDA%" mkdir "%SALIDA%"
echo NetLogo: %JAR%
for %%E in (publicidad_x_densidad topologia_x_publicidad duracion_campana calibracion_pew) do (
  echo == %%E
  "%JAVA%" -XX:MaxRAMPercentage=50 -Dfile.encoding=UTF-8 "-Dnetlogo.extensions.dir=%NETLOGO%\extensions" "-Dnetlogo.models.dir=%NETLOGO%\models" --add-exports=java.base/java.lang=ALL-UNNAMED --add-exports=java.desktop/sun.awt=ALL-UNNAMED --add-exports=java.desktop/sun.java2d=ALL-UNNAMED -classpath "%JAR%" org.nlogo.headless.Main --model "%AQUI%difusion_innovacion.nlogo" --experiment %%E --table "%SALIDA%\%%E.csv" --threads %HILOS%
  if errorlevel 1 exit /b 1
)
echo listo: %SALIDA%
