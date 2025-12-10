I want to create a GUI python application using Dear PyGui.  

The application will be used to connect to a Polar Verity Sense or a Polar H10 Chest Strap from a laptop. 

I want to use the following package - https://github.com/ZheLearn/polar-python.

The application should be able to run on windows or macos.

It should periodically save the data to disk to prevent loss of data.  Store the data in json.

In the interface, I should be able to select between “Polar Verity Sense” or “Polar H10” with default being the Verity.

Connect button should connect to the selected device.

A text field for subject id  to use in creating the filename for storing the data.

The filename should be of the form: sub-subject_id_date-YYYYMMDD_time-HHMM.json

I want to have a live plotter of the heart rate. 

Create the necessary descriptions so I can build the application using pyinstaller using github to support windows and macos.