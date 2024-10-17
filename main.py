import pdfplumber
import re
import json

# Извлечение теста из PDF
def extract_text_from_pdf(pdf_path):
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        n = 1
        # Основная часть текста (после оглавлений) начинается с 14-ой страницы
        for page in pdf.pages[13:]:
            full_text += page.extract_text() + '\n'
            print(int((n/(358-13))*100), '%')
            n += 1
    return full_text.replace("■","").replace("○","")


# Получение словаря из текста
def parse_book(text):

    # инициализируем словарь
    book_structure = {}

    # номер и заголовок текущей главы
    current_chapter_number = None
    current_chapter_title = ""

    # номер и заголовок текущего раздела
    current_section_number = None
    current_section_title = ""

    # номер и заголовок текущего подраздела
    current_subsection_number = None
    current_subsection_title = ""

    # текущий текст
    current_text = ""

    # РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ:

    # номер главы (ГЛАВА 1)
    chapter_number_pattern = re.compile(r'^ГЛАВА\s?+(\d+)')

    # строка, в которой все буквы заглавные (КАПС ЛОК)
    all_caps_pattern = re.compile(r'^([A-ZА-Я\s]+)$')

    # номер и заголовок раздела (2.1 НОВЫЙ РАЗДЕЛ)
    section_pattern = re.compile(r'^(\d+\.\d+\.?)\s?+([A-ZА-Я\s,]+)$')

    # номер и заголовок подраздела (2.1.1 Новый подраздел)
    subsection_pattern = re.compile(r'^(\d+\.\d+\.\d+\.?)\s?+(.+)$')
    text_start_pattern = re.compile(r'^([А-Я][а-ёя\s]+)')
    
    # делим текст по строкам, получим список
    text_lines = text.splitlines()

    # функция внесения текста в словарь
    def save_text():
        nonlocal current_text
        if len(current_text) and current_chapter_number is not None:
            current_text_norm = current_text.replace("\n", " ").strip()
            if current_section_number is not None:
                current_section = \
                    book_structure[current_chapter_number]["sections"][current_section_number]
                
                if current_subsection_number is not None:
                    current_section["subsections"][current_subsection_number]["text"] = current_text_norm                        
                else:
                    current_section["text"] = current_text_norm

            else:
                book_structure[current_chapter_number]["text"] = current_text_norm
            
            current_text = ""

    # пройдем по каждой линии текста (нужны индексы, поэтому используем range)
    for i in range(0, len(text_lines)):

        # Проверяем является ли текущая строка номером главы (ГЛАВА 1)
        chapter_number_match = chapter_number_pattern.match(text_lines[i])
        if chapter_number_match:
            # перед началом новой главы, сохраняем старый текст в словарь
            save_text()

            # обнуляем номер и заголовок текущего раздела
            current_section_number = None
            current_section_title = ""

            # обнуляем номер и заголовок текущего подраздела
            current_subsection_number = None
            current_subsection_title = ""
            
            # определяем номер новой главы
            current_chapter_number = chapter_number_match.group(1)

            # инициализируем заголовок новой главы
            current_chapter_title = ""
            # переходим в следующую строку (так как заголовок главы начинается со следующей строки)
            j = i + 1

            # возьмем все последующие строки, которые написаны капс-локом (только заглавными),
            # объединяем их в одну строку (без переноса строки) как заголовок главы
            all_caps_match = all_caps_pattern.match(text_lines[j])
            while all_caps_match and j < len(text_lines):
                current_chapter_title += text_lines[j] + " "
                j += 1
                all_caps_match = all_caps_pattern.match(text_lines[j])  

            # записываем новую главу в словарь
            book_structure[current_chapter_number] = {
                'title': current_chapter_title.capitalize().strip()
            }
            
            # переходим в следующую итерацию (в следующую строку)
            continue

        # Проверяем является ли текущая строка номером и названием раздела (1.1 НОВЫЙ РАЗДЕЛ)
        section_match = section_pattern.match(text_lines[i])
        if section_match:
            # перед началом нового раздела, сохраняем текущий текст в словарь
            save_text()

            # обнуляем номер и название текущего подраздела
            current_subsection_number = None
            current_subsection_title = ""
            
            # получаем номер и название раздела
            current_section_number = section_match.group(1)
            current_section_title = section_match.group(2)

            # если в конце номера есть точка, то убираем
            if current_section_number[-1] == ".":
                current_section_number = current_section_number[:-1]

            # переходим в следующую строку для проверки продолжения названия раздела
            j = i + 1

            # возьмем все последующие строки, которые написаны капс-локом (только заглавными),
            # объединяем их в одну строку (без переноса строки) как заголовок раздела
            all_caps_match = all_caps_pattern.match(text_lines[j])
            while all_caps_match and j < len(text_lines):
                current_section_title += text_lines[j] + " "
                j += 1
                all_caps_match = all_caps_pattern.match(text_lines[j])
            
            # в словаре для текущей главы создаем под-словарь для разделов, если еще нет
            if 'sections' not in book_structure[current_chapter_number].keys():
                book_structure[current_chapter_number]['sections'] = {}

            # записываем новый раздел в словарь (в текущую главу)
            book_structure[current_chapter_number]['sections'][current_section_number] = {
                    'title': current_section_title.capitalize().strip()
            }

            # переходим в следующую итерацию (в следующую строку)
            continue

        # Проверяем является ли текущая строка номером и названием подраздела (1.1.1 Новый подраздел)
        subsection_match = subsection_pattern.match(text_lines[i])
        if subsection_match:
            # сначала сохраняем текущий текст
            save_text()

            # получаем номер и заголовок подраздела
            current_subsection_number = subsection_match.group(1)
            current_subsection_title = subsection_match.group(2)

            # убираем последнюю точку с номера, если есть
            if current_subsection_number[-1] == ".":
                current_subsection_number = current_subsection_number[:-1]

            # переходим в следующую строку для проверки продолжения заголовка
            j = i + 1

            # проверяем является ли строка началом текста
            # все последующие строки, не являющиеся текстом, 
            # записываем как продолжение заголовка подраздела
            is_text_start = text_start_pattern.match(text_lines[j])
            while not is_text_start and j < len(text_lines):
                current_subsection_title += text_lines[j] + " "
                j += 1
                is_text_start = text_start_pattern.match(text_lines[j])
            
            # в словаре для текущего раздела создаем под-словарь для подразделов, если еще нет
            if 'subsections' not in book_structure[current_chapter_number]["sections"][current_section_number].keys():
                book_structure[current_chapter_number]["sections"][current_section_number]["subsections"] = {}

            # записываем подраздел в словарь
            book_structure[current_chapter_number]["sections"][current_section_number]["subsections"][current_subsection_number] = {
                'title': current_subsection_title.strip()
            }

            # переходим в следующую итерацию (строку)
            continue
        
        # если строка не является номером и заголовком главы, раздела или подраздела,
        # то проверяем не является ли она продолжением заголовка
        if not all_caps_pattern.match(text_lines[i]):
            # если является частью (продолжением) заголовка, то игнорируем и продолжим итерацию
            if current_subsection_number is not None and current_text == "" and text_lines[i][0].islower():
                continue
            # иначе записываем как продолжение текущего текста
            else:
                current_text += text_lines[i] + " "

    # записываем текст в текущую главу, раздел или подраздел
    save_text()
    
    #  возвращаем полученный словарь
    return book_structure

# получаем текст
text = extract_text_from_pdf("mybook.pdf")

# словарь:
book_text_dict = parse_book(text)

# сохраняем в JSON--файл:
with open('struct.json', 'w', encoding='utf-8') as json_file:
    json.dump(book_text_dict, json_file, ensure_ascii=False, indent=4)










