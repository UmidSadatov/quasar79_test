import pdfplumber
import re
import json

def extract_text_from_pdf(pdf_path):
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[202:203]:
            full_text += page.extract_text() + '\n'
    return full_text.replace("■","").replace("○","")


def parse_book(text):
    book_structure = {}
    current_chapter_number = None
    current_chapter_title = ""

    current_section_number = None
    current_section_title = ""

    current_subsection_number = None
    current_subsection_title = ""

    current_text = ""
    
    chapter_number_pattern = re.compile(r'^ГЛАВА\s+(\d+)')
    all_caps_pattern = re.compile(r'^([A-ZА-Я\s]+)$')
    section_pattern = re.compile(r'^(\d+\.\d+)\s+([A-ZА-Я\s]+)$')
    subsection_pattern = re.compile(r'^(\d+\.\d+\.\d+)\s+(.+)$')
    text_start_pattern = re.compile(r'^([А-Я][а-ёя\s]+)')

    current_line = 0
    text_lines = text.splitlines()
    lines_total = len(text_lines)
    

    while current_line < lines_total:
        chapter_number_match = chapter_number_pattern.match(text_lines[current_line])
        if chapter_number_match:

            current_section_number = None
            current_section_title = ""

            current_subsection_number = None
            current_subsection_title = ""

            current_text = ""

            current_chapter_number = chapter_number_match.group(1)
            print(current_chapter_number)
            
            current_chapter_title = ""
            current_line += 1            
            is_all_caps = all_caps_pattern.match(text_lines[current_line])
            while is_all_caps:
                current_chapter_title += " " + text_lines[current_line]
                current_line += 1
                if current_line == lines_total - 1:
                    break
                is_all_caps = all_caps_pattern.match(text_lines[current_line])
            
            book_structure[current_chapter_number] = {
                "title": current_chapter_title.strip().capitalize(),
            }


        section_match = section_pattern.match(text_lines[current_line])
        if section_match:
            current_subsection_number = None
            current_subsection_title = ""

            current_text = ""

            current_section_number = section_match.group(1)
            current_section_title = section_match.group(2)

            current_line += 1
            
            is_all_caps = all_caps_pattern.match(text_lines[current_line])
            while is_all_caps:
                current_section_title += text_lines[current_line]
                current_line += 1
                if current_line == lines_total - 1:
                    break
                is_all_caps = all_caps_pattern.match(text_lines[current_line])

            book_structure[current_chapter_number]["sections"] = {
                current_section_number: {
                    "title": current_section_title.strip().capitalize()
                }
            }
        


        subsection_match = subsection_pattern.match(text_lines[current_line])
        if subsection_match:

            current_text = ""

            current_subsection_number = subsection_match.group(1)
            current_subsection_title = subsection_match.group(2)

            current_line += 1
            
            is_text_start = text_start_pattern.match(text_lines[current_line])
            while not is_text_start:
                current_subsection_title += text_lines[current_line]
                current_line += 1
                if current_line == lines_total:
                    break
                is_text_start = text_start_pattern.match(text_lines[current_line])

            book_structure[current_chapter_number]["sections"][current_section_number]["subsections"] = {
                current_subsection_number: {
                    "title": current_subsection_title.strip().capitalize()
                }
            }
    

        # is_text = True
        # while is_text and current_line < lines_total:
        #     current_text += text_lines[current_line] + ' '

        #     chapter_number_match = chapter_number_pattern.match(text_lines[current_line])
        #     section_match = section_pattern.match(text_lines[current_line])
        #     subsection_match = subsection_pattern.match(text_lines[current_line])


        #     if chapter_number_match or section_match or subsection_match:
        #         is_text = False
        #     current_line += 1
        

        if current_chapter_number is not None:

            if current_section_number is not None:

                if current_subsection_number is not None:
                    subsection_structure = book_structure[current_chapter_number]["sections"][current_section_number]["subsections"]
                    subsection_structure[current_subsection_number]["text"] = current_text.replace("\n", " ").strip()
                
                else:
                    book_structure[current_chapter_number]["sections"][current_section_number]["text"] = current_text.replace("\n", " ").strip()

            else:
                book_structure[current_chapter_number]["text"] = current_text.replace("\n", " ").strip()
            
            current_text = ""
        
        current_line += 1
        
            # current_chapter_number = None
            # current_chapter_title = ""

            # current_section_number = None
            # current_section_title = ""

            # current_subsection_number = None
            # current_subsection_title = ""

            # current_text = ""

            # current_line += 1


    return book_structure


# chapter_number_pattern = re.compile(r'^ГЛАВА\s+(\d+)')

# print(chapter_number_pattern.match("ГЛАВА 2").group(1))


# book_text = extract_text_from_pdf("mybook.pdf")


book_text_dict = parse_book(extract_text_from_pdf("mybook.pdf"))

with open('struct.json', 'w', encoding='utf-8') as json_file:
    json.dump(book_text_dict, json_file, ensure_ascii=False, indent=4)

# print(book_text)
