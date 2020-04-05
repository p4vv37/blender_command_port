# Blender Command Port

Command Port addon for Blender.

## How to use
### Installing


Open User Preferences and click Install from File under Add-ons. Then navigate to the downloaded zip archive of this plugin and select it.
### Starting the port
Command port can be configured and started from a Blender Command Port section of "Data" panel.
![Command port configuration](img/command_port_settings.png?raw=true "Title")

### Basic usage

Command should be sent to command port as a text. It can be also done sent from Python:

```
import socket


def send_command(command):
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect(('localhost', 5000))
    clientsocket.sendall(command.encode())
    while True:
        res = clientsocket.recv(4096)
        if not res:
            break
        print(res.decode())
    clientsocket.close()

send_command("""
j = 0
for i in range(10):
    print(j)
    j+=i*2
j
""")
```

### Visual Studio Code Integration
The following json code can be pasted into a task.json file to add an 'Execute Script in Blender' task to VS Code.
```
{
	// See https://go.microsoft.com/fwlink/?LinkId=733558
	// for the documentation about the tasks.json format
	"version": "2.0.0",
	"tasks": [
		{
			"label": "Execute Script in Blender",
			"type": "shell",
			"command": "python",
			"args": [
				"${env:APPDATA}/Blender Foundation/Blender/2.82/scripts/addons/blender_command_port/execute_file_in_blender.py",
				"${file}",
				"5000"
			],
			"presentation": {
				"reveal": "always",
				"panel": "new"
			},
			"problemMatcher": []
		}
	]
}
```

### PyCharm Integration
Another way is to use execute_file_in_blender.py script to create a run configuration in PyCharm that executes a file in Blender. Path to a file must be passed as a first script parameter, port need to be passed as a second one.
![PyCharm configuration](img/pycharm.png?raw=true "Title")

## Authors

* **Paweł Kowalski** - [pkowalski.com](http://pkowalski.com)
* **Jeff Hanna** - [github/jeffhanna](https://github.com/jeffhanna)

## License

This project is licensed under the MIT License
