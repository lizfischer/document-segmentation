from celery.utils.serialization import jsonify

from models import Project, Threshold
import time
from interface import celery
from image_generation import export_pdf_images, export_binary_images, split_images
from find_gaps import find_gaps

from flask import request

@celery.task(bind=True)
def binarize_task(self, project_id):
    project = Project.get_by_id(project_id)

    nsteps = 1
    if not project.get_pages():  # If pdf hasn't been converted to images yet
        nsteps = 2
        export_pdf_images(project, task=self, nsteps=nsteps)
    if not project.is_binarized:
        export_binary_images(project, task=self, nsteps=nsteps)

    return {'current': 100, 'total': 100, 'status': 'Done',
            'result': "Binarization successful"}


@celery.task(bind=True)
def margins_task(self, project_id, specs):
    project = Project.get_by_id(project_id)

    self.update_state(state='PENDING',
                      meta={'current': 0, 'total': 100,
                            'status': 'Preparing threshold preview...'})

    if specs:
        thresh = Threshold(h_width=float(specs['h_width']), h_blank=float(specs['h_blank']),
                           v_blank=float(specs['v_blank']), v_width=float(specs['v_width']))
        if specs["preview"] == "all":
            preview = None
        else:
            preview = [int(specs["start"]), int(specs["end"])]
    else:
        thresh = Threshold.get_default()
        preview = [0,10]

    find_gaps(project, thresh=thresh, preview=preview, task=self)

    return {'current': 100, 'total': 100, 'status': 'Done',
                'result': {
                    'thresh_id': thresh.id,
                    'preview': {
                        'start': preview[0],
                        'end': preview[1]
                    }
                }
            }


@celery.task(bind=True)
def simple_sep_task(self, project_id):
    project = Project.get_by_id(project_id)

    if not project.get_pages():  # If pdf hasn't been converted to images yet
        export_pdf_images(project, task=self)
    if not project.is_binarized:
        export_binary_images(project, task=self)

    return {'current': 100, 'total': 100, 'status': 'Done',
            'result': "Binarization successful"}

