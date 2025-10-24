import re
from dataclasses import dataclass, field
from xml.etree import ElementTree

from vector import MomentumObject4D 

@dataclass
class Particle:
    pdgid: int
    px: float
    py: float
    pz: float
    energy: float
    mass: float
    spin: float
    status: int
    vtau: float
    parent: int

    def p4(self):
        return MomentumObject4D(px = self.px, py = self.py, pz = self.pz, E=self.energy)


@dataclass
class Event:
    particles: list = field(default_factory=list)
    weights: list = field(default_factory=list)
    scale: float = -1

    def add_particle(self, particle):
        self.particles.append(particle)


class LHEReader():
    def __init__(self, file_path, weight_mode='list', weight_regex = '.*'):
        '''
        Constructor.

        :param file_path: Path to input LHE file
        :type file_path: string
        :param weight_mode: Format to return weights as. Can be dict or list. If dict, weight IDs are used as keys.
        :type weight_mode: string
        :param weight_regex: Regular expression to select weights to be read. Defaults to reading all.
        :type weight_regex: string
        '''
        self.file_path = file_path
        self.iterator = ElementTree.iterparse(self.file_path,events=('start','end'))
        self.current = None
        self.current_weights = None

        assert(weight_mode in ['list','dict'])
        self.weight_mode = weight_mode
        self.weight_regex = re.compile(weight_regex)

    def unpack_from_iterator(self):
        # Read the lines for this event
        lines = self.current[1].text.strip().split("\n")

        # Create a new event
        event = Event()
        event.scale = float(lines[0].strip().split()[3])
        event.weights = self.current_weights

        # Read header
        event_header = lines[0].strip()
        num_part = int(event_header.split()[0].strip())

        # Iterate over particle lines and push back
        for ipart in range(1, num_part+1):
            part_data = lines[ipart].strip().split()
            p = Particle(pdgid = int(part_data[0]),
                        status = int(part_data[1]),
                        parent = int(part_data[2])-1,
                        px = float(part_data[6]),
                        py = float(part_data[7]),
                        pz = float(part_data[8]),
                        energy = float(part_data[9]),
                        mass = float(part_data[10]),
                        vtau = float(part_data[11]),
                        spin = int(float(part_data[12])))
            event.add_particle(p)

        return event

    def __iter__(self):
        return self

    def __next__(self):
        # Clear XML iterator
        if(self.current):
            self.current[1].clear()

        # Find beginning of new event in XML
        element = next(self.iterator)
        while element[1].tag != "event":
            element = next(self.iterator)

        # Loop over tags in this event
        element = next(self.iterator)

        if self.weight_mode == 'list':
            self.current_weights = []
        elif self.weight_mode == 'dict':
            self.current_weights = {}

        while not (element[0]=='end' and element[1].tag == "event"):
            if element[0]=='end' and element[1].tag == 'wgt':

                # If available, use "id" identifier as
                # 1. filter which events to read
                # 2. key for output dict
                weight_id = element[1].attrib.get('id','')

                if self.weight_regex.match(weight_id):
                    value = float(element[1].text)
                    if self.weight_mode == 'list':
                        self.current_weights.append(value)
                    elif self.weight_mode == 'dict':
                        self.current_weights[weight_id] = value
            element = next(self.iterator)

        # Find end up this event in XML
        # use it to construct particles, etc
        while not (element[0]=='end' and element[1].tag == "event"):
            element = next(self.iterator)
        self.current = element

        return self.unpack_from_iterator()
