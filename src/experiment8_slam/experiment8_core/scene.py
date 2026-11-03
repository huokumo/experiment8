"""Reuse Experiment7 geometry, adding visible horizontal surfaces for 3-D LIO."""
import xml.etree.ElementTree as ET
from experiment7_core.scene import BOXES as BASE_BOXES, generate as generate_base, text

PLATFORMS = [
    ('west_platform', (-3.3, 0., .55), (1.4, 2.8, 1.1)),
    ('north_platform', (0., 2.3, .55), (2., 1.4, 1.1)),
]
BOXES = [*BASE_BOXES, *PLATFORMS]


def generate(exp5, destination, pattern_csv, samples=4000, frequency=5.):
    generate_base(exp5, destination, pattern_csv, samples, frequency)
    root = ET.parse(destination).getroot()
    world = root.find('world')
    world.set('name', 'experiment8')
    robot = world.find("model[@name='r1']")
    sensor = robot.find("plugin[@name='experiment7::Mid360Teaching']")
    motion = robot.find("plugin[@name='experiment6::PlanarMotion']")
    for name, center, size in PLATFORMS:
        model = ET.SubElement(world, 'model', name=name)
        text(model, 'static', 'true')
        text(model, 'pose', ' '.join(map(str, (*center, 0, 0, 0))))
        link = ET.SubElement(model, 'link', name='link')
        for kind in ('collision', 'visual'):
            node = ET.SubElement(link, kind, name=kind)
            box = ET.SubElement(ET.SubElement(node, 'geometry'), 'box')
            text(box, 'size', ' '.join(map(str, size)))
            if kind == 'visual':
                material = ET.SubElement(node, 'material')
                text(material, 'ambient', '0.55 0.35 0.12 1')
                text(material, 'diffuse', '0.55 0.35 0.12 1')
        obstacle = ET.SubElement(sensor, 'obstacle')
        text(obstacle, 'pose', ' '.join(map(str, (*center, 0, 0, 0))))
        text(obstacle, 'size', ' '.join(map(str, size)))
        obstacle = ET.SubElement(motion, 'obstacle')
        for key, value in zip(('x', 'y', 'yaw', 'half_x', 'half_y'),
                              (center[0], center[1], 0, size[0]/2, size[1]/2)):
            text(obstacle, key, value)
    ET.indent(root, space='  ')
    ET.ElementTree(root).write(destination, encoding='utf-8', xml_declaration=True)
    return str(destination)
