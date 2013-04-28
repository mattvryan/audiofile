pushd ~/Music/vtest
rm -rf *
cp -a ~/Music/My_Music/Scorpions . 
popd
rm ~/.audiofile/lib.db
python resetmongo.py
