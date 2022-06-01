import os

from werkzeug.utils import secure_filename

import parse_rules
from interface import app
from models import Project


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def initialize_project(file):
    filename = secure_filename(file.filename)
    project_name = filename.split(".")[0]

    db_project = Project(name=project_name, file=filename)
    db_project.create()

    project_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(db_project.id))
    os.mkdir(project_folder)
    file_path = os.path.join(project_folder, filename)
    file.save(file_path)

    return db_project


def ignore_handler(project, form_data):
    # Handle Ignore Rules
    ignore_rule_1 = {"direction": form_data['ignore-position-0'],
                     "n_gaps": form_data['ignore-num-0'],
                     "min_size": form_data['ignore-width-0'],
                     "blank_thresh": form_data['ignore-blank-0']}
    ignore_rule_2 = {"direction": form_data['ignore-position-1'],
                     "n_gaps": form_data['ignore-num-1'],
                     "min_size": form_data['ignore-width-1'],
                     "blank_thresh": form_data['ignore-blank-1']}

    if not ignore_rule_1["min_size"]: ignore_rule_1 = None;
    if not ignore_rule_2["min_size"]: ignore_rule_2 = None;
    parse_rules.ignore(project, ignore_rule_1, ignore_rule_2)

