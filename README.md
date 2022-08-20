# dbus-discovergy-smartmeter Service

### Purpose

This service is meant to be run on a raspberry Pi with Venus OS from Victron.

The Python script cyclically reads data from Discoergy via the REST API and publishes information on the dbus, using the service name com.victronenergy.grid. This makes the Venus OS work as if you had a physical Victron Grid Meter installed.

### Configuration

Replace the contents in the discovergy-config.py with the actual values.

### Installation

1. Install git on the Venus device:

   1. Connect to root shell    
   2. `opkg update` to update the package manager sources
   3. `opkg install git` to install git

2. Fetch this repository:

   1. `cd /data`
   2. `git clone https://github.com/flofloflo/venus.dbus-discovergy-smartmeter.git dbus-discovergy-smartmeter`

3. Set permissions for files:

   `chmod 755 /data/dbus-discovergy-smartmeter/service/run`

   `chmod 744 /data/dbus-discovergy-smartmeter/kill_me.sh`

4. Get two files from the [velib_python](https://github.com/victronenergy/velib_python) and install them on your venus:

   1. `git clone https://github.com/victronenergy/velib_python.git`
   2. `cp velib_python/vedbus.py dbus-discovergy-smartmeter/vedbus.py`
   3. `cp velib_python/ve_utils.py dbus-discovergy-smartmeter/ve_utils.py`

4. Add a symlink to the file /data/rc.local:

   `ln -s /data/dbus-discovergy-smartmeter/service /service/dbus-discovergy-smartmeter`

   Or if that file does not exist yet, store the file rc.local from this service on your Raspberry Pi as /data/rc.local .
   You can then create the symlink by just running rc.local:
  
   `rc.local`

   The daemon-tools should automatically start this service within seconds.

### Debugging

You can check the status of the service with svstat:

`svstat /service/dbus-discovergy-smartmeter`

It will show something like this:

`/service/dbus-discovergy-smartmeter: up (pid 10078) 325 seconds`

If the number of seconds is always 0 or 1 or any other small number, it means that the service crashes and gets restarted all the time.

When you think that the script crashes, start it directly from the command line:

`python /data/dbus-discovergy-smartmeter/dbus-discovergy-smartmeter.py`

and see if it throws any error messages.

If the script stops with the message

`dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.grid"`

it means that the service is still running or another service is using that bus name.

#### Restart the script

If you want to restart the script, for example after changing it, just run the following command:

`/data/dbus-discovergy-smartmeter/kill_me.sh`

The daemon-tools will restart the scriptwithin a few seconds.

