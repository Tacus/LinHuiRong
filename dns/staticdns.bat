@echo off
if not "%1"=="am_admin" (powershell start -verb runas '%0' am_admin & exit)
netsh interface ipv4 add dnsservers "ÒÔÌ«Íø" 114.114.114.114 index=1
netsh interface ipv4 add dnsservers "ÒÔÌ«Íø" 223.5.5.5 index=2
