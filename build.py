import argparse
import os
import shutil
import subprocess


THIS_DIR = os.path.abspath(os.path.dirname(__file__))
BASEMODEL_NAME = 'basemodel.py'
BASEMODEL = os.path.join(THIS_DIR, BASEMODEL_NAME)
SANBOX = os.path.join(THIS_DIR, '_sandbox')


def build_models():

    for model_dir in os.listdir(SANBOX):
        print(model_dir)
        full_model_dir = os.path.join(SANBOX, model_dir)
        model_basemodel = os.path.join(full_model_dir, BASEMODEL_NAME)
        shutil.copy(BASEMODEL, model_basemodel)

        line = 'zip -j -r models/{target_name}.zip {model_dir}'.format(
            target_name=model_dir, model_dir=full_model_dir)

        subprocess.Popen(line.split(' '))


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--models', action='store_true', help='Build models', default=False)

    args = parser.parse_args()

    if args.models:
        build_models()
    else:
        print('Unknown action. Try --help to get help')


if __name__ == '__main__':

    main()
