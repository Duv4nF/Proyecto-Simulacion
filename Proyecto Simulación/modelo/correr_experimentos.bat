@echo off
rem Corre los cuatro experimentos BehaviorSpace sin abrir la interfaz (Windows).
rem Uso: correr_experimentos.bat "C:\Program Files\NetLogo 6.4.0" [hilos]
set NETLOGO=%~1
if "%NETLOGO%"=="" set NETLOGO=C:\Program Files\NetLogo 6.4.0
set HILOS=%~2
if "%HILOS%"=="" set HILOS=2
set AQUI=%~dp0
set SALIDA=%AQUI%..\datos\resultados
if not exist "%SALIDA%" mkdir "%SALIDA%"
for %%E in (publicidad_x_densidad topologia_x_publicidad duracion_campana calibracion_pew) do (
  echo == %%E
  "%NETLOGO%\netlogo-headless.bat" --model "%AQUI%difusion_innovacion.nlogo" --experiment %%E --table "%SALIDA%\%%E.csv" --threads %HILOS%
)
echo listo: %SALIDA%
