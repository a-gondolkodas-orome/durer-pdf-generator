@echo off

pushd %~dp0

poppler-0.68.0/bin/pdfunite.exe %*

popd
