#!/bin/bash
#
# "stop lms-service gunicorn"
echo 'stop lms-service gunicorn'
pstree -ap|grep lms-service

if [ ! -f gunicorn.pid ] ; then
   echo  'lms-service is not running yet.'
   exit -1
fi
echo ''
gpid=`cat gunicorn.pid`
echo 'kill -9' $gpid
kill -9 $gpid

if [ $? -ne 0 ] ;  then
   exit -1
fi

gp_total=0
for n in {0..60}
do
	`sleep 1`
	echo -n '#'
	gp_total=`pstree -ap|grep lms-service|wc -l`
	if [ $gp_total -eq 0 ]
	then
		break
	fi
done

echo ''
echo lms-service gunicorn: ${gpid} is killed !
rm gunicorn.pid

echo ''
pstree -ap|grep lms-service

echo ''
gp_total=`pstree -ap|grep lms-service|wc -l`
if [ $gp_total -eq 0 ] ;  then
   echo 'lms-service gunicorn shut down successfully!'
fi