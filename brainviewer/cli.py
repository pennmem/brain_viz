from argparse import ArgumentParser
from brainviewer.pipeline import generate_subject_brain, generate_average_brain
from cml_pipelines.wrapper import memory


def build_average_brain_visualization(input_args=None):
    parser = ArgumentParser()
    parser.add_argument('--blender', '-b', action='store_true', default=False,
                        help='Generate Blender standalone 3D viewer')

    args = parser.parse_args(input_args)
    generate_average_brain(blender=args.blender)
    memory.clear()


def build_subject_brain_visualization(input_args=None):
    parser = ArgumentParser()
    parser.add_argument('--subject', '-s', help='Subject ID')
    parser.add_argument('--localization', '-l', help='Localization number')
    parser.add_argument('--blender', '-b', action='store_true', default=False,
                        help='Generate Blender standalone 3D viewer')

    args = parser.parse_args(input_args)
    generate_subject_brain(args.subject, args.localization,
                           blender=args.blender)
    memory.clear()






