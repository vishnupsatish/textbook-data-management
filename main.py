from unicodedata import normalize
from bs4 import BeautifulSoup
import os
import shutil
from jinja2 import Environment, FileSystemLoader, select_autoescape
from slugify import slugify

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape()
)


def rmw(txt):
    return " ".join(normalize('NFKD', txt).split())


ignore = {'.git'}

# Delete everything in /www that is not in the set 'ignore'; we don't want to delete
for filename in os.listdir('www'):
    if filename in ignore:
        continue
    file_path = os.path.join('www', filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))

# Parse HTML of the textbook using BeautifulSoup
with open('Textbook.html', 'r') as book_content:
    textbook = BeautifulSoup(book_content)

# Get CSS
textbook_style = textbook.head.style
# Add CSS style to www/textbook/style.css
os.mkdir('www/textbook')
with open('www/textbook/style.css', 'w+') as style_file:
    style_file.write(textbook_style.text)

textbook_body = list(textbook.body)

# Holds a dict. Key: name of main_section. Value: dict where key
# is name of title_section, value is ID of the title_section
all_sections = {
    'title': {}
}
current_main_section = 'title'
prev_cutoff = 0

only_book_template = env.get_template('only-book.html')


def make_textbook_file(name, start, end):
    with open(f'www/textbook/{name}.html', 'w+') as book:
        book.write(only_book_template.render(textbook_content='\n'.join(map(str, textbook_body[start:end])), body_class=' '.join(textbook.body['class'])))


shutil.copytree('templates/images', 'www/textbook/images')

shutil.copytree('templates/assets', 'www/assets')

print(*textbook.body['class'])

for i, element in enumerate(textbook_body):
    prev_element = textbook_body[i - 1]
    if rmw(element.text) == 'main_section':
        make_textbook_file(slugify(current_main_section), prev_cutoff, i - 1)
        prev_cutoff = i - 1
        current_main_section = rmw(prev_element.text)
        all_sections[current_main_section] = {}

    elif rmw(element.text) == 'title_section':
        all_sections[current_main_section][rmw(prev_element.text)] = prev_element['id']

make_textbook_file(slugify(current_main_section), prev_cutoff, len(textbook_body) - 1)

print(all_sections)

env.globals.update(slugify=slugify, all_sections=all_sections)

book_template = env.get_template('book-page.html')

for section in all_sections:
    with open(f'www/{slugify(section)}.html', 'w+') as book:
        book.write(book_template.render(current_main=slugify(section)))
