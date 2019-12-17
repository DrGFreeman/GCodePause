# GCodePause python package

Add pauses at specific layer heights in 3D printing G-code.

By Julien de la Bruère-Terreault (drgfreeman@tuta.io)

## Installation

The *gcodepause* package can be installed using pip:

```
pip install git+https://github.com/DrGFreeman/GCodePause.git
```

Or from sources:

```
python setup.py install
```

## Usage

Pauses can be added to a .gcode file using the `gcodepause.GCodeFile` class as demonstrated in the example below:

```python
from gcodepause import GCodeFile

# Create a GCodeFile instance from the source .gcode file
gcode = GCodeFile('source.gcode')

# Add a pause at the begining of layer at height of 4.6mm (z).
#   Raise the print head 25mm (z_offset) and move the
#   print head to X,Y coordinates 125, 200 (x_pause, y_pause).
gcode.insert_pause(z=4.6, z_offset=25, x_pause=125, y_pause=200,
                   message='Message to display')

# Write the modified G-code to a new file
gcode.write('modified.gcode')
```

Alternatively, pauses can be defined in a .yaml file. Given a .yaml file *pauses.yaml* with the following content:

```yaml
# pauses.yaml
4.2: # Pause at layer height of 4.2mm
  z_offset: 20
  x_pause: 125
  y_pause: 200
  message: Message for 4.2
  
7: # Pause at layer height of 7mm
  z_offset: 15
  x_pause: 10.5
  y_pause: 10.5
  message: Message for 7.0
```
The following code will insert pauses at the begining of the layers at heights of 4.2mm and 7mm with the respective associated parameters and save the modified gcode into a file named *source_pause.gcode*:

```python
from gcodepause import GCodeFile

gcode = GCodeFile('source.gcode')

# Add pauses as specified in the .yaml file
gcode.insert_pause_from_yaml('pauses.yaml')

# Write the modified G-code to a new file using the default name
# <original_name>_pause.gcode
gcode.write()
```

The diff function below shows the lines added into *source_pause.gcode*:

```
$ diff source.gcode source_pause.gcode
21907a21908,21914
> ;BEGIN_PAUSE
> G91    ; Put in relative mode
> G1 Z20    ; Raise hot end by 20mm
> G90    ; Put back in absolute mode
> G1 X125 Y200    ; Move the X & Y away from the print
> M0 Message for 4.2    ; Pause and wait for the user
> ;END_PAUSE
35010a35018,35024
> ;BEGIN_PAUSE
> G91    ; Put in relative mode
> G1 Z15    ; Raise hot end by 15mm
> G90    ; Put back in absolute mode
> G1 X10.5 Y10.5    ; Move the X & Y away from the print
> M0 Message for 7.0    ; Pause and wait for the user
> ;END_PAUSE
```

The `GCodeFile` object has different attributes and additional methods that can be helpful:

The `.layers` attribute contains an `OrderedDict` of the different layers and their respective line number in the current state of the gcode (zero indexed):

```python 
>>> gcode.layers
OrderedDict([(0.2, 46),
             (0.4, 1139),
             (0.6, 2237),
             (0.8, 3334),
             ...
             (16.6, 80939),
             (16.8, 81018),
             (17.0, 81096),
             (17.2, 81173)])
```

The `.pauses` attribute contains an `OrderedDict` of the different pauses and their respective start and end line numbers in the current state of the gcode (zero indexed):

```python 
>>> gcode.pauses
OrderedDict([(4.2, (21907, 21913)), (7.0, (35017, 35023))])
```

The `.remove_pause(height)` method removes the pause at the specified height (if present):

```python 
>>> gcode.remove_pause(4.2)
>>> gcode.pauses
OrderedDict([(7.0, (35010, 35016))])
```

Finally, the `.pauses_template` attribute contains a list of the lines that will be inserted into the gcode to instruct the printer to pause:

```python
>>> gcode.pause_template
[';BEGIN_PAUSE\n',
 'G91    ; Put in relative mode\n',
 'G1 Z{z_offset:.4g}    ; Raise hot end by {z_offset:.4g}mm\n',
 'G90    ; Put back in absolute mode\n',
 'G1 X{x_pause:.4g} Y{y_pause:.4g}    ; Move the X & Y away from the print\n',
 'M117 {message}    ; Diplay message to user\n',
 'M0     ; Pause and wait for the user\n',
 ';END_PAUSE\n']
```

## Pause G-code

The G-code inserted for each pause will first move the print head to the speficied coordinates using [`G1`](https://www.reprap.org/wiki/G-code#G0_.26_G1:_Move) commands (in relative mode for Z and absolute for X & Y). Then, a [`M117`](https://www.reprap.org/wiki/G-code#M117:_Display_Message) command is issued to display the pause message to the user. Finally, a [`M0`](https://www.reprap.org/wiki/G-code#M0:_Stop_or_Unconditional_stop) command is issued to pause the print until resumed by the user.

These commands will be properly interpreted by printers running Marlin or RepRap firmware. Compatibility with other firmware should be verified [here](https://www.reprap.org/wiki/G-code).

## Notes

1. If no layer exist at the specified pause `z` value, a warning will be issued and the pause will be inserted at the next (higher) layer.
1. If the specified pause `z` value exceeds the height of the last layer, a warning will be issued and the pause will not be added.
1. It is recommended to avoid moving the print head at the limits of the printer bed during the pause as this may trigger limit switches or cause mechanical contacts, potentially resulting in a horizontal offset in the print at the location of the pause(s).
1. To detect the layer changes in the G-code, the parser looks for a comment line with the layer height (e.g. `;4.2` for the layer at 4.2mm) at the begining of the layer change. Ensure that the slicer includes this line at the begining of each layer change. In [PrusaSlicer](https://www.prusa3d.com/prusaslicer/), this is included by default under *Printer Settings -> Custom G-code -> Before layer change G-code* (third line below). Other slicers should also allow the inclusion of custom G-code before the layer change.

```
;BEFORE_LAYER_CHANGE
G92 E0.0
;[layer_z]
```


