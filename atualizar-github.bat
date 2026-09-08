@echo off
chcp 65001 >nul
echo ======================================================
echo   Atualizar o projeto no GitHub
echo ======================================================
echo.
cd /d "%~dp0"

echo Verificando o que mudou...
git status
echo.

set /p MENSAGEM="Descreva em poucas palavras o que voce mudou: "

if "%MENSAGEM%"=="" (
    echo.
    echo Voce nao digitou nada. Cancelando.
    pause
    exit /b
)

echo.
echo Salvando as mudancas...
git add .
git commit -m "%MENSAGEM%"

echo.
echo Enviando para o GitHub...
git push

echo.
echo ======================================================
echo   Pronto! Confira em:
echo   https://github.com/Catarinacarneiro123/classificador-cnae-reforma
echo ======================================================
pause
