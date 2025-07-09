import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import io
from datetime import datetime
import re
import zipfile

# --- Constants ---
INDENT_FOR_IND_TAG_CM = 1.25
SUB_LETTER_HANGING_OFFSET_CM = 0.50
SUB_LETTER_TEXT_INDENT_NO_IND_CM = 1.25

# --- Cached Data Loading ---

@st.cache_data
def load_firm_details():
    """Loads and caches the law firm's details."""
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

@st.cache_data
def load_precedent_text():
    """Loads and caches the precedent text from a file."""
    try:
        with open("precedent.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        st.error("precedent.txt not found. Please ensure the file exists in the same directory.")
        return ""

# --- Document Generation Helpers ---

def get_placeholder_map(app_inputs, firm_details):
    """Creates a dictionary of all placeholders and their values."""
    placeholders = {
        "[qu1_dispute_nature]": app_inputs.get('qu1_dispute_nature', ""),
        "[qu2_initial_steps]": app_inputs.get('qu2_initial_steps', ""),
        "[qu3_timescales]": app_inputs.get('qu3_timescales', ""),
        "[qu4_initial_costs_estimate]": app_inputs.get('qu4_initial_costs_estimate', 'XX,XXX'),
        "{our_ref}": str(app_inputs.get('our_ref', '')),
        "{your_ref}": str(app_inputs.get('your_ref', '')),
        "{letter_date}": str(app_inputs.get('letter_date', '')),
        "{client_name_input}": str(app_inputs.get('client_name_input', '')),
        "{client_address_line1}": str(app_inputs.get('client_address_line1', '')),
        "{client_address_line2_conditional}": str(app_inputs.get('client_address_line2_conditional', '')),
        "{client_postcode}": str(app_inputs.get('client_postcode', '')),
        "{name}": str(app_inputs.get('name', ''))
    }
    # Add firm details to the placeholder map, e.g., {firm_name}
    firm_placeholders = {f"{{{k}}}": str(v) for k, v in firm_details.items()}
    placeholders.update(firm_placeholders)
    return placeholders

def add_formatted_runs(paragraph, text_line):
    """
    Adds text runs to a paragraph, processing inline formatting tags.
    Supported tags: [b], [italics], [u]/[underline]
    """
    parts = re.split(r'(\[b\]|\[/b\]|\[italics\]|\[/italics\]|\[u\]|\[/u\]|\[underline\]|\[/underline\])', text_line)
    is_bold = is_italic = is_underline = False
    for part in parts:
        if not part:
            continue
        if part == "[b]": is_bold = True
        elif part == "[/b]": is_bold = False
        elif part == "[italics]": is_italic = True
        elif part == "[/italics]": is_italic = False
        elif part in ["[u]", "[underline]"]: is_underline = True
        elif part in ["[/u]", "[/underline]"]: is_underline = False
        else:
            run = paragraph.add_run(part)
            run.bold = is_bold
            run.italic = is_italic
            run.underline = is_underline
            run.font.name = 'Arial'
            run.font.size = Pt(11)

def should_render_track_block(tag, claim_assigned, selected_track):
    """Determines if a court track block should be rendered based on the tag and inputs."""
    tag_map = {
        'a1': (True, "Small Claims Track"), 'a2': (True, "Fast Track"),
        'a3': (True, "Intermediate Track"), 'a4': (True, "Multi Track"),
        'u1': (False, "Small Claims Track"), 'u2': (False, "Fast Track"),
        'u3': (False, "Intermediate Track"), 'u4': (False, "Multi Track"),
    }
    expected = tag_map.get(tag)
    if not expected:
        return False
    expected_assignment, expected_track = expected
    return claim_assigned == expected_assignment and selected_track == expected_track

def generate_initial_advice_doc(app_inputs):
    """Generates the Initial Advice Summary Word document."""
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'HelveticaNeueLT Pro 45 Lt'
    style.font.size = Pt(11)

    p = doc.add_paragraph()
    p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    placeholder_map = get_placeholder_map(app_inputs, app_inputs['firm_details'])
    add_formatted_runs(p, f"Initial Advice Summary - Matter Number: {placeholder_map.get('[matter_number]', '')}")
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

# --- Streamlit App UI ---

st.set_page_config(layout="wide")
st.title("Ramsdens Client Care Letter Generator")

firm_details = load_firm_details()
precedent_content = load_precedent_text()

with st.form("input_form"):
    st.header("Letter Details")
    our_ref = st.text_input("Our Reference", "PP/LEGAL/RAM001/001")
    your_ref = st.text_input("Your Reference (if any)", "")
    letter_date = st.date_input("Letter Date", datetime.today())

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
    qu1_dispute_nature = st.text_area('We are instructed in relation to [your text below is inserted here - define the dispute] (the "Dispute").', "a contractual matter where you wish to bring a claim against your landlord", height=75)
    qu2_initial_steps = st.text_area('Per our recent discussions [when you came in to the office, or when we spoke on the phone, it was agreed that we would HERE YOU NEED TO SET OUT WHAT INITIAL WORK YOU AGREED TO DO] (the "Work").', "review the documentation you have provided and advise you on the merits of your case and set out the next steps", height=150)
    qu3_timescales = st.text_area("Q3: Estimated Timescales", "We estimate that to complete the initial advice for you we will take approximately two to fourt weeks to complete. Obviously, where other parties are involved this will depend on the complexity of the matter and the responsiveness of other parties. We will keep you updated on progress.", height=100)
    st.subheader("Q4: Estimated Initial Costs")
    lower_cost_estimate = st.number_input("Lower estimate (£)", value=1500, step=100)
    upper_cost_estimate = st.number_input("Upper estimate (£)", value=2000, step=100)

    submitted = st.form_submit_button("Generate Documents")

if submitted:
    vat_rate = 0.20
    lower_cost_vat = lower_cost_estimate * vat_rate
    upper_cost_vat = upper_cost_estimate * vat_rate
    lower_cost_total = lower_cost_estimate + lower_cost_vat
    upper_cost_total = upper_cost_estimate + upper_cost_vat

    costs_text = (
        f"£{lower_cost_estimate:,.2f} to £{upper_cost_estimate:,.2f} plus VAT "
        f"(currently standing at 20% but subject to change by the government) "
        f"which at the current rate would be £{lower_cost_total:,.2f} to £{upper_cost_total:,.2f} with VAT included."
    )

    app_inputs = {
        'qu1_dispute_nature': qu1_dispute_nature, 'qu2_initial_steps': qu2_initial_steps,
        'qu3_timescales': qu3_timescales, 'qu4_initial_costs_estimate': costs_text,
        'client_type': client_type,
        'claim_assigned': claim_assigned_input == "Yes", 'selected_track': selected_track,
        'our_ref': our_ref, 'your_ref': your_ref, 'letter_date': letter_date.strftime('%d %B %Y'),
        'client_name_input': client_name_input, 'client_address_line1': client_address_line1,
        'client_address_line2_conditional': client_address_line2 if client_address_line2 else "",
        'client_postcode': client_postcode, 'name': firm_details["person_responsible_name"],
        'initial_advice_content': initial_advice_content,
        'initial_advice_method': initial_advice_method, 'initial_advice_date': initial_advice_date,
        'firm_details': firm_details
    }

    placeholder_map = get_placeholder_map(app_inputs, firm_details)

    # --- Generate Client Care Letter ---
    doc = Document()
    doc.styles['Normal'].font.name = 'HelveticaNeueLT Pro 45 Lt'
    doc.styles['Normal'].font.size = Pt(11)

    in_indiv_block = in_corp_block = False
    active_track_block = None
    paragraph_counter = 0

    for line in precedent_content.splitlines():
        line = line.strip()

        # --- Block-level Tags ---
        if line.startswith("[indiv]"): in_indiv_block = True; continue
        if line.startswith("[/indiv]"): in_indiv_block = False; continue
        if line.startswith("[corp]"): in_corp_block = True; continue
        if line.startswith("[/corp]"): in_corp_block = False; continue
        
        track_tag_match = re.match(r'\[/?(a[1-4]|u[1-4])\]', line)
        if track_tag_match:
            tag = track_tag_match.group(1)
            if line.startswith('[/'):
                if active_track_block == tag:
                    active_track_block = None
            else:
                active_track_block = tag
            continue

        # --- Conditional Rendering ---
        if (in_indiv_block and app_inputs['client_type'] != "Individual") or \
           (in_corp_block and app_inputs['client_type'] != "Corporate") or \
           (active_track_block and not should_render_track_block(active_track_block, app_inputs['claim_assigned'], app_inputs['selected_track'])):
            continue
        
        if not line or line == "[]":
            if doc.paragraphs:
                doc.paragraphs[-1].paragraph_format.space_after = Pt(12)
            continue

        # --- Placeholder Replacement ---
        for placeholder, value in placeholder_map.items():
            line = line.replace(placeholder, str(value))

        # --- Paragraph Styling and Content ---
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        pf.space_after = Pt(0)
        
        text_content = line
        is_indented = "[ind]" in text_content
        if is_indented:
            text_content = text_content.replace("[ind]", "").lstrip()

        if text_content.startswith("[#]"):
            paragraph_counter += 1
            text_content = text_content.replace("[#]", f"{paragraph_counter}.", 1).lstrip()
            p.style = 'List Number'
        elif m := re.match(r'^\[([a-zA-Z])\](.*)', text_content):
            letter, rest = m.groups()
            text_content = f"({letter.lower()})\t{rest.lstrip()}"
            indent = INDENT_FOR_IND_TAG_CM + SUB_LETTER_HANGING_OFFSET_CM if is_indented else SUB_LETTER_TEXT_INDENT_NO_IND_CM
            pf.left_indent = Cm(indent)
            pf.first_line_indent = Cm(-SUB_LETTER_HANGING_OFFSET_CM)
            pf.tab_stops.add_tab_stop(Cm(indent))
        elif m := re.match(r'^\[(i{1,3}|iv)\](.*)', text_content):
            roman, rest = m.groups()
            text_content = f"({roman.lower()})\t{rest.lstrip()}"
            indent = INDENT_FOR_IND_TAG_CM + SUB_LETTER_HANGING_OFFSET_CM if is_indented else SUB_LETTER_TEXT_INDENT_NO_IND_CM
            pf.left_indent = Cm(indent)
            pf.first_line_indent = Cm(-SUB_LETTER_HANGING_OFFSET_CM)
            pf.tab_stops.add_tab_stop(Cm(indent))
        elif text_content.startswith("[bp]"):
            text_content = text_content.replace("[bp]", "", 1).lstrip()
            p.style = 'List Bullet'
            pf.space_after = Pt(6)
            if is_indented:
                pf.left_indent = Cm(INDENT_FOR_IND_TAG_CM)
        elif is_indented:
            pf.left_indent = Cm(INDENT_FOR_IND_TAG_CM)

        add_formatted_runs(p, text_content)

    client_care_doc_io = io.BytesIO()
    doc.save(client_care_doc_io)
    client_care_doc_io.seek(0)

    # --- Generate Initial Advice Document ---
    advice_doc_io = generate_initial_advice_doc(app_inputs)

    # --- Create ZIP file for Download ---
    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(f"Client_Care_Letter_{client_name_input.replace(' ', '_')}.docx", client_care_doc_io.getvalue())
        zipf.writestr(f"Initial_Advice_Summary_{client_name_input.replace(' ', '_')}.docx", advice_doc_io.getvalue())
    zip_io.seek(0)

    st.success("Documents Generated Successfully!")
    st.download_button(
        label="Download All Documents as ZIP",
        data=zip_io,
        file_name=f"Client_Documents_{client_name_input.replace(' ', '_')}.zip",
        mime="application/zip"
    )
