#!/usr/bin/env bash

set -e   # αν κάτι σπάσει → σταματάει
set -o pipefail

CLI="se2534"

echo "=================================================================="
echo " Testing status codes missing 204 and 400"
echo "=================================================================="

echo "============================"
echo " Point"
echo "============================"

$CLI point --id 16543
$CLI point --id charge

echo "============================"
echo " Reserve"
echo "============================"

$CLI reserve --id 35432 
$CLI reserve --id charge

echo "============================"
echo " Update point"
echo "============================"

$CLI updpoint --id 65421 --status charging  
$CLI updpoint --id charge --price 0.3

echo "============================"
echo " New session"
echo "============================"

$CLI newsession --id charge --starttime "2025-12-20 21:15" --endtime "2025-12-20 21:35" --startsoc 10 --endsoc 50 --totalkwh 10.0 --kwhprice 0.50 --amount 5.0 

echo "============================"
echo " Sessions"
echo "============================"

$CLI sessions --id 6543 --from 2025-11-20 --to 2025-12-20 --format json
$CLI sessions --id charge --from 2025-11-20 --to 2025-12-20 --format json

echo "============================"
echo " Point status"
echo "============================"
 
$CLI pointstatus --id 59861 --from 2025-12-01 --to 2025-12-31 --format csv
$CLI pointstatus --id charge --from 2025-12-01 --to 2025-12-31 --format csv

echo "============================"
echo " End of tests"
echo "============================"
