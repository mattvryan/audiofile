./audiofile3 -a ~/Music/vtest

#if [ ! -f ~/.audiofile/lib.db ]; then
#	echo "Database not created."
#	exit 1
#fi

./audiofile3 -r '%a/%b/%d.%n-%t-%b-%a.mp3'

if [ ! -f ~/Music/vtest/Scorpions/Blackout/1.7-Arizona-Blackout-Scorpions.mp3 ]; then
	echo "Renamed files not created."
	exit 2
fi
