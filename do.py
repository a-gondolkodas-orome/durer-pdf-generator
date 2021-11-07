import csv
import logging
import os
from subprocess import Popen, DEVNULL
import jinja2
from jinja2.environment import Template
import tempfile
import shutil
import argparse

possible_categories = {'C kategória': 'C.tex', 'D kategória': 'D.tex'}
possible_places = set(['Budapest', 'Zenta', 'Miskolc', 'Eger', 'Hatvan'])
category_header = 'Kategória'
teamname_header = 'Csapatnév'
place_header = 'Helyszín'

# I/O
def get_place_directory(place):
    return os.path.join('target', place)

def ensure_dir(path):
    if not os.path.isdir(path):
        os.mkdir(path)
def initialize_output_directories():
    ensure_dir('target')
    for place in possible_places:
        ensure_dir(get_place_directory(place))

def load_templates():
    # JINJA2 latex templating https://www.miller-blog.com/latex-with-jinja2/
    latex_jinja_env = jinja2.Environment(
        block_start_string='\BLOCK{',
        block_end_string='}',
        variable_start_string='\VAR{',
        variable_end_string='}',
        comment_start_string='\#{',
        comment_end_string='}',
        line_statement_prefix='%%',
        line_comment_prefix='%#',
        trim_blocks=True,
        autoescape=False,
        loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'src'))
    )
    templates = {}

    for category_name in possible_categories:
        category_fn = possible_categories[category_name]
        templates[category_name] = latex_jinja_env.get_template(category_fn)
    return templates

class LatexCompileError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

def sanitize_teamname(s):
    return s.replace("_", "\\_")

def compile_tex(input_fn, output_dir):
    cmds = ['pdflatex', '-halt-on-error', f'-output-directory', output_dir, input_fn]
    # not used for real command
    cmd_sanitized_for_logging = ' '.join([arg.replace(' ', '\\ ') for arg in cmds])
    logging.debug(f"Running command {cmds}")
    logging.debug(f"   $ {cmd_sanitized_for_logging}")
    p = Popen(cmds, stdin=None, stdout=DEVNULL, stderr=DEVNULL)
    p.communicate()
    if p.returncode != 0:
        raise LatexCompileError(f"Failed to compile from {input_fn}. The file is still available for debugging")

templates = load_templates()

def instantiate_template(category, output_fn, **kwargs):
    with open(output_fn, 'w') as f:
        f.write(templates[category].render(**kwargs))

def lpad(s, n):
    s = str(s)
    l = len(s)
    if l < n:
        return (n-l)*"0"+s
    return s

def handle_team(id, row):
    logging.debug('Adding new team')
    category = row[category_header]
    teamname = row[teamname_header]
    place = row[place_header]
    good = True # write all warnings
    logging.info(f'Adding team {teamname}')
    if place not in possible_places:
        logging.error(f"Error: {place} not in {[*possible_places]}. Skipping.")
        good = False
    if category not in possible_categories:
        logging.error(f"Error: {category} not in {[*possible_categories.keys()]}. Skipping.")
        good = False
    if not good:
        return
    ids = lpad(id,3)
    output_tex = os.path.join("target", place, f"{ids}.tex")
    output_pdf = os.path.join("target", place, f"{ids}.pdf")
    output_dir = os.path.join("target", place)
    logging.debug(f"{teamname}; {place}; {category} -> {output_tex}")
    instantiate_template(category, output_tex, csapatnev=sanitize_teamname(teamname))
    try:
        compile_tex(output_tex, output_dir)
    except Exception:
        logging.error(f"Error happened while compiling {output_tex}")
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loglevel", choices=["DEBUG", "INFO", "WARNING", "ERROR"], nargs='?', default="INFO")
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    initialize_output_directories()

    try:
        with open('xv-helyi.tsv', 'r', newline='') as f:
            reader = csv.DictReader(f, delimiter='\t', quotechar='"')
            id=0
            if len(set(reader.fieldnames)) != len(reader.fieldnames):
                raise ValueError("Duplicate fieldname! Not going to proceed! Fix team table")
            for row in reader:
                handle_team(id, row)
                id += 1
    except Exception:
        print("Some error happened. If it was parsing, try")
        print("  - Running in debug level: python do.py --loglevel=DEBUG")
        print("  - Checking the output file at target/location/n.tex. Which file failed should be easy to determine.")
        raise

main()