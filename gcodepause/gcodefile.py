import re
from collections import OrderedDict
from pathlib import Path
from warnings import warn

import yaml

template = []
template.append(";BEGIN_PAUSE\n")
template.append("G91    ; Put in relative mode\n")
template.append("G1 Z{z_offset:.4g}    ; Raise hot end by {z_offset:.4g}mm\n")
template.append("G90    ; Put back in absolute mode\n")
template.append("G1 X{x:.4g} Y{y:.4g}    ; Move the X & Y away from the print\n")
template.append("M0 {message}    ; Pause and wait for the user\n")
template.append(";END_PAUSE\n")

class GCodeFile():

    def __init__(self, file):
        """A class that allows insertion and removal of pauses in a 3D printing GCODE file.
        
        Parameters
        ----------
        file : str
            The filename of the source GCODE file, including its path if not in the current
            directory.
            
        Returns
        -------
        self : GCodeFile
            A GCodeFile object representing the source GCODE file.
        """
        if Path(file).is_file() and Path(file).suffix == '.gcode':
            self.in_file = Path(file)
        else:
            raise FileNotFoundError(f"{file} is not a valid file")
        self.pause_template = template
        self.lines  = self._read_file()
        self._find_layers(self.lines)
        self._find_pauses(self.lines)

    def _read_file(self):
        """Reads the .gcode file into a list of lines."""
        with open(self.in_file, 'r') as file:
            return file.readlines()

    def _find_layers(self, lines):
        """Finds the layer changes in the file and the corresponding line numbers (zero index)."""
        layers = OrderedDict()

        for line_num, line in enumerate(lines):
            line = line.strip('\n').strip('\r')
            if re.match(r'\A(;[0-9]+\.*[0-9]*){1}\Z', line):
                height = float(line.strip(';'))
                layers[height] = line_num
        
        self.layers = layers

    def _find_pauses(self, lines):
        """Find the pause blocks in the file and the corresponding line numbers (zero index)"""
        pauses = OrderedDict()

        for line_num, line in enumerate(lines):
            line = line.strip('\n').strip('\r')
            if re.match(self.pause_template[0].strip('\n').strip('\r'), line):
                height = {l: h for h, l in self.layers.items()}[line_num - 1]
                pauses[height] = line_num, line_num + len(self.pause_template) - 1

        self.pauses = pauses


    def _get_layer(self, z):
        """Returns the line number matching a given layer height or the next higer layer if no
        layer exists at the given height."""
        if z in self.layers:
            return self.layers.get(z)
        else:
            layers = [height for height in sorted(self.layers.keys()) if height > z]
            if len(layers) > 0:
                warn(f"No layer found at {z}; using the next higher layer ({layers[0]}).")
                return self.layers.get(layers[0])
            else:
                warn(f"{z} is above all layers.")
                return None

    def _get_pause_text(self, z_offset, x_pause, y_pause, message):
        """Returns a list of lines to be inserted into the file."""
        text = self.pause_template[:]
        
        if z_offset > 0:
            text[2] = text[2].format(z_offset=z_offset)
        else:
            raise ValueError(f"z_offset must be greater than zero, got  {z_offset}")
        if x_pause > 0 and y_pause > 0:
            text[4] = text[4].format(x=x_pause, y=y_pause)
        else:
            e = f"x_pause and y_pause must be greater than zero, got ({x_pause, y_pause})"
            raise ValueError(e)
        text[5] = text[5].format(message=message)

        return text

    def insert_pause(self, z, z_offset=10, x_pause=10, y_pause=10, message=None):
        """Inserts a pause at the begining of the layer at a specified height.
        
        Parameters
        ----------
        z : int or float
            The height of the layer at which to insert a pause. if not layer exist at the specified
            height, the pause will be inserted at the next higher layer.
            
        z_offset : int of float (> 0), default=10
            Specifies by how much the hot end will move vertically relative to the print
            at the begining of the pause.

        x_pause : int or float (> 0), default=10
            Specifies the X position at which the print head will mode at the begining of the
            pause.

        y_pause: int or float (> 0), default=10
            Specifies the Y position at which the print head will mode at the begining of the
            pause.

        message: str,
            The message associated with the pause. Depenging of the printer configuration, this
            message may or may not be displayed during the pause.

        Returns
        -------
        None
        """
        insert_line = self._get_layer(z)
        if insert_line is not None:
            insert_line += 1

            pause_template = self._get_pause_text(z_offset, x_pause, y_pause, message)
            self.lines = self.lines[:insert_line] + pause_template + self.lines[insert_line:]
            self._find_layers(self.lines)
            self._find_pauses(self.lines)

    def insert_pauses_from_yaml(self, file):
        """Inserts one or more pauses as defined in a YAML file.

        Parameters
        ----------
        file : str
            The filename of the YAML file (.yml or .yaml), including its path if not in the current
            directory. See examples folder for an example file format.

        Returns
        -------
        None
        """
        if Path(file).is_file():
            with open(Path(file), 'r') as f:
                pauses = OrderedDict(yaml.load(f, Loader=yaml.Loader))

            for height, params in pauses.items():
                self.insert_pause(height, **params)
        else:
            raise FileNotFoundError(f"{file} is not a valid file")
    
    def remove_pause(self, height):
        """Removes the pause at a specified height if present.
        
        Parameters
        ----------
        height : int or float
            The height (z value) of the layer at which to remove the pause.

        Returns
        -------
        None
        """
        if height in self.pauses:
            start, end = self.pauses[height]
            self.lines = self.lines[:start] + self.lines[end + 1:]
            self._find_layers(self.lines)
            self._find_pauses(self.lines)
        else:
            warn(f"No pause found at height of {height}")

    def write(self, file=None, suffix='_pause'):
        """Writes the modified GCODE to a file.
        
        Parameters
        ----------
        file : str, default=None
            The name of the file in which to write the modified GCODE. If ommited, the name of the
            source file will be reused, with the value of the 'suffix' parameter appended.

        suffix : str, default='_pause'
            A suffix to be added to the source filename. Ignored if a filename is passed to the
            file parameter.

        Returns
        -------
        None
        """
        if file is not None:
            file = Path(file)
        else:
            file = Path(self.in_file)
            file = file.parent.joinpath(Path(file.stem + suffix + file.suffix))
        with open(file, 'w') as f:
            f.writelines(self.lines)
