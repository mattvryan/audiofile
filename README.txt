AudioFile is a basic Python application used to manage an MP3 library.  It supports the following features:
 - Loading MP3 files in a folder into the library, with recursive descent.
 - Query and (crude) display of MP3 files.  Querying by artist, album, genre, title, etc.
 - Renaming of MP3 files per pattern based on metadata.
Future:
 - Tagging of MP3 files.
 - Scrobbling and publishing.
 - Some other cool features TBD.

AudioFile was originally created for the presentation "Writing Software for the Cloud", originally presented at OpenWest 2013.  The original purpose of the project was to demonstrate some ideas of how to write software that is meant to work in the cloud.  There are three formats to the app which are intended to demonstrate the topic of the presentation.  AudioFile is probably not useful as-is in practical application.

The first is a standard single-user app format.  It uses a straightforward, single-machine-based application development approach.  Loading scans a folder for MP3 files, then opens each MP3 file it finds, reads the ID3 v2 data, and stores the data in a sqlite database.  Queries operate on the database itself.  Renaming works with a specified format to rename the files one by one as matches are found in the database.

The second format demonstrates a refactoring of the first format to make the code more modular in preparation for cloud scale.  When loading the libary, instead of adding each file as it is found, the application creates and manages a pool of threads.  When the app finds an MP3 file, it posts a job to the threadpool, which assigns a thread to open the MP3 file, read the ID3 v2 data, and store the data in the database.  This format also abstracts the data store from the library so other data stores can be added without affecting the library code directly.

The third format uses a more cloud-based approach.  It uses a cloud-scale data store (CouchDB) and replaces the threadpool with code that posts messages to a message queue (RabbitMQ) and other parts of the code wait for and read messages from the queue.

