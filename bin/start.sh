#!/bin/bash
#
# start lms-service"

cd /apps/lms/lms-service
echo LMS-SERVICE-HOME: $PWD
echo 'start lms-service gunicorn'
echo 'gunicorn -c gunicorn.conf app:__hug_wsgi__ &'
gunicorn -c /apps/lms/lms-service/gunicorn.conf app:__hug_wsgi__ &

`sleep 5`

workers_total=5
gp_total=0
for n in {0..60}
do
	`sleep 1`
	echo -n '#'
	gp_total=`pstree -ap|grep lms-service|wc -l`
	if [ $gp_total -gt $workers_total ]
	then
		break
	fi
done

echo ''
echo '/############################################################################\'
echo '           `.----``..-------..``.----.                                        '                                  
echo '          :/:::::--:---------:--::::://.                                      '
echo '         .+::::----##/-/oo+:-##----:::://                                     '
echo '         `//::-------/oosoo-------::://.         ##      ##     ##    ####### '
echo '           .-:------./++o/o-.------::-`   ```    ##     ####   ####  ##       '
echo '              `----.-./+o+:..----.     `.:///.   ##    ##  ## ##  ##  ##      '
echo '    ```        `----.-::::::------  `.-:::://.   ##   ##    ####   ##   ####  '
echo '   ://::--.``` -:``...-----...` `:--::::::-.`    ##  ##      ##     ##     ## '
echo '   :/:::::::::-:-     `````      .:::::-.`       ########   ####    ########  '
echo '    ``.--:::::::.                .:::.`                                       '
echo '          ``..::.                .::           LEADS MANAGEMENT SYSTEM SERVICE'
echo '              ::-                .:-                                          '
echo '              -::`               ::-                    VERSION 1.0.8         '
echo '              `::-              -::`                                          '
echo '               -::-`           -::-                                           '
echo '\############################################################################/'
echo ''

pstree -ap|grep lms-service
echo ''

gp_total=`pstree -ap|grep lms-service|wc -l`
if [ $gp_total -gt $workers_total ] ;  then
   echo 'lms-service gunicorn start up successfully!'
else
   echo 'lms-service gunicorn start up failure! Please check /apps/lms/lms-service/logs/gunicorn_error.log'
fi
