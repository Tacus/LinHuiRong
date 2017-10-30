@echo off
if not "%1"=="am_admin" (powershell start -verb runas '%0' am_admin & exit)
netsh interface ipv4 set dnsservers "ÒÔÌ«Íø" dhcp
