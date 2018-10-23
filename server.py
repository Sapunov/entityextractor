from importlib import import_module
import glob
import json
import logging
import os
import random
import shutil
import string
import zipfile
import sys

from flask import Flask, request, jsonify

import settings

app = Flask(__name__)

MODELS = {}

sys.path.append(settings.WORK_MODELS_DIRECTORY)


def setup_log():

    main_logger = logging.getLogger(settings.APP_NAME)
    app_logger = logging.getLogger(settings.APP_NAME + '.' + __file__.split('.')[0])
    app_logger.setLevel(settings.LOGGING_LEVEL)

    handler = logging.StreamHandler()
    handler.setLevel(settings.LOGGING_LEVEL)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    app_logger.addHandler(handler)

    return app_logger


log = setup_log()


def ensure_work_dir():

    if not os.path.exists(settings.WORK_DIRECTORY):
        os.mkdir(settings.WORK_DIRECTORY)

    if not os.path.exists(settings.WORK_MODELS_DIRECTORY):
        os.mkdir(settings.WORK_MODELS_DIRECTORY)


def clear_models_dir():

    if os.path.exists(settings.WORK_MODELS_DIRECTORY):
        log.debug('Cleaning: %s', settings.WORK_MODELS_DIRECTORY)
        shutil.rmtree(settings.WORK_MODELS_DIRECTORY)

    ensure_work_dir()


def random_string(n):

    return ''.join(
        random.choice(string.ascii_letters + string.digits) for _ in range(n))


def unzip_file_to_dir(filename, dirname):

    zip_ref = zipfile.ZipFile(filename, 'r')
    zip_ref.extractall(dirname)
    zip_ref.close()


def get_model_props(model_directory):

    props_file = os.path.join(model_directory, 'properties.json')

    if not os.path.exists(props_file):
        log.debug('Model: %s doesnt contains props file', model_directory)
        raise ValueError()

    props = {}

    try:
        with open(props_file) as fid:
            props = json.load(fid)
    except Exception:
        log.error('Bad props file: %s', props_file)
        raise ValueError()

    for propname in ['name', 'version', 'entrypoint']:
        if propname not in props:
            log.error('Bad property `%s` is absent in file: %s',
                propname, props_file)
            raise ValueError()

    return props


def change_directory_name(old_abs_name, new_name):

    parts = old_abs_name.split(os.sep)
    parts[-1] = new_name
    new_abs_name = os.sep.join(parts)

    os.rename(old_abs_name, new_abs_name)

    return new_abs_name


def prepare_models():

    log.debug('Preparing models')

    clear_models_dir()

    ready_models = []

    for model_file in glob.glob(os.path.join(settings.MODELS_DIRECTORY, '*.zip')):
        log.debug('Processing model: %s', model_file)

        tmp_model_work_dir = os.path.join(
            settings.WORK_MODELS_DIRECTORY, random_string(10))
        unzip_file_to_dir(model_file, tmp_model_work_dir)

        try:
            model_props = get_model_props(tmp_model_work_dir)
            model_name = model_props.get('name')
            new_model_work_dir = change_directory_name(tmp_model_work_dir, model_name)

            model_props['_class_string'] = model_name + '.' + model_props['entrypoint']

            ready_models.append(model_props)

            log.debug('Model: %s prepared', new_model_work_dir)
        except ValueError:
            log.debug('Deleting: %s', tmp_model_work_dir)
            shutil.rmtree(tmp_model_work_dir)

    return ready_models


def import_module_class(path_to_class):
    '''Import class from any module'''

    module_name, class_name = path_to_class.rsplit('.', 1)

    module = import_module(module_name)

    try:
        class_ = getattr(module, class_name)
    except AttributeError:
        raise ImportError('No class <%s> in %s' % (class_name, module))

    return class_


def load_models(ready_models):

    global MODELS

    log.debug('There is %s models to load', len(ready_models))

    for model_props in ready_models:
        log.debug('Loading model from: %s', model_props['_class_string'])
        path_to_class = model_props['_class_string']
        try:
            model_class = import_module_class(path_to_class)
            try:
                MODELS[model_props['name']] = model_class()
                log.debug('Model: %s succesfully loaded', model_props['name'])
            except Exception as exc:
                log.error('Error while instaniating model: %s - %s', model_props['name'], exc)
        except Exception as exc:
            log.error('Error while loading model: %s', exc)


@app.route('/extract/<string:model_name>', methods=['POST'])
def extract_entities(model_name):

    model_name = model_name.lower()

    if model_name not in MODELS:
        return jsonify({'error': 'Incorrect model name', 'ok': 0}), 200

    data = request.get_json()

    if 'text' in data:
        result = MODELS[model_name].extract(data['text'])
        return jsonify({'ok': 1, 'result': result})
    elif 'texts' in data:
        results = []
        for text_obj in data['texts']:
            extraction_result = MODELS[model_name].extract(text_obj['text'])
            results.append(extraction_result)
        return jsonify({'ok': 1, 'results': results})

    return jsonify({'ok': 0, 'error': 'Bad request'})


def main():

    ready_models = prepare_models()

    log.debug('Ready models: %s', ready_models)

    load_models(ready_models)

    app.run(debug=False)

if __name__ == '__main__':

    main()
