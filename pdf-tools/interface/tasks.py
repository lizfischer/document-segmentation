from models import Project
import time
from interface import celery


@celery.task(name="create_task")
def create_task():
    time.sleep(10)
    return True



@celery.task(bind=True)
def binarize_task(self, project_id):
    project = Project.get_by_id(project_id)

    pages = project.get_pages()

    i = 1
    for p in pages:
        self.update_state(state='PROGRESS',
                      meta={'current': i, 'total': len(pages),
                            'status': f"working on {p}"})
        i += 1
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}

