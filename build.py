import argparse
import os
import shutil
import subprocess
import json
import re
from datetime import datetime


THIS_DIR = os.path.abspath(os.path.dirname(__file__))
BASEMODEL_NAME = 'basemodel.py'
BASEMODEL = os.path.join(THIS_DIR, BASEMODEL_NAME)
SANBOX = os.path.join(THIS_DIR, '_sandbox')


def update_version(props_file):

    version_pattern = '([0-9]{4}-[0-9]{2}-[0-9]{2})\.([0-9]+)'

    props = {}
    with open(props_file) as fid:
        props = json.load(fid)

    current_version = props['version']
    date, seq = re.match(version_pattern, current_version).groups()

    seq = int(seq)
    new_date = datetime.now().strftime('%Y-%m-%d')

    new_version = '{0}.{1}'.format(new_date, seq + 1)
    props['version'] = new_version

    with open(props_file, 'w') as fid:
        json.dump(props, fid)

    return new_version


def build_models():

    for model_dir in os.listdir(SANBOX):
        print('Building', model_dir)

        full_model_dir = os.path.join(SANBOX, model_dir)
        props_file = os.path.join(full_model_dir, 'properties.json')
        model_basemodel = os.path.join(full_model_dir, BASEMODEL_NAME)

        target_version = update_version(props_file)

        print('Target version:', target_version)

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
