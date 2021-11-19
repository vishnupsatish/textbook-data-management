from unicodedata import normalize
from bs4 import BeautifulSoup
import os
import shutil
from jinja2 import Environment, FileSystemLoader, select_autoescape
from slugify import slugify
import requests
import tinycss2
from urllib.parse import unquote


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

shutil.copyfile('templates/index.html', 'www/index.html')

# Parse HTML of the textbook using BeautifulSoup
with open('Textbook.html', 'r') as book_content:
    textbook = BeautifulSoup(book_content)

# Parse HTML of the textbook (with images hyperlinked to Google) using BeautifulSoup
with open('Textbook_images_hyperlinked.html', 'r') as book_content:
    textbook_img_hyp = BeautifulSoup(book_content)


# Get and parse CSS
textbook_style = textbook.head.style
parsed_css = tinycss2.parse_stylesheet(textbook_style.text)

# Get the imported URL from Google Fonts using the CSS parser
import_url = parsed_css[0].prelude[1].arguments[0].value

# Get the text from the imported font URL (adding it directly as an @import throws a 403)
import_font = requests.get(import_url).text

os.mkdir('www/textbook')

# Add CSS style to www/textbook/style.css
with open('www/textbook/style.css', 'w+') as style_file:
    
    style_file.write(import_font + textbook_style.text)

textbook_body = list(textbook.body)
textbook_img_hyp_body = list(textbook_img_hyp.body)

# Holds a dict. Key: name of main_section. Value: dict where key
# is name of title_section, value is ID of the title_section
all_sections = {
    'title': ('', {})
}
current_main_section = 'title'
prev_cutoff = 0

only_book_template = env.get_template('only-book.html')


def make_textbook_file(name, start, end):
    with open(f'www/textbook/{name}.html', 'w+') as book:
        book.write(only_book_template.render(textbook_content='\n'.join(map(str, textbook_body[start:end])), body_class=' '.join(textbook.body['class'])))


shutil.copytree('templates/images', 'www/textbook/images')

shutil.copytree('templates/assets', 'www/assets')


img = textbook.findChildren('img')
img_hyp = textbook_img_hyp.findChildren('img')


# Replace all image equations to high-quality MathJax equations
for i, child in enumerate(img):
    element_img_hyp = img_hyp[i]
    if 'google.com/chart' in element_img_hyp.get('src', ''):
        equ = unquote(element_img_hyp['src'].split('chl=')[-1]).replace('\\+', '').replace('\\-', '')
        new_tag = textbook.new_tag("span")
        new_tag['class'] = 'mathjax-desmos'
        new_tag.string = f'\\({equ}\\)'
        img[i].replaceWith(new_tag)



for i, element in enumerate(textbook_body):
    prev_element = textbook_body[i - 1]
    if rmw(element.text) == 'main_section':
        make_textbook_file(slugify(current_main_section), prev_cutoff, i - 1)
        prev_cutoff = i - 1
        current_main_section = rmw(prev_element.text)
        all_sections[current_main_section] = (prev_element['id'], {})

    elif rmw(element.text) == 'title_section':
        all_sections[current_main_section][1][rmw(prev_element.text)] = prev_element['id']

make_textbook_file(slugify(current_main_section), prev_cutoff, len(textbook_body) - 1)

env.globals.update(slugify=slugify, all_sections=all_sections)

book_template = env.get_template('book-page.html')

for section in all_sections:
    with open(f'www/{slugify(section)}.html', 'w+') as book:
        book.write(book_template.render(current_main=slugify(section), section=section))
