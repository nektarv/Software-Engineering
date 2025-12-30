#!/usr/bin/env bash

set -e   # αν κάτι σπάσει → σταματάει
set -o pipefail

CLI="se2534"

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
$CLI points --status reserved --format csv

echo "============================"
echo " Point"
echo "============================"

$CLI point --id 1

echo "============================"
echo " Reserve"
echo "============================"

$CLI reserve --id 2 
$CLI reserve --id 3 --minutes 30

echo "============================"
echo " Update point"
echo "============================"

$CLI updpoint --id 4 --status malfunction
$CLI updpoint --id 5 --price 0.5
$CLI updpoint --id 6 --status charging  --price 0.3

echo "============================"
echo " New session"
echo "============================"

$CLI newsession --id 147 --starttime "2025-12-20 21:15" --endtime "2025-12-20 21:35" --startsoc 10 --endsoc 50 --totalkwh 10.0 --kwhprice 0.50 --amount 5.0 

echo "============================"
echo " Sessions"
echo "============================"

$CLI sessions --id 91 --from 2025/12/15 --to 2025/12/17  
$CLI sessions --id 149 --from 2025-11-20 --to 2025-12-20 --format json
$CLI sessions --id 78 --from 20251201 --to 20251231 --format csv 

echo "============================"
echo " Point status"
echo "============================"
 
$CLI pointstatus --id 33 --from 2025/11/20 --to 2025/12/15 --format json 
$CLI pointstatus --id 51 --from 2025-12-01 --to 2025-12-31 --format csv
$CLI pointstatus --id 145 --from 20251201 --to 20251231

echo "============================"
echo " End of tests"
echo "============================"
