import io
import shutil
import zipfile

from flask import render_template, request, redirect, url_for, flash, send_file, jsonify

import parse_rules
from find_gaps import find_gaps
from image_generation import export_pdf_images, split_images
from utils import allowed_file, initialize_project, ignore_handler
from models import *
from interface import tasks, celery


@app.route('/status/<task_id>', methods=['GET'])
def task_status(task_id):
    task = celery.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            "task_id": task_id,
            "state": task.state,
            "current": 0,
            "total": 1,
            "status": "Pending..."
        }
    elif task.state != 'FAILURE':
        response = {
            "task_id": task_id,
            "state": task.state,
            "current": task.info.get('current', 0),
            "total": task.info.get('total', 1),
            "status": task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # Something went wrong in the task
        response = {
            "task_id": task_id,
            "state": task.state,
            "current": 1,
            "total": 1,
            "status": str(task.info)
        }

    return jsonify(response )


@app.route('/delegate', methods=['POST'])
def delegate_tasks():
    content = request.json
    project_id = content["project_id"]
    if content["type"] == "binarize":
        task = tasks.binarize_task.delay(project_id)
    if content["type"] == "thresholds":
        task = tasks.margins_task.delay(project_id, content["data"])

    return jsonify({"task_id": task.id}), 202

# TODO: Decompose me please!

@app.route('/')
def main():
    projects = Project.query.all()
    return render_template('select_project.html', projects=projects)


@app.route('/<project_id>/project')
def project(project_id):
    p = Project.get_by_id(project_id)
    return render_template('project.html', project=p)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash('Invalid file format')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            new_project = initialize_project(file)
            return redirect(url_for('project', project_id=new_project.id))
    return render_template("upload.html")


@app.route('/<project_id>/split', methods=['GET', 'POST'])
def split_file(project_id):
    project = Project.get_by_id(project_id)

    pct = .5
    pages = project.get_pages(original_only=True)

    if len(pages) == 0:  # If pdf hasn't been converted to images yet
        export_pdf_images(project)
    if request.method == 'POST':
        pct = float(request.form['split_pct'])
        split_images(project, pct)
        flash('Successfully split pages')

    image_paths = [page.get_ui_img() for page in project.get_pages()]
    return render_template('split.html', project=project, images=image_paths, pct=pct)


@app.route('/<project_id>/threshold-preview', methods=['GET'])
def threshold_preview(project_id):  # Potentially replacing the find_margins function
    project = Project.get_by_id(project_id)

    thresh_id = request.args.get('t')
    start = int(request.args.get('start'))
    end = int(request.args.get('end'))

    thresh = Threshold.get_by_id(thresh_id)
    anno_map = []

    pages = project.get_pages()
    pages = pages[start:end]

    for page in pages:
        anno_map.append({"img": page.get_ui_img(), "anno": page.get_whitespace(thresh).annotation})

    return render_template('margins.html', project=project, data=anno_map, thresh=thresh, start=start, end=end)


@app.route('/<project_id>/simple', methods=['GET', 'POST'])
def simple_separate_ui(project_id):
    project = Project.get_by_id(project_id)

    status = None

    if request.method == 'POST':
        form_data = request.form
        ignore_handler(project, form_data)

        parse_rules.simple_separate(project,
                                    gap_size=float(form_data["gap-width"]),
                                    blank_thresh=float(form_data["gap-blank"]),
                                    split=form_data["split-type"],
                                    regex=form_data["regex-text"])

        status = "done!"
    return render_template('simple_sep.html',  project=project, status=status)


@app.route('/<project_id>/indent', methods=['GET', 'POST'])
def indent_separate_ui(project_id):
    status = None

    if request.method == 'POST':
        form_data = request.form
        ignore_data = ignore_handler(project_id, form_data)  # FIXME: should this be returning a list?
        entries = parse_rules.indent_separate(project_id,
                                              indent_type=form_data["indent-type"],
                                              margin_thresh=float(form_data["hanging-blank"]),
                                              indent_width=float(form_data["regular-width"]),
                                              ignore=ignore_data)

        project_folder = os.path.join((app.config['UPLOAD_FOLDER']), project_id)
        with open(os.path.join(project_folder, "entries.json"), "w") as outfile:
            json.dump(entries, outfile, indent=4)
        status = "done!"
    return render_template('indent_sep.html', project_id=project_id, status=status)


@app.route('/<project_id>/cleanup')  # TODO: DB-ify
def cleanup(project_id):
    files_to_save = [f"{project_id}.pdf", "entries.json"]
    project_folder = os.path.join(app.config['UPLOAD_FOLDER'], project_id)
    files = os.listdir(project_folder)
    for f in files:
        path = os.path.join(project_folder, f)
        if f not in files_to_save:
            try:
                shutil.rmtree(path)
            except OSError:
                os.remove(path)

    flash('Project files cleaned up')
    return redirect(url_for("project", project_id=project_id))


@app.route('/<project_id>/export') # TODO: DB-ify
def export(project_id):
    project = Project.objects(id=project_id).first()

    path = project.entries_to_json(file=True)
    return send_file(path, as_attachment=True, attachment_filename=f"{project.name}_entries.json")


@app.route('/<project_id>/export_txt') # TODO: DB-ify
def export_txt(project_id):
    project = Project.get_by_id(project_id)

    dir = project.entries_to_txt() #FIXME

    data = io.BytesIO()
    files = os.listdir(dir)
    with zipfile.ZipFile(data, mode='w') as z:  # open ZIP
        for i in range(0, len(files)):  # For all entries
            z.write(os.path.join(dir, files[i]), files[i])
    data.seek(0)
    shutil.rmtree(dir)  # remove temp files
    return send_file(  # Download ZIP
        data,
        mimetype='application/zip',
        as_attachment=True,
        attachment_filename=f'{project.name}.zip'
    )
