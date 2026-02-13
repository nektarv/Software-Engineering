#!/usr/bin/env bash

set -e   # αν κάτι σπάσει → σταματάει
set -o pipefail

CLI="se2534"

NOW=$(date '+%Y-%m-%d %H:%M')
END=$(date -v+15M '+%Y-%m-%d %H:%M')
start=$(date -v+5M '+%Y-%m-%d %H:%M')


echo "================================"
echo " Testing status codes 200"
echo "================================"

echo "============================"
echo " Healthcheck "
echo "============================"
 
$CLI healthcheck

echo "============================"
echo " Reset points"
echo "============================"

$CLI resetpoints

echo "============================"
echo " Add points"
echo "============================"

$CLI addpoints --source test.csv


echo "============================"
echo " Points"
echo "============================"

$CLI points
$CLI points --status available
$CLI points --status charging --format json
$CLI points --status offline --format csv


echo "============================"
echo " Point"
echo "============================"

$CLI point --id 1

echo "============================"
echo " Reserve"
echo "============================"

$CLI reserve --id 1
$CLI reserve --id 6 --minutes 30
$CLI reserve --id 7 --minutes 60


echo "============================"
echo " New session"
echo "============================"

$CLI newsession --id 1 --starttime "$start" --endtime "$END" --startsoc 10 --endsoc 50 --totalkwh 10.0 --kwhprice 0.50 --amount 5.0 
$CLI newsession --id 6 --starttime "$start" --endtime "$END" --startsoc 10 --endsoc 50 --totalkwh 10.0 --kwhprice 0.50 --amount 5.0 
$CLI newsession --id 7 --starttime "$start" --endtime "$END" --startsoc 10 --endsoc 50 --totalkwh 10.0 --kwhprice 0.50 --amount 5.0 

echo "============================"
echo " Sessions"
echo "============================"

$CLI sessions --id 1 --from 2026/01/15 --to 2026/02/17  
$CLI sessions --id 6 --from 2025-11-20 --to 2026-12-20 --format json
$CLI sessions --id 7 --from 20251126 --to 20260701 --format csv 


echo "============================"
echo " Update point"
echo "============================"

$CLI updpoint --id 4 --status malfunction
$CLI updpoint --id 5 --price 0.5
$CLI updpoint --id 6 --status charging  --price 0.3

echo "============================"
echo " Point status"
echo "============================"
 
$CLI pointstatus --id 1 --from 2025/11/20 --to 2026/12/15 --format json 
$CLI pointstatus --id 6 --from 2025-12-01 --to 2026-12-31 --format csv


echo "============================"
echo " End of tests"
echo "============================"
