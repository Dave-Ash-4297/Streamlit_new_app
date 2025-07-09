import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import io
from datetime import datetime
import re
import zipfile

# Cache firm details to avoid redefinition
@st.cache_data
def load_firm_details():
    return {
        "name": "Ramsdens Solicitors LLP",
        "short_name": "Ramsdens",
        "person_responsible_name": "Paul Pinder",
        "person_responsible_title": "Senior Associate",
        "supervisor_name": "Nick Armitage",
        "supervisor_title": "Partner",
        "person_responsible_phone": "01484 821558",
        "person_responsible_mobile": "07923 250815",
        "person_responsible_email": "paul.pinder@ramsdens.co.uk",
        "assistant_name": "Reece Collier",
        "supervisor_contact_for_complaints": "Nick Armitage on 01484 507121",
        "bank_name": "Barclays Bank PLC",
        "bank_address": "17 Market Place, Huddersfield",
        "account_name": "Ramsdens Solicitors LLP Client Account",
        "sort_code": "20-43-12",
        "account_number": "03909026",
        "marketing_email": "dataprotection@ramsdens.co.uk",
        "marketing_address": "Ramsdens Solicitors LLP, Oakley House, 1 Hungerford Road, Edgerton, Huddersfield, HD3 3AL"
    }

# Load precedent text from file
@st.cache_data
def load_precedent_text():
    try:
        with open("precedent.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        st.error("precedent.txt not found. Please ensure the file exists in the same directory.")
        return ""

# Process inline formatting and placeholders
def add_runs_from_text(paragraph, text_line, app_inputs):
    placeholder_map = {
        "[qu1_dispute_nature]": app_inputs.get('qu1_dispute_nature', ""),
        "[qu2_initial_steps]": app_inputs.get('qu2_initial_steps', ""),
        "[qu3_timescales]": app_inputs.get('qu3_timescales', ""),
        "[qu4_initial_costs_estimate]": f"£{app_inputs.get('qu4_initial_costs_estimate', 'XX,XXX')}",
        "[matter_number]": str(app_inputs.get('matter_number', '')),
        "{our_ref}": str(app_inputs.get('our_ref', '')),
        "{your_ref}": str(app_inputs.get('your_ref', '')),
        "{letter_date}": str(app_inputs.get('letter_date', '')),
        "{client_name_input}": str(app_inputs.get('client_name_input', '')),
        "{client_address_line1}": str(app_inputs.get('client_address_line1', '')),
        "{client_address_line2_conditional}": str(app_inputs.get('client_address_line2_conditional', '')),
        "{client_postcode}": str(app_inputs.get('client_postcode', '')),
        "{name}": str(app_inputs.get('name', ''))
    }
    placeholder_map.update({f"{{{k}}}": str(v) for k, v in app_inputs.get('firm_details', {}).items()})

    for placeholder, value in placeholder_map.items():
        text_line = text_line.replace(placeholder, value)

    parts = re.split(r'(\[bold\]|\[end bold\]|\[italics\]|\[end italics\]|\[underline\]|\[end underline\]|\[end\])', text_line)
    is_bold = is_italic = is_underline = False
    for part in parts:
        if not part: continue
        if part == "[bold]": is_bold = True
        elif part == "[end bold]" or (part == "[end]" and is_bold): is_bold = False
        elif part == "[italics]": is_italic = True
        elif part == "[end italics]" or (part == "[end]" and is_italic): is_italic = False
        elif part == "[underline]": is_underline = True
        elif part == "[end underline]" or (part == "[end]" and is_underline): is_underline = False
        elif part == "[end]": is_bold = is_italic = is_underline = False
        else:
            run = paragraph.add_run(part)
            run.bold = is_bold
            run.italic = is_italic
            run.underline = is_underline
            run.font.name = 'Arial'
            run.font.size = Pt(11)

# Determine if a paragraph should be rendered
def should_render_paragraph(p_num, p_version, app_inputs):
    if not p_version: return True
    conditions = {
        '6': lambda v: (app_inputs['client_type'] == "Individual" and v == '1') or (app_inputs['client_type'] == "Corporate" and v != '1'),
        '18': lambda v: (app_inputs['client_type'] == "Individual" and v == '1') or (app_inputs['client_type'] == "Corporate" and v != '1'),
        '24': {
            '1': lambda: app_inputs['claim_assigned'] and app_inputs['selected_track'] == "Small Claims Track",
            '2': lambda: app_inputs['claim_assigned'] and app_inputs['selected_track'] == "Fast Track",
            '3': lambda: app_inputs['claim_assigned'] and app_inputs['selected_track'] == "Intermediate Track",
            '4': lambda: app_inputs['claim_assigned'] and app_inputs['selected_track'] == "Multi Track",
            '5': lambda: not app_inputs['claim_assigned'] and app_inputs['selected_track'] == "Small Claims Track",
            '6': lambda: not app_inputs['claim_assigned'] and app_inputs['selected_track'] == "Fast Track",
            '7': lambda: not app_inputs['claim_assigned'] and app_inputs['selected_track'] == "Intermediate Track",
            '8': lambda: not app_inputs['claim_assigned'] and app_inputs['selected_track'] == "Multi Track"
        }
    }
    if p_num == '24':
        return conditions[p_num].get(p_version, lambda: False)()
    return conditions.get(p_num, lambda v: True)(p_version)

# Parse precedent text into logical elements
def preprocess_precedent(precedent_text, app_inputs):
    logical_elements = []
    current_paragraph = None
    para_tag_regex = re.compile(r'\[(\d+)((?:-(\d+))?)\]')
    para_end_tag_regex = re.compile(r'\[/(\d+)((?:-(\d+))?)\]')

    for line in precedent_text.splitlines():
        while line:
            m_start = para_tag_regex.search(line)
            m_end = para_end_tag_regex.search(line)

            if current_paragraph:
                if m_end and m_end.group(1) == current_paragraph['num'] and \
                   (m_end.group(3) if m_end.group(2) else None) == current_paragraph['version']:
                    current_paragraph['lines'].append(line[:m_end.start()])
                    if current_paragraph['is_selected_for_render']:
                        logical_elements.append({
                            'type': 'paragraph_block',
                            'paragraph_display_number_text': f"{current_paragraph['num']}.",
                            'content_lines': current_paragraph['lines']
                        })
                    current_paragraph = None
                    line = line[m_end.end():]
                else:
                    current_paragraph['lines'].append(line)
                    line = ""
            elif m_start:
                if content_before_tag := line[:m_start.start()]:
                    logical_elements.append({'type': 'raw_line', 'content': content_before_tag})
                p_num = m_start.group(1)
                p_version = m_start.group(3) if m_start.group(2) else None
                current_paragraph = {
                    'num': p_num,
                    'version': p_version,
                    'lines': [],
                    'is_selected_for_render': should_render_paragraph(p_num, p_version, app_inputs),
                    'paragraph_display_number_text': f"{p_num}."
                }
                line = line[m_start.end():]
            else:
                if line: logical_elements.append({'type': 'raw_line', 'content': line})
                line = ""

    if current_paragraph and current_paragraph['is_selected_for_render'] and current_paragraph['lines']:
        logical_elements.append({
            'type': 'paragraph_block',
            'paragraph_display_number_text': current_paragraph['paragraph_display_number_text'],
            'content_lines': current_paragraph['lines']
        })
    return logical_elements

# Generate Initial Advice Summary document
def generate_initial_advice_doc(app_inputs):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'HelveticaNeueLT Pro 45 Lt'
    style.font.size = Pt(11)

    p = doc.add_paragraph()
    p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    add_runs_from_text(p, f"Initial Advice Summary - Matter Number: [matter_number]", app_inputs)
    p.paragraph_format.space_after = Pt(12)

    table = doc.add_table(rows=3, cols=2)
    table.style = 'Table Grid'
    table.autofit = True
    rows = [
        ("Date of Advice", app_inputs.get('initial_advice_date', '').strftime('%d %B %Y')),
        ("Method of Advice", app_inputs.get('initial_advice_method', '')),
        ("Advice Given", app_inputs.get('initial_advice_content', ''))
    ]
    for i, (label, value) in enumerate(rows):
        cells = table.rows[i].cells
        cells[0].text = label
        cells[1].text = value
        for cell in cells:
            cell.paragraphs[0].style.font.name = 'Arial'
            cell.paragraphs[0].style.font.size = Pt(11)
            cell.paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    table.columns[0].width = Cm(4.5)
    table.columns[1].width = Cm(10.0)

    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

# Streamlit App UI
st.set_page_config(layout="wide")
st.title("Ramsdens Client Care Letter Generator")

firm_details = load_firm_details()
precedent_content = load_precedent_text()

with st.form("input_form"):
    st.header("Letter Details")
    our_ref = st.text_input("Our Reference", "PP/LEGAL/RAM001/001")
    your_ref = st.text_input("Your Reference (if any)", "")
    letter_date = st.date_input("Letter Date", datetime.today())
    matter_number = st.text_input("Matter Number", "RAM001/001")

    st.header("Client Information")
    client_name_input = st.text_input("Client Full Name / Company Name", "Mr. John Smith")
    client_address_line1 = st.text_input("Client Address Line 1", "123 Example Street")
    client_address_line2 = st.text_input("Client Address Line 2", "SomeTown")
    client_postcode = st.text_input("Client Postcode", "EX4 MPL")
    client_type = st.radio("Client Type", ("Individual", "Corporate"))

    st.header("Initial Advice Details")
    initial_advice_content = st.text_area("Initial Advice Given", "Advised on the merits of the claim and potential next steps.", height=100)
    initial_advice_method = st.selectbox("Method of Initial Advice", ["Phone Call", "In Person", "Teams Call"])
    initial_advice_date = st.date_input("Date of Initial Advice", datetime.today())

    st.header("Case Details")
    claim_assigned_input = st.radio("Is the claim already assigned to a court track?", ("Yes", "No"))
    track_options = ["Small Claims Track", "Fast Track", "Intermediate Track", "Multi Track"]
    selected_track = st.selectbox("Which court track applies or is anticipated?", track_options)

    st.header("Dynamic Content")
    qu1_dispute_nature = st.text_area("Q1: Nature of the Dispute", "a contractual matter related to services provided", height=75)
    qu2_initial_steps = st.text_area("Q2: Immediate Steps to be Taken", "review the documentation you have provided and advise you on the merits of your position and potential next steps. we will also prepare an initial letter to the other side", height=150)
    qu3_timescales = st.text_area("Q3: Estimated Timescales", "We estimate that the initial Work will take approximately 2-4 weeks to complete, depending on the complexity and responsiveness of other parties. We will keep you updated on progress.", height=100)
    qu4_initial_costs_estimate = st.text_input("Q4: Estimated Initial Costs (e.g., 1,500)", "1,500")
    fee_table_content = st.text_area("Fee Table Content", "Partner: £XXX per hour\nSenior Associate: £YYY per hour\nSolicitor: £ZZZ per hour\nParalegal: £AAA per hour", height=150)

    submitted = st.form_submit_button("Generate Documents")

if submitted:
    app_inputs = {
        'qu1_dispute_nature': qu1_dispute_nature,
        'qu2_initial_steps': qu2_initial_steps,
        'qu3_timescales': qu3_timescales,
        'qu4_initial_costs_estimate': qu4_initial_costs_estimate,
        'fee_table_content': fee_table_content,
        'client_type': client_type,
        'claim_assigned': claim_assigned_input == "Yes",
        'selected_track': selected_track,
        'our_ref': our_ref,
        'your_ref': your_ref,
        'letter_date': letter_date.strftime('%d %B %Y'),
        'client_name_input': client_name_input,
        'client_address_line1': client_address_line1,
        'client_address_line2_conditional': client_address_line2 if client_address_line2 else "",
        'client_postcode': client_postcode,
        'name': firm_details["person_responsible_name"],
        'matter_number': matter_number,
        'initial_advice_content': initial_advice_content,
        'initial_advice_method': initial_advice_method,
        'initial_advice_date': initial_advice_date,
        'firm_details': firm_details
    }

    # Generate Client Care Letter
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'HelveticaNeueLT Pro 45 Lt'
    style.font.size = Pt(11)

    logical_elements = preprocess_precedent(precedent_content, app_inputs)
    lines_to_process = [
        {'text': e['content'], 'is_numbered_block_line': False} if e['type'] == 'raw_line' else
        {'text': line, 'is_numbered_block_line': i == 0 and line.strip()}
        for e in logical_elements if e['type'] == 'raw_line' or e['type'] == 'paragraph_block'
        for i, line in enumerate([e['content']] if e['type'] == 'raw_line' else e['content_lines'])
    ]

    INDENT_FOR_IND_TAG_CM = 1.25
    SUB_LETTER_HANGING_OFFSET_CM = 0.50
    SUB_LETTER_TEXT_INDENT_NO_IND_CM = 1.25
    in_indiv_block = in_corp_block = False
    active_track_block = None

    for line_item in lines_to_process:
        line = line_item['text'].strip()
        is_numbered = line_item['is_numbered_block_line']

        if line == "[indiv]": in_indiv_block = True; continue
        if line == "[end indiv]": in_indiv_block = False; continue
        if line == "[corp]": in_corp_block = True; continue
        if line == "[end corp]": in_corp_block = False; continue
        track_tags = ['[all_sc]', '[all_ft]', '[all_int]', '[all_mt]', '[sc]', '[ft]', '[int]', '[mt]']
        end_track_tags = ['[end all_sc]', '[end all_ft]', '[end all_int]', '[end all_mt]', '[end sc]', '[end ft]', '[end int]', '[end mt]']
        if line in track_tags: active_track_block = line; continue
        if line in end_track_tags and active_track_block and line == f"[end {active_track_block[1:-1]}]": active_track_block = None; continue

        if (in_indiv_block and app_inputs['client_type'] != "Individual") or \
           (in_corp_block and app_inputs['client_type'] != "Corporate") or \
           (active_track_block and not should_render_paragraph('24', active_track_block[1:-1].split('-')[-1] if '-' in active_track_block else None, app_inputs)):
            continue

        if line == "[]":
            if doc.paragraphs: doc.paragraphs[-1].paragraph_format.space_after = Pt(12)
            continue
        if not line: continue

        if line == "[FEE_TABLE_PLACEHOLDER]":
            for fee_line in app_inputs.get('fee_table_content', '').split('\n'):
                p = doc.add_paragraph()
                p.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
                p.paragraph_format.space_after = Pt(6)
                add_runs_from_text(p, fee_line, app_inputs)
            continue

        style_name = 'Normal'
        space_after = Pt(0)
        format_type = "normal"
        text_content = line

        if is_numbered:
            style_name = 'List Number'
            format_type = "main_numbered_auto"
        elif text_content.startswith("[ind]"):
            text_content = text_content.replace("[ind]", "", 1).lstrip()
            format_type = "ind_block_only"
        elif sub_letter_match := re.match(r'^\[([a-zA-Z])\](.*)', text_content):
            letter, rest = sub_letter_match.groups()
            text_content = f"({letter.lower()})\t{rest.lstrip()}"
            format_type = "sub_letter"
        elif text_content.startswith("[bp]"):
            style_name = 'ListBullet'
            text_content = text_content.replace("[bp]", "", 1).lstrip()
            space_after = Pt(6)
            format_type = "ind_bullet" if text_content.startswith("[ind]") else "bullet_auto"

        if not text_content.strip() and style_name == 'Normal': continue

        p = doc.add_paragraph(style=style_name)
        pf = p.paragraph_format
        pf.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        pf.tab_stops.clear_all()

        if format_type == "main_numbered_auto": pass
        elif format_type == "sub_letter":
            indent = INDENT_FOR_IND_TAG_CM + SUB_LETTER_HANGING_OFFSET_CM if "[ind]" in line else SUB_LETTER_TEXT_INDENT_NO_IND_CM
            pf.left_indent = Cm(indent)
            pf.first_line_indent = Cm(-SUB_LETTER_HANGING_OFFSET_CM)
            pf.tab_stops.add_tab_stop(Cm(indent))
        elif format_type == "bullet_auto": pass
        elif format_type == "ind_bullet": pf.left_indent = Cm(INDENT_FOR_IND_TAG_CM)
        elif format_type == "ind_block_only":
            pf.left_indent = Cm(INDENT_FOR_IND_TAG_CM)
            pf.first_line_indent = Cm(0)
            pf.tab_stops.add_tab_stop(Cm(INDENT_FOR_IND_TAG_CM))

        pf.space_after = space_after
        add_runs_from_text(p, text_content, app_inputs)

    if doc.paragraphs and doc.paragraphs[-1].paragraph_format.space_after == Pt(0):
        doc.paragraphs[-1].paragraph_format.space_after = Pt(6)

    client_care_doc_io = io.BytesIO()
    doc.save(client_care_doc_io)
    client_care_doc_io.seek(0)

    # Generate Initial Advice Document
    advice_doc_io = generate_initial_advice_doc(app_inputs)

    # Create ZIP file
    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(f"Client_Care_Letter_{client_name_input.replace(' ', '_')}.docx", client_care_doc_io.getvalue())
        zipf.writestr(f"Initial_Advice_Summary_{client_name_input.replace(' ', '_')}.docx", advice_doc_io.getvalue())
    zip_io.seek(0)

    st.success("Documents Generated!")
    st.download_button(
        label="Download All Documents",
        data=zip_io,
        file_name=f"Client_Documents_{client_name_input.replace(' ', '_')}.zip",
        mime="application/zip"
    )
