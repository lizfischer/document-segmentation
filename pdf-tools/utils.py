import os
import unicodedata
import re

from werkzeug.utils import secure_filename

import parse_rules
from interface import app


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    value = value.replace(":", "")
    return re.sub(r'[-\s]+', '-', value).strip('-_')



def update_status(task, message, current, total, steps=None):
    if steps:
        message = f"{steps['prefix_message']}: {message} [step {steps['current']} of {steps['total']}]"
    task.update_state(state='PROGRESS',
                  meta={'current': current, 'total': total ,
                        'status': message})


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def ignore_handler(project, form_data, task=None, steps=None):
    # Handle Ignore Rules
    ignore_rule_1 = {"direction": form_data['ignore-position-0'],
                     "n_gaps": form_data['ignore-num-0'],
                     "min_size": form_data['ignore-width-0'],
                     "blank_thresh": form_data['ignore-blank-0']}
    ignore_rule_2 = {"direction": form_data['ignore-position-1'],
                     "n_gaps": form_data['ignore-num-1'],
                     "min_size": form_data['ignore-width-1'],
                     "blank_thresh": form_data['ignore-blank-1']}

    n_steps = 6
    if not ignore_rule_1["min_size"]:
        ignore_rule_1 = None
        n_steps -= 2
    if not ignore_rule_2["min_size"]:
        ignore_rule_2 = None
        n_steps -= 2

    steps = {'current': 0, 'total': n_steps, 'prefix_message': 'Finding areas to ignore'}
    parse_rules.ignore(project, ignore_rule_1, ignore_rule_2, task=task, steps=steps)
    return steps

