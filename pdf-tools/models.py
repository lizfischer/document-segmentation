import os
import json

import shutil

from interface import app
from interface import db
from sqlalchemy.orm import validates


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


class BoundingBox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'), nullable=False)

    page = db.Column(db.Integer, nullable=False)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    w = db.Column(db.Integer, nullable=False)
    h = db.Column(db.Integer, nullable=False)


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    project = db.relationship('Project', backref=db.backref('entries', cascade='all,delete'), lazy=True)

    text = db.Column(db.String)
    sequence = db.Column(db.Float)
    boxes = db.relationship('BoundingBox', backref='entry', cascade="all,delete", lazy=True)
    name = db.Column(db.String)

    def add_box(self, b):
        db.session.add(self)
        self.boxes.append(b)
        db.session.commit()

    def to_json(self):
        return {"text": self.text,
                "boxes": [{"x": b.x, "y": b.y, "h": b.h, "w": b.w, "page": b.page}
                          for b in self.boxes]}

    def update_text(self, text):
        self.text = text.strip()
        db.session.commit()

    def update_name(self, name):
        self.name = name.strip()
        db.session.commit()

    @staticmethod
    def get_by_id(entry_id):
        return Entry.query.filter_by(id=entry_id).first()

    @staticmethod
    def get_first(project_id):
        return Entry.query.filter_by(project_id=project_id).order_by(Entry.sequence).limit(1).first() #TODO Change to min sequence

    def get_next(self):
        return Entry.query.filter_by(project_id=self.project.id).filter(Entry.sequence > self.sequence).order_by(Entry.sequence).limit(1).first()

    def get_previous(self):
        return Entry.query.filter_by(project_id=self.project.id).filter(Entry.sequence < self.sequence).order_by(Entry.sequence.desc()).limit(1).first()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Threshold(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    h_width = db.Column(db.Float, default=40.0)
    h_blank = db.Column(db.Float, default=0.02)
    v_width = db.Column(db.Float, default=10.0)
    v_blank = db.Column(db.Float, default=0.05)
    name = db.Column(db.String, unique=True)

    def toJSON(self):
        return {"h_width": self.h_width,
                "h_blank": self.h_blank,
                "v_width": self.v_width,
                "v_blank": self.v_blank}

    def __init__(self, *args, h_width=40.0, h_blank=0.02,
                 v_width = 10.0, v_blank = 0.05, **kwargs):
        self.h_width = h_width
        self.h_blank = h_blank
        self.v_width = v_width
        self.v_blank = v_blank
        for key, value in kwargs.items():
            setattr(self, key, value)


    @staticmethod
    def get_default():
        default = Threshold.query.filter_by(name="default").first()
        if not default:
            db.session.add(Threshold(name="default"))
            db.session.commit()
        return default

    @staticmethod
    def get_by_values(h_width, h_blank, v_width, v_blank):
        return Threshold.query.filter_by(h_width=h_width, h_blank=h_blank,v_width=v_width, v_blank=v_blank).first()

    @staticmethod
    def get_by_id(threshold_id):
        return Threshold.query.filter_by(id=threshold_id).first()


class Gap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    whitespace_id = db.Column(db.Integer, db.ForeignKey('whitespace.id'), nullable=False)

    start = db.Column(db.Integer, nullable=False)
    end = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    direction = db.Column(db.String, nullable=False)

    @validates('direction')
    def validate_direction(self, key, t):
        assert t in ["horizontal", "vertical"]
        return t


class Whitespace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)
    page = db.relationship('Page', backref=db.backref('whitespaces', cascade="all,delete"), lazy=True)

    threshold_id = db.Column(db.Integer, db.ForeignKey('threshold.id'), nullable=False)
    threshold = db.relationship('Threshold', lazy=True, uselist=False)

    gaps = db.relationship('Gap', backref='whitespace', cascade="all,delete", lazy=True)

    annotation = db.Column(db.String)

    def add_gap(self, g):
        exists = Gap.query.with_parent(self).filter_by(start=g.start, end=g.end, width=g.width, direction=g.direction).first()
        if not exists:
            self.gaps.append(g)
            db.session.commit()

    def set_annotation(self, a):
        self.annotation = a
        db.session.commit()

    def get_horizontal(self):
        return [g for g in self.gaps if g.direction == "horizontal"]

    def get_vertical(self):
        return [g for g in self.gaps if g.direction == "vertical"]

    def get_nth_horizontal(self, n):
        gaps = self.get_horizontal()
        try: return gaps[n]
        except IndexError: return None

    def get_nth_vertical(self, n):
        gaps = self.get_vertical()
        try: return gaps[n]
        except IndexError: return None


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    project = db.relationship('Project', backref=db.backref('pages', cascade="all,delete"), lazy=True)

    sequence = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(), nullable=False)
    type = db.Column(db.String, nullable=False, default="original")
    height = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=False)

    ignore_start = db.Column(db.Integer)
    ignore_end = db.Column(db.Integer)
    ignore_left = db.Column(db.Integer)
    ignore_right = db.Column(db.Integer)

    def __repr__(self):
        return f'<Page {self.image}>'

    def __init__(self, *args, **kwargs):
        self.ignore_start = 0
        self.ignore_end = kwargs['height']
        self.ignore_left = 0
        self.ignore_right = kwargs['width']
        for key, value in kwargs.items():
            setattr(self, key, value)

    @validates('type')
    def validate_type(self, key, t):
        assert t in ["original", "split"]
        return t

    def get_ui_img(self):
        return os.path.join(app.config['VIEW_UPLOAD_FOLDER'], str(self.project_id), "images", str(self.image))

    def get_img(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.project_id), "images", str(self.image))

    def get_binary(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.project_id), "images",
                            str(self.image).replace(".jpg", ".tiff"))

    def add_whitespace(self, ws):
        space = get_or_create(db.session, Whitespace, threshold_id=ws.threshold.id, page_id=self.id)
        return space
        # exists = self.get_whitespace(ws.threshold)
        # if not exists:
        #     self.whitespaces.append(ws)
        #     db.session.commit()
        # return self.get_whitespace(ws.threshold)

    def get_whitespace(self, thresh):
        ws = Whitespace.query.with_parent(self).filter_by(threshold_id=thresh.id).first()
        return ws

    def set_ignore(self, direction, value):
        if direction == "start": self.ignore_start = value
        elif direction == "end": self.ignore_end = value
        elif direction == "left": self.ignore_left = value
        elif direction == "right": self.ignore_right = value
        else: raise ValueError(f"Cannot set ignore type '{direction}'")
        db.session.commit()


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    file = db.Column(db.String())

    is_split = db.Column(db.Boolean(), default=False)
    is_binarized = db.Column(db.Boolean(), default=False)
    has_gaps = db.Column(db.Boolean(), default=False)

    def __repr__(self):
        return f'<Project {self.name}>'

    @staticmethod
    def get_by_id(project_id):
        return Project.query.filter_by(id=project_id).first()

    def create(self):
        db.session.add(self)
        db.session.commit()

    def add_page(self, page):
        self.pages.append(page)
        db.session.commit()

    def add_entry(self, entry):
        self.entries.append(entry)
        db.session.commit()

    def set_name(self, new_name):
        self.name = new_name
        db.session.commit()

    def set_binarized(self, b):
        self.is_binarized = b
        db.session.commit()

    def set_split(self, b):
        self.is_split = b
        db.session.commit()

    def set_gaps(self, b):
        self.has_gaps = b
        db.session.commit()

    def get_folder(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.id))

    def get_pdf(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.id), str(self.file))

    def get_image_dir(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.id), "images")

    def get_binary_dir(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.id), "binary")

    def get_pages(self, original_only=False):
        if self.is_split and not original_only:
            pages = Page.query.with_parent(self).filter(Page.type == "split").all()
        else:
            pages = Page.query.with_parent(self).filter(Page.type == "original").all()
        return pages

    def get_page_by_id(self, page_id):
        page = Page.query.with_parent(self).filter(Page.type == "split", Page.id == page_id).first()
        return page

    def get_page_by_sequence(self, n, original_only=False):
        if self.is_split and not original_only:
            page = Page.query.with_parent(self).filter(Page.type == "split", Page.sequence==n).first()
        else:
            page = Page.query.with_parent(self).filter(Page.type == "original", Page.sequence==n).first()
        return page

    def has_whitespace(self, thresh, pages=None):
        ws = self.get_whitespace(thresh)
        if not pages:
            return len(ws) > 0
        existing_pgs = [space.page_id for space in ws]
        for i, page in enumerate(pages):  # for every page
            if page.id not in existing_pgs:
                return False
        return True

    def get_whitespace(self, thresh):
        return Whitespace.query.join(Page, Whitespace.page_id == Page.id) \
            .filter(Page.project_id == self.id, Whitespace.threshold_id == thresh.id).all()

    def remove_split_pages(self):
        pages = Page.query.with_parent(self).filter(Page.type == "split").all()
        for p in pages:
            db.session.delete(p)
        db.session.commit()

    def clear_entries(self):
        for e in self.entries:
            db.session.delete(e)
        db.session.commit()

    def entries_to_json(self, file=False):
        data = [e.to_json() for e in self.entries]
        if file:
            path = os.path.join(self.get_folder(), "entries.json")
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            return os.path.abspath(path)
        return data

    def entries_to_txt(self, directory=None):
        if not directory:
            directory = os.path.join(self.get_folder(), "txt")
        if not os.path.exists(directory):
            os.mkdir(directory)
        for i in range(0, len(self.entries)):
            with open(os.path.join(directory, f"{self.name}_entry-{i}.txt"), 'w') as f:
                f.write(self.entries[i].text)
        return directory

    def delete(self):
        project = Project.query.filter_by(id=self.id).first()
        project_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(self.id))
        shutil.rmtree(project_folder)
        db.session.delete(project)
        db.session.commit()

    def rename(self, new_name):
        self.name = new_name
        db.session.commit()

    def clear_split(self):
        pages = self.get_pages()
        for p in pages:
            os.remove(p.get_img())
            db.session.delete(p)
        self.is_split = False
        db.session.commit()