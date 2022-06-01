from models import Project
import time
from interface import celery
from image_generation import export_pdf_images, export_binary_images, split_images


@celery.task(bind=True)
def binarize_task(self, project_id):
    project = Project.get_by_id(project_id)

    if not project.get_pages():  # If pdf hasn't been converted to images yet
        export_pdf_images(project, task=self)
    if not project.is_binarized:
        export_binary_images(project, task=self)

    return {'current': 100, 'total': 100, 'status': 'Done',
            'result': "Binarization successful"}

