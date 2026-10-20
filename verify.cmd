@echo off
setlocal
pushd "%~dp0backend"
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 goto failed
popd
pushd "%~dp0frontend"
call npm.cmd test
if errorlevel 1 goto failed
call npm.cmd run lint
if errorlevel 1 goto failed
call npm.cmd run typecheck
if errorlevel 1 goto failed
call npm.cmd run build
if errorlevel 1 goto failed
popd
echo All checks passed.
exit /b 0
:failed
popd
echo Verification failed. Review the error above.
exit /b 1
