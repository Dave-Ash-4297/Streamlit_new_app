import streamlit as st
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
# from docx.enum.style import WD_STYLE_TYPE # For custom styles if needed
import io
from datetime import datetime
import re

# --- Helper function to process inline formatting and placeholders ---
def add_runs_from_text(paragraph, text_line, app_inputs):
    # Centralized placeholder replacement
    text_line = text_line.replace("[qu 1 set out the nature of the dispute - start and end lower case]", app_inputs.get('qu1_dispute_nature', ""))
    text_line = text_line.replace("[qu 2 set out the immediate steps that will be taken (this maybe a review of the facts and papers to allow you to advise in writing or making initial court applications or taking the first step, prosecuting or defending in a mainstream action). If you have agreed to engage counsel or other third party to assist you should also say so here – start and end lower case]", app_inputs.get('qu2_initial_steps', ""))
    text_line = text_line.replace("[qu3 Explain the estimated time scales to complete the Work. Start capital and end full stop]", app_inputs.get('qu3_timescales', "")) 
    text_line = text_line.replace("qu3 Explain the estimated time scales to complete the initial and any ongoing Work. CAPITAL Start capital and end full stop \".\"", app_inputs.get('qu3_timescales', "")) 
    text_line = text_line.replace("£ [qu4_ what is the value of the estimated initial costs xx,xxx?]", f"£{app_inputs.get('qu4_initial_costs_estimate', 'XX,XXX')}")

    text_line = text_line.replace("{our_ref}", str(app_inputs.get('our_ref', '')))
    text_line = text_line.replace("{your_ref}", str(app_inputs.get('your_ref', '')))
    text_line = text_line.replace("{letter_date}", str(app_inputs.get('letter_date', '')))
    text_line = text_line.replace("{client_name_input}", str(app_inputs.get('client_name_input', '')))
    text_line = text_line.replace("{client_address_line1}", str(app_inputs.get('client_address_line1', '')))
    text_line = text_line.replace("{client_address_line2_conditional}", str(app_inputs.get('client_address_line2_conditional', '')))
    text_line = text_line.replace("{client_postcode}", str(app_inputs.get('client_postcode', '')))
    text_line = text_line.replace("{name}", str(app_inputs.get('name', ''))) 

    for key, val in app_inputs.get('firm_details', {}).items(): 
        text_line = text_line.replace(f"{{{key}}}", str(val))
        
    parts = re.split(r'(\[bold\]|\[end bold\]|\[italics\]|\[end italics\]|\[underline\]|\[end underline\]|\[end\])', text_line)
    is_bold = False
    is_italic = False
    is_underline = False
    for part in parts:
        if not part: continue
        if part == "[bold]": is_bold = True
        elif part == "[end bold]" or (part == "[end]" and is_bold): is_bold = False
        elif part == "[italics]": is_italic = True
        elif part == "[end italics]" or (part == "[end]" and is_italic): is_italic = False
        elif part == "[underline]": is_underline = True
        elif part == "[end underline]" or (part == "[end]" and is_underline): is_underline = False
        elif part == "[end]": is_bold = False; is_italic = False; is_underline = False
        else:
            run = paragraph.add_run(part)
            if is_bold: run.bold = True
            if is_italic: run.italic = True
            if is_underline: run.underline = True
            run.font.name = 'Arial'
            run.font.size = Pt(11)

# --- Helper to decide if an optional paragraph version should be rendered ---
def should_render_paragraph_version(p_num, p_version, app_inputs):
    if not p_version: return True
    if p_num == '6':
        is_indiv_version = (p_version == '1')
        return (app_inputs['client_type'] == "Individual" and is_indiv_version) or \
               (app_inputs['client_type'] == "Corporate" and not is_indiv_version)
    elif p_num == '18':
        is_indiv_version = (p_version == '1')
        return (app_inputs['client_type'] == "Individual" and is_indiv_version) or \
               (app_inputs['client_type'] == "Corporate" and not is_indiv_version)
    elif p_num == '24':
        is_allocated = app_inputs['claim_assigned']
        track = app_inputs['selected_track']
        if p_version == '1': return is_allocated and track == "Small Claims Track"
        if p_version == '2': return is_allocated and track == "Fast Track"
        if p_version == '3': return is_allocated and track == "Intermediate Track"
        if p_version == '4': return is_allocated and track == "Multi Track"
        if p_version == '5': return not is_allocated and track == "Small Claims Track"
        if p_version == '6': return not is_allocated and track == "Fast Track"
        if p_version == '7': return not is_allocated and track == "Intermediate Track"
        if p_version == '8': return not is_allocated and track == "Multi Track"
        return False
    return True 

# --- Pre-parser for precedent_content ---
def preprocess_precedent(precedent_text, app_inputs):
    logical_elements = []
    current_paragraph_builder = None 

    para_tag_regex = re.compile(r'\[(\d+)((?:-(\d+))?)\]')       
    para_end_tag_regex = re.compile(r'\[/(\d+)((?:-(\d+))?)\]') 

    for raw_line in precedent_text.splitlines():
        line_to_process = raw_line 

        while line_to_process:
            m_start = para_tag_regex.search(line_to_process)
            m_end = para_end_tag_regex.search(line_to_process)

            if current_paragraph_builder:
                current_block_end_pos = -1
                if m_end and m_end.group(1) == current_paragraph_builder['num'] and \
                   (m_end.group(3) if m_end.group(2) else None) == current_paragraph_builder['version']:
                    current_block_end_pos = m_end.start()
                
                if current_block_end_pos != -1: 
                    content_before_end_tag = line_to_process[:current_block_end_pos]
                    if content_before_end_tag: # Preserve empty lines if they are part of content
                         current_paragraph_builder['lines'].append(content_before_end_tag)
                    
                    if current_paragraph_builder['is_selected_for_render']:
                        logical_elements.append({
                            'type': 'paragraph_block',
                            'paragraph_display_number_text': current_paragraph_builder['paragraph_display_number_text'],
                            'content': "\n".join(current_paragraph_builder['lines'])
                        })
                    current_paragraph_builder = None
                    line_to_process = line_to_process[m_end.end():] 
                else: 
                    current_paragraph_builder['lines'].append(line_to_process)
                    line_to_process = "" 
            
            elif m_start: 
                content_before_tag = line_to_process[:m_start.start()]
                if content_before_tag: # Preserve empty lines if they are part of content
                    logical_elements.append({'type': 'raw_line', 'content': content_before_tag})

                p_num = m_start.group(1)
                p_version = m_start.group(3) if m_start.group(2) else None 

                selected = should_render_paragraph_version(p_num, p_version, app_inputs)
                
                current_paragraph_builder = {
                    'num': p_num, 
                    'version': p_version, 
                    'lines': [], 
                    'is_selected_for_render': selected,
                    'paragraph_display_number_text': f"{p_num}." # Use extracted number for display
                }
                line_to_process = line_to_process[m_start.end():] 
            
            else: 
                if line_to_process: # Preserve empty lines if they are part of content
                    logical_elements.append({'type': 'raw_line', 'content': line_to_process})
                line_to_process = "" 

    if current_paragraph_builder: 
        st.warning(f"Unterminated paragraph block: [{current_paragraph_builder['num']}"
                   f"{'-'+current_paragraph_builder['version'] if current_paragraph_builder['version'] else ''}]. "
                   f"Content included if selected.")
        if current_paragraph_builder['is_selected_for_render'] and current_paragraph_builder['lines']:
            logical_elements.append({
                'type': 'paragraph_block',
                'paragraph_display_number_text': current_paragraph_builder['paragraph_display_number_text'],
                'content': "\n".join(current_paragraph_builder['lines'])
            })
    return logical_elements

# --- Streamlit App UI ---
st.set_page_config(layout="wide")
st.title("Ramsdens Client Care Letter Generator")

firm_details = {
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

st.sidebar.header("Letter Details")
our_ref = st.sidebar.text_input("Our Reference", "PP/LEGAL/RAM001/001")
your_ref = st.sidebar.text_input("Your Reference (if any)", "")
letter_date = st.sidebar.date_input("Letter Date", datetime.today())

st.sidebar.header("Client Information")
client_name_input = st.sidebar.text_input("Client Full Name / Company Name", "Mr. John Smith")
client_address_line1 = st.sidebar.text_input("Client Address Line 1", "123 Example Street")
client_address_line2 = st.sidebar.text_input("Client Address Line 2", "SomeTown")
client_postcode = st.sidebar.text_input("Client Postcode", "EX4 MPL")
client_type = st.sidebar.radio("Client Type:", ("Individual", "Corporate"), key="client_type_radio")

st.sidebar.header("Case Details")
claim_assigned_input = st.sidebar.radio("Is the claim already assigned to a court track?",
                                   ("Yes", "No"), key="claim_assigned_radio")
track_options = ["Small Claims Track", "Fast Track", "Intermediate Track", "Multi Track"]
selected_track = st.sidebar.selectbox("Which court track applies or is anticipated?", track_options, key="track_select")


st.header("Dynamic Content (Answers to Questions)")
qu1_dispute_nature = st.text_area("Q1: Nature of the Dispute (for 'the Dispute')",
                                  "a contractual matter related to services provided", height=75)
qu2_initial_steps = st.text_area("Q2: Immediate Steps to be Taken (for 'the Work')",
                                 "review the documentation you have provided and advise you on the merits of your position and potential next steps. we will also prepare an initial letter to the other side", height=150)
qu3_timescales = st.text_area("Q3: Estimated Timescales for 'the Work'",
                              "We estimate that the initial Work will take approximately 2-4 weeks to complete, depending on the complexity and responsiveness of other parties. We will keep you updated on progress.", height=100)
qu4_initial_costs_estimate = st.text_input("Q4: Estimated Initial Costs for 'the Work' (e.g., 1,500)", "1,500")

fee_table_content = st.text_area("Fee Table Content (to be inserted in 'Costs and Disbursements')",
                                 "Partner: £XXX per hour\nSenior Associate: £YYY per hour\nSolicitor: £ZZZ per hour\nParalegal: £AAA per hour",
                                 height=150)

# --- Precedent Text (Your existing precedent_content string) ---
precedent_content = """
Our Ref: {our_ref}
Your Ref: {your_ref}
Date: {letter_date}
[]
{client_name_input}
{client_address_line1}
{client_address_line2_conditional}
{client_postcode}
[]
Dear {client_name_input},
[]
[1]Further to our recent discussions, we now write to confirm the terms under which Ramsdens Solicitors LLP [bold](“Ramsdens”)[end] will act for you. As a firm that is regulated by the Solicitors Regulation Authority, we are required to send you this letter which contains specific and prescribed information.[/1]
[]
[2]We enclose with this letter our Terms and Conditions of Business which must be read in conjunction with this letter. These documents are a formal communication and the language used is reflective of that. We hope that you understand. Please take the time to read these documents carefully. Where there is any conflict between this letter and our Terms and Conditions of Business, the terms of this letter will prevail. Your continuing instructions in this matter will amount to your acceptance of our Terms and Conditions of Business.[/2]
[]
[bold]Your Instructions[end]
[]
[3]We are instructed in relation to [qu 1 set out the nature of the dispute - start and end lower case] [bold](“the Dispute”)[/bold]. Per our recent discussions [qu 2 set out the immediate steps that will be taken (this maybe a review of the facts and papers to allow you to advise in writing or making initial court applications or taking the first step, prosecuting or defending in a mainstream action). If you have agreed to engage counsel or other third party to assist you should also say so here – start and end lower case] [bold](“the Work”)[end].[/3]
[]
[4]This matter may develop over time and the nature of disputes is that opposing parties often seek to present facts and matters in a way that is favourable to their own case. We therefore cannot predict every eventuality but we will work with you to advise on any significant developments and review the overall strategy should that be required. Insofar as changes in the future may have a material impact on any cost estimates provided, we will discuss that with you. We will notify you of any material changes by telephone or in correspondence and we will of course always confirm any verbal advice in writing whenever you request that from us.[/4]
[]
[bold]Timescales[end]
[]
[5]qu3 Explain the estimated time scales to complete the initial and any ongoing Work. CAPITAL Start capital and end full stop "." [/5]
[]
[bold]Action Required To Be Taken By You[end]
[]
[underline]Client Identification and Money Laundering[end]
[]
[indiv][6-1]Solicitors are required by law to obtain evidence of their client’s identity and address to satisfy money laundering and client identification regulations. This includes clients that are corporate entities.[/6-1][end indiv]
[corp][6-2]Solicitors are required by law to obtain evidence of their client’s identity and address to satisfy money laundering and client identification regulations. This includes clients that are corporate entities.
[a]We will make our own enquiries and obtain documentation from Companies House to identify our corporate client. If you believe Companies House’s records to be out of date, please let us know as soon as possible. We may also require documentation or information from the company itself.
[b]We are also obliged to identify the individuals at the corporate client who provide us with instructions, which usually means directors of limited companies or members/partners in LLPs, and sometimes we must do the same for “beneficial owners”. Either situation may include you as the recipient of this letter, but may also include other people at the business. We will tell you who else may be required to provide identification.[/6-2][end corp]
[]
[7]To comply with the individual identity requirement, you have two options:
[]
[a]We can carry out a remote ID verification of you and your ID documents using a SmartSearch facility. If you would like us to verify your identification remotely please provide your name, address, date of birth, personal email and mobile number. Once the search has been undertaken, SmartSearch will send you a text or email with a link to use on your smartphone which will require you to take a photo of your ID document and then yourself which it will then upload to its system that will check the document, provide us with a copy, and verify that you are the person on the ID document. The process is quick and easy, and avoids you having to send in ID documents to us. Or;
[]
[b]You can provide us with two documents referred to in the list below, one photographic and one showing your current address. If you are local to any of our offices please call with your original documents and they will be copied whilst you wait and the copies forwarded to us.
[bp]Current signed passport;
[bp]Household utility bill;
[bp]Residence permit issued by the Home Office to EEA nationals on sight of own country passport;
[bp]Current UK or EEA photo-card driving licence; or
[bp]National Identity Card containing a photograph.
[]
Please note that until these identification requirements have been satisfied, we may not be able to accept any money from you or make any substantial progress with your matter. It is therefore important that you provide your documents as soon as possible to avoid any delays.[/7]
[]
[underline]Document Preservation and Disclosure[end]
[]
[8]In the event that your matter is litigated before a Court, all parties will be required to give full disclosure of all material relevant to the Dispute. It is therefore essential that you preserve any and all such material that includes correspondence, documents, emails, text and SMS messages and/or other electronic communications of any sort. Your disclosure obligations include an obligation to disclose material that may harm your case or help your opponent’s case, as well as those on which you may rely or which help. If any device on which any such material is stored is to be disposed of or ceases to be used, you must ensure that copies are kept of the material.[/8]
[]
[bold]People Responsible For Your Case[end]
[]
[9]I shall be the person with responsibility for your case. My name is {person_responsible_name} and I am a {person_responsible_title} with the firm. My work will be carried out under the supervision of {supervisor_name} who is a {supervisor_title} of the firm.[/9]
[]
[10]The easiest way to communicate with me will be either by telephone on {person_responsible_phone}, my mobile {person_responsible_mobile}, or via email to {person_responsible_email}.[/10]
[]
[11]There may be occasions when I am not immediately available to speak or meet with you and in these circumstances you should ask to speak to my Assistant, {assistant_name} who will be able to help you.[/11]
[]
[12]At Ramsdens we aim to provide the best possible service to our clients and in order to do this we may arrange for one of our client care team to contact you to discuss how we are doing and what we might do better. Please let us know if you would prefer not to be contacted by our team during our handling of your matter. We do however, need to know from you if you feel dissatisfied about the service you are receiving. Should you have any occasion to feel unhappy about our service please let me know straight away and I will discuss this with you. If you are unable to resolve matters with me and still have concerns regarding our service, contact {supervisor_contact_for_complaints} who will attempt to resolve your concerns with you. Formal complaints will be dealt with in accordance with our Firm's complaints procedures which can be provided on request. In the event you are not satisfied with our handling of your complaint you can contact the Legal Ombudsman, full details will be given as part of our complaints procedure.[/12]
[]
[13]You also have a right to complain about any bill sent by us by applying to the Court for an assessment of the bill under Part III of the Solicitors Act 1974.[/13]
[]
[bold]Costs and Disbursements[end]
[]
[underline]Costs[end]
[]
[14]Our charges to you will be calculated and incurred on a time-spent basis. Time will be recorded on your matter in units of six minutes for letters (generally representing a unit per page or part thereof), emails written (again, representing a unit per equivalent to a page of normal letter) and telephone calls made and received.[/14]
[]
[15]Our current hourly charge-out rates, exclusive of VAT, are as follows:
[]
[FEE_TABLE_PLACEHOLDER]
[]
Our hourly charge-out rates are reviewed periodically and we will notify you of any increases. We will also notify you of any changes in the status of legal personnel and their hourly charge-out rate. Unless otherwise agreed with you, we will account to you every month for the fees that have been incurred in relation to this matter. If you require an up to date statement of fees incurred at any time then please ask us and we will provide you with that information. Unless otherwise stated, interim bills are on account of costs and are usually prepared taking into account the value of the time recorded against the matter as at the date of the interim bill. If we hold any monies on account of your costs when an invoice is raised, these monies will be utilised towards discharging the invoice.[/15]
[]
[underline]Disbursements[end]
[]
[16]Our hourly charge-out rates do not include expenses for which we will be responsible on your behalf. These expenses are referred to as disbursements and may include travel or accommodation expenses, Court fees or the costs of Barristers or expert witnesses. Where possible, we will endeavour to seek your permission prior to instructing a third party in relation to your matter.[/16]
[]
[17]We will not pay out any disbursements on your behalf until the monies have been paid by you.[/17]
[]
[underline]Legal Expenses Insurance[end]
[]
[indiv][18-1]It may be that you or a member of your household has the benefit of legal expenses insurance that might cover you for legal costs in connection with this matter. If you wish us to check your eligibility, please let us have a copy of the relevant insurance schedule and policy document. Alternatively you may be entitled to have your liability for costs paid by another person; for example, an employer or Trade Union. Again, please let us know if you wish us to assist you in checking such eligibility. Please note that you will remain responsible for our charges until such time as any legal expenses insurers have agreed to cover you for our legal costs.[/18-1][end indiv]
[corp][18-2]It may be possible to purchase “After the Event” legal expenses insurance cover to cover your opponents, or, possibly, your costs in this matter. If you wish to explore the possibility of such insurance cover, please let us know. Please bear in mind, though, that there will be costs involved in making an application for cover, and it is likely that a large premium (the amount of which will depend on the amount of costs protected and the prospects of success) will be payable at the outset and possibly on any subsequent anniversary of the inception of the policy.[/18-2][end corp]
[]
[underline]Your Costs Responsibility to Ramsdens[end]
[]
[19]Our charges to you are not contingent upon the result of your case. You are primarily responsible for the payment of our costs and disbursements. Whilst we may be able to recover a portion of your costs from your opponent, this is not always possible and does not affect your primary responsibility to pay our costs and disbursements.[/19]
[]
[underline]Section 74 Solicitors Act 1974 Agreement & Recovery of Costs[end]
[]
[20]It is common in litigation that even where costs are recoverable from an opponent, such recovery will not equate to the level of costs incurred by the successful party. Our agreement expressly permits us to charge an amount of costs greater than that which you will recover or could have recovered from your opponent, and expressly permits payment of such sum.[/20]
[]
[21]This part of our agreement is made under section 74(3) of the Solicitors Act 1974 and Civil Procedure Rules 46.9 (2) and (3).[/21]
[]
[22]If a Court orders your opponent to pay your costs, you should be aware that:
[]
[a]You will have to pay the costs to us in the first instance and you may then be reimbursed when cleared funds are received from your opponent.
[b]You are unlikely to recover the entirety of our charges from your opponent. In most cases there will be a shortfall between our charges to you and the amount of costs that you may recover from your opponent. This shortfall may arise because your claim is subject to the fixed recoverable costs regime (see below) or because there is a difference between our hourly charge-out rates and the guideline hourly charge-out rates that are considered by the Court when assessing some costs. In so far as any costs or disbursements are of an unusual nature or amount, these costs might not be recoverable from your opponent.
[c]In the unlikely event that your claim is subject to the fixed recoverable costs regime (see below) and the fixed costs recoverable from your opponent exceed the level of our charges calculated and incurred on a time-spent basis, you agree that the charges due to us from you will be the amount of fixed costs recoverable from your opponent.
[d]Your opponent may refuse to comply with the Court’s order. If they do not pay, then you may seek to enforce the Court’s order (for example by sending in the bailiffs or obtaining a charge over property owned by them). However, you should be aware that this itself costs more money and takes time.
[e]Your opponent may have very little by way of assets or they may simply disappear. If this happens then you will not be able to recover your costs or indeed any other monies awarded to you. That is why it is important that in financial disputes you consider now whether your opponent has sufficient assets to pay you a lump sum or instalments as appropriate.
[f]There may be points during your case (including at its conclusion) where you are successful only in part on the issues in it, as a result of which you are entitled to payment of some of your costs by your opponent.
[g]If your opponent receives funding from the Community Legal Service, there are statutory controls on the amount of costs that can be recovered from them. In these circumstances, it is highly unlikely that the Court will make an order that your opponent would have to contribute anything to your costs.[/22]
[]
[underline]Fixed Recoverable Costs[end]
[]
[23]Depending upon the value and complexity of a claim, the Court will allocate it to one of four ‘tracks’ when managing the case. If a claim is successful and a Court orders one party to pay the other’s costs, the amount of the costs that can be recovered may be fixed by the Court.[/23]
[]
[all_sc][24-1]From the information that you have supplied us with, the claim has already been allocated to the Small Claims Track which is the normal track for claims with a monetary value of £10,000 or less.
[]
Having been allocated to the Small Claims Track, the normal rule is that only the following limited costs are recoverable by a successful party:
[bp]Any Court fees paid.
[bp]Fixed issue costs ranging between £50 and £125.
[bp]Loss of earnings not exceeding £95 per person per day.
[bp]Expenses reasonably incurred in travelling to and from and attending a Court hearing
[bp]A sum not exceeding £750 for any expert’s fees.
[]
There are some exceptions to the normal rule and the Court can award costs against a party that has acted unreasonably. However, in practice such awards are rare.[/24-1][end all_sc]
[all_ft][24-2]From the information that you have supplied us with, the claim has already been allocated to the Fast Track which is the normal track for claims with a monetary value of between £10,000 and £25,000.
[]
Having been allocated to the Fast Track, the Court has also assigned your/your opponent’s claim to a Band 1/2/3/4. This means that as the Claimant/Defendant in the proceedings, we know that the costs that may be recoverable from your opponent/you will be fixed dependent upon the stage of the proceedings in which the claim is resolved. A table setting out these fixed recoverable costs is enclosed with this letter.[/24-2][end all_ft]
[all_int][24-3]From the information that you have supplied us with, the claim has already been allocated to the Intermediate Track which is the normal track for claims with a monetary value of between £25,000 and £100,000.
[]
Having been allocated to the Intermediate Track, the Court has also assigned your/your opponent’s claim to Band 1/2/3/4. This means that as the Claimant/Defendant in the proceedings, we know that the costs that may be recoverable from your opponent/you will be fixed dependent upon the stage of the proceedings in which the claim is resolved. A table setting out these fixed recoverable costs is enclosed with this letter.[/24-3][end all_int]
[all_mt][24-4]From the information that you have supplied us with, the claim has already been allocated to the Multi-Track which is the normal track for claims with a monetary value of over £100,000.
[]
Having been allocated to the Multi-Track, this means that the fixed costs regime does not apply to your/your opponent’s claim and the general rule that the ‘loser pays the winner’s costs’ will apply, subject to any costs budgeting that has been implemented by the Court and the caveats set out above under the heading [italics]Section 74 Solicitors Act 1974 Agreement & Recovery of Costs[end italics].[/24-4][end all_mt]
[sc][24-5]From the information that you have supplied us with, it is likely that were Court proceedings to be commenced, the claim would be allocated to the Small Claims Track which is the normal track for claims with a monetary value of £10,000 or less.
[]
Upon allocation to the Small Claims Track, the normal rule is that only the following limited costs are recoverable by a successful party:
[]
[bp]Any Court fees paid.
[bp]Fixed issue costs ranging between £50 and £125.
[bp]Loss of earnings not exceeding £95 per person per day.
[bp]Expenses reasonably incurred in travelling to and from and attending a Court hearing
[bp]A sum not exceeding £750 for any expert’s fees.
[]
There are some exceptions to the normal rule and the Court can award costs against a party that has acted unreasonably. However, in practice such awards are rare.[/24-5][end sc]
[ft][24-6]From the information that you have supplied us with, it is likely that were Court proceedings to be commenced, the claim would be allocated to the Fast Track which is the normal track for claims with a monetary value of between £10,000 and £25,000.
[]
Upon allocation to the Fast Track, the Court will assign your/your opponent’s claim to one of four ‘bands’ depending upon the complexity and number of issues in the claim. When the claim is assigned, as the Claimant/Defendant in the proceedings, we will know that the costs that may be recoverable from your opponent/you will be fixed dependent upon the stage of the proceedings in which the claim is resolved. A table setting out these fixed recoverable costs is enclosed with this letter.[/24-6][end ft]
[int][24-7]From the information that you have supplied us with, it is likely that were Court proceedings to be commenced, the claim would be allocated to the Intermediate Track which is the normal track for claims with a monetary value of between £25,000 and £100,000.
[]
Upon allocation to the Intermediate Track, the Court will assign your/your opponent’s claim to one of four ‘bands’ depending upon the complexity and number of issues in the claim. When the claim is assigned, as the Claimant/Defendant in the proceedings, we will know that the costs that may be recoverable from your opponent/you will be fixed dependent upon the stage of the proceedings in which the claim is resolved. A table setting out these fixed recoverable costs is enclosed with this letter.[/24-7][end int]
[mt][24-8]From the information that you have supplied us with, it is likely that were Court proceedings to be commenced, the claim would be allocated to the Multi-Track which is the normal track for claims with a monetary value of in excess of £100,000.
[]
Upon allocation to the Multi-Track, the fixed costs regime will not apply to your/your opponent’s claim and the general rule that the ‘loser pays the winner’s costs’ will apply, subject to any costs budgeting that has been implemented by the Court and the caveats set out above under the heading [italics]Section 74 Solicitors Act 1974 Agreement & Recovery of Costs[end italics].[/24-8][end mt]
[]
[underline]Costs Advice[end]
[]
[25]From the information you have provided us with to date, we estimate that our costs for the initial stage of the Work will be £ [qu4_ what is the value of the estimated initial costs xx,xxx?] plus VAT. If any further work is required thereafter, we will discuss the likely associated costs with you beforehand.[/25]
[]
[26]It is always difficult to give an indication of the likely costs to be incurred in cases of this type. This is because it is impossible to say at this stage when the case may be brought to a conclusion and the amount of work that may be required to reach that point. The vast majority of cases are settled without the need for Court proceedings and of those where Court proceedings are commenced, the majority are settled without a trial. The actual amount of costs to be incurred will depend upon the arguments being advanced and the amount and nature of the evidence involved. The more evidence that is required, the greater the amount of time that will be spent on it by the parties and the Court and, therefore, the greater the costs.[/26]
[]
[27]The involvement of expert evidence (such as in the form of valuation evidence) will also contribute to an increase in the costs involved.[/27]
[]
[28]In the event that it may appear that our initial estimate of costs may be exceeded, we will notify you of these changes. We will review our estimate of costs at least every six months.[/28]
[]
[29]There may be occasions during the conduct of your case where significant disbursements or major amounts of chargeable time are due to be incurred. We reserve the right to seek payment in advance for these commitments, and routinely do so. In the event that we do seek such payment in advance and it is not made by any reasonable deadline set, we reserve the right to cease acting for you in this matter. In the event that we do cease to act we would attempt to mitigate the impact that doing so would have on your case but it is possible that your case may be prejudiced as a result. We also reserve the right to cease acting for you in the event that any bills rendered to you are not paid within the timescale required.[/29]
[]
[30]To this extent, you agree with us that our retainer in this matter is not to be considered an entire agreement, such that we are not obliged to continue acting for you to the conclusion of the matter and are entitled to terminate your retainer before your case is concluded. We are required to make this clear because there has been legal authority that in the absence of such clarity a firm was required to continue acting in a case where they were no longer being funded to do so.[/30]
[]
[31]You have a right to ask for your overall cost to be limited to a maximum and we trust you will lialiaise with us if you wish to limit your costs. We will not then exceed this limit without first obtaining your consent. However this does mean that your case may not be concluded if we have reached your cost limit.[/31]
[]
[32]In Court or some Tribunal proceedings, you may be ordered to pay the costs of someone else, either in relation to the whole of the costs of the case if you are unsuccessful or in relation to some part or issue in the case. Also, you may be ordered to pay the costs of another party during the course of proceedings in relation to a particular application to the Court. In such case you will need to provide this firm with funds to discharge such liability within seven days as failure to do so may prevent your case progressing. Please be aware that once we issue a Court or certain Tribunal claims or counterclaim on your behalf, you are generally unable to discontinue your claim or counterclaim without paying the costs of your opponent unless an agreement on costs is reached.[/32]
[]
[bold]Limitation of Liability[end]
[]
[33]The liability of Ramsdens Solicitors LLP, its partners and employees in any circumstances whatsoever, whether in contract, tort, statute or otherwise and howsoever caused (including our negligence) for loss or damage arising from or in connection with the provision of services to you shall be limited to the sum of £3,000,000.00 (three million pounds) excluding costs and interest.[/33]
[]
[bold]Bank Accounts and Cybercrime[end]
[]
[34]Should we ask you to pay money to us during the course of your matter then please send your funds to our account held with {bank_name} at {bank_address} to:
[]
[ind]Account Name: {account_name}
[ind]Sort Code: {sort_code}
[ind]Account Number: {account_number}[/34]
[]
[35]Should you receive any email correspondence regarding our bank account details please telephone your usual contact at Ramsdens before sending your first payment to verify that the details you have been given are correct. We would never advise our clients of any change in our bank account details by email. Should this happen please treat the email as suspicious and contact us immediately. Please do not send any funds until you have verified that the details are correct.[/35]
[]
[36]Similarly, if an occasion arises whereby we need to send money to you, we will not accept your bank account details by email without further verification. It is likely that we will telephone you to confirm that the details supplied to us are correct.[/36]
[]
[bold]Quality Standard[end]
[]
[37]Our firm is registered under the Lexcel quality standard of the Law Society. As a result of this we are or may become subject to periodic checks by outside assessors. This could mean that your file is selected for checking, in which case we would need your consent for inspection to occur. All inspections are, of course, conducted in confidence. If you prefer to withhold consent, work on your file will not be affected in any way. Since very few of our clients do object to this we propose to assume that we do have your consent unless you notify us to the contrary. We will also assume, unless you indicate otherwise, that consent on this occasion will extend to all future matters which we conduct on your behalf. Please do not hesitate to contact us if we can explain this further or if you would like us to mark your file as not to be inspected. Alternatively if you would prefer to withhold consent please put a line through this section in the copy letter and return to us.[/37]
[]
[bold]Data Protection[end]
[]
[38]The enclosed Privacy Notice explains how and why we collect, store, use and share your personal data. It also explains your rights in relation to your personal data and how to contact us or supervisory authorities in the event you have a complaint. Please read it carefully. This Privacy Notice is also available on our website, www.ramsdens.co.uk.[/38]
[]
[39]Our use of your personal data is subject to your instructions, the EU General Data Protection Regulation (GDPR), other relevant UK and EU legislation and our professional duty of confidentiality. Under data protection law, we can only use your personal data if we have a proper reason for doing so. Detailed reasons why we may process your personal data are set out in our Privacy Notice but examples are:[/39]
[]
[a]To comply with our legal and regulatory obligations;
[b]For the performance of our contract with you or to take steps at your request before entering into a contract; or
[c]For our legitimate interests or those of a third party, including:
[ind][bp]Operational reasons, such as recording transactions, training and quality control;
[ind][bp]Updating and enhancing client records;
[ind][bp]Analysis to help us manage our practice; and
[ind][bp]Marketing, such as by sending you updates about subjects and/or events that may be of interest to you.[/39]
[]
[40]However, this does not apply to processing sensitive personal data about you, as defined. If it is necessary to process this data for the continued provision of our services to you, we will need your explicit consent for doing so and will request this from you as required.[/40]
[]
[bold]Marketing Communications[end]
[]
[41]We would like to use your personal data to send you updates (by email, telephone or post) about legal developments that might be of interest to you and/or information about our services.[/41]
[]
[42]This will be done pursuant to our Privacy Notice (referred to above), which contains more information about our and your rights in this respect.[/42]
[]
[43]You have the right to opt out of receiving promotional communications at any time, by:
[]
[a]Contacting us by email on {marketing_email};
[b]Using the ‘unsubscribe’ link in emails; or
[c]Writing to Marketing Department at: {marketing_address}.[/43]
[]
Yours sincerely,
[]
[]
[]
{name}
Solicitor
""".strip()


if st.button("Generate Client Care Letter"):
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
        'firm_details': firm_details 
    }

    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)

    logical_document_elements = preprocess_precedent(precedent_content, app_inputs)

    in_indiv_block = False
    in_corp_block = False
    active_track_block = None 

    for element in logical_document_elements:
        lines_to_render_for_docx = []
        is_from_numbered_block = False 

        if element['type'] == 'raw_line':
            stripped_content = element['content'].strip()

            if stripped_content == "[indiv]": in_indiv_block = True; continue
            if stripped_content == "[end indiv]": in_indiv_block = False; continue
            if stripped_content == "[corp]": in_corp_block = True; continue
            if stripped_content == "[end corp]": in_corp_block = False; continue

            track_tags = ['[all_sc]', '[all_ft]', '[all_int]', '[all_mt]', '[sc]', '[ft]', '[int]', '[mt]']
            end_track_tags = ['[end all_sc]', '[end all_ft]', '[end all_int]', '[end all_mt]', '[end sc]', '[end ft]', '[end int]', '[end mt]']
            
            is_track_start_tag = False
            for tag in track_tags:
                if stripped_content == tag: active_track_block = tag; is_track_start_tag = True; break
            if is_track_start_tag: continue

            is_track_end_tag = False
            for tag in end_track_tags:
                if stripped_content == tag:
                    if active_track_block and tag == f"[end {active_track_block[1:-1]}]": active_track_block = None
                    is_track_end_tag = True; break
            if is_track_end_tag: continue
            
            if in_indiv_block and app_inputs['client_type'] != "Individual": continue
            if in_corp_block and app_inputs['client_type'] != "Corporate": continue
            
            if active_track_block:
                should_render_current_track_content = False
                is_allocated = app_inputs['claim_assigned']; track_name = app_inputs['selected_track']
                if active_track_block == '[all_sc]' and is_allocated and track_name == "Small Claims Track": should_render_current_track_content = True
                elif active_track_block == '[all_ft]' and is_allocated and track_name == "Fast Track": should_render_current_track_content = True
                elif active_track_block == '[all_int]' and is_allocated and track_name == "Intermediate Track": should_render_current_track_content = True
                elif active_track_block == '[all_mt]' and is_allocated and track_name == "Multi Track": should_render_current_track_content = True
                elif active_track_block == '[sc]' and not is_allocated and track_name == "Small Claims Track": should_render_current_track_content = True
                elif active_track_block == '[ft]' and not is_allocated and track_name == "Fast Track": should_render_current_track_content = True
                elif active_track_block == '[int]' and not is_allocated and track_name == "Intermediate Track": should_render_current_track_content = True
                elif active_track_block == '[mt]' and not is_allocated and track_name == "Multi Track": should_render_current_track_content = True
                if not should_render_current_track_content: continue
            
            lines_to_render_for_docx.append(element['content']) 

        elif element['type'] == 'paragraph_block':
            if in_indiv_block and app_inputs['client_type'] != "Individual": continue
            if in_corp_block and app_inputs['client_type'] != "Corporate": continue
            if active_track_block: 
                should_render_current_track_content = False
                is_allocated = app_inputs['claim_assigned']; track_name = app_inputs['selected_track'] 
                if active_track_block == '[all_sc]' and is_allocated and track_name == "Small Claims Track": should_render_current_track_content = True
                elif active_track_block == '[all_ft]' and is_allocated and track_name == "Fast Track": should_render_current_track_content = True
                elif active_track_block == '[all_int]' and is_allocated and track_name == "Intermediate Track": should_render_current_track_content = True
                elif active_track_block == '[all_mt]' and is_allocated and track_name == "Multi Track": should_render_current_track_content = True
                elif active_track_block == '[sc]' and not is_allocated and track_name == "Small Claims Track": should_render_current_track_content = True
                elif active_track_block == '[ft]' and not is_allocated and track_name == "Fast Track": should_render_current_track_content = True
                elif active_track_block == '[int]' and not is_allocated and track_name == "Intermediate Track": should_render_current_track_content = True
                elif active_track_block == '[mt]' and not is_allocated and track_name == "Multi Track": should_render_current_track_content = True
                if not should_render_current_track_content: continue

            block_internal_lines = element['content'].split('\n')
            para_num_display_str = element['paragraph_display_number_text'] # Use the extracted number + "."
            has_added_number_to_block = False
            for internal_line_raw in block_internal_lines:
                current_text_for_this_docx_para = internal_line_raw 
                if not has_added_number_to_block and internal_line_raw.strip(): 
                    current_text_for_this_docx_para = f"{para_num_display_str} {internal_line_raw.lstrip()}"
                    has_added_number_to_block = True
                lines_to_render_for_docx.append(current_text_for_this_docx_para)
            is_from_numbered_block = True

        for line_for_docx_processing_raw in lines_to_render_for_docx:
            line_for_docx_processing = line_for_docx_processing_raw.strip() 

            # Preserve raw line for "[]" and empty lines from original template not inside a block
            if line_for_docx_processing_raw.strip() == "[]":
                if doc.paragraphs: doc.paragraphs[-1].paragraph_format.space_after = Pt(12)
                continue
            elif not line_for_docx_processing and not is_from_numbered_block: # Empty line from template
                 if doc.paragraphs: doc.paragraphs[-1].paragraph_format.space_after = Pt(12)
                 continue # Don't add an actual empty paragraph unless it's for signature lines (handled by [] typically)
            elif not line_for_docx_processing and is_from_numbered_block: # Empty line within a block (e.g. "[]" was inside [xx]...[/xx])
                # This effectively is like a "[]" within a numbered block's content
                if doc.paragraphs: doc.paragraphs[-1].paragraph_format.space_after = Pt(12)
                continue

            current_paragraph_style_name = 'Normal'
            left_indent_value = None
            space_after_val_pt = Pt(0) 

            if line_for_docx_processing == "[FEE_TABLE_PLACEHOLDER]":
                fee_lines_content = app_inputs.get('fee_table_content', '').split('\n')
                for fee_item_line in fee_lines_content:
                    p_fee = doc.add_paragraph()
                    p_fee.paragraph_format.space_after = Pt(6)
                    add_runs_from_text(p_fee, fee_item_line, app_inputs)
                if doc.paragraphs and fee_lines_content: 
                    doc.paragraphs[-1].paragraph_format.space_after = Pt(0)
                continue

            text_content_for_runs = line_for_docx_processing # Start with the stripped line
            if text_content_for_runs.startswith("[bp]"):
                current_paragraph_style_name = 'ListBullet'; text_content_for_runs = text_content_for_runs.replace("[bp]", "", 1).lstrip(); space_after_val_pt = Pt(6)
            elif text_content_for_runs.startswith("[a]"): text_content_for_runs = "(a) " + text_content_for_runs.replace("[a]", "", 1).lstrip()
            elif text_content_for_runs.startswith("[b]"): text_content_for_runs = "(b) " + text_content_for_runs.replace("[b]", "", 1).lstrip()
            elif text_content_for_runs.startswith("[c]"): text_content_for_runs = "(c) " + text_content_for_runs.replace("[c]", "", 1).lstrip()
            elif text_content_for_runs.startswith("[d]"): text_content_for_runs = "(d) " + text_content_for_runs.replace("[d]", "", 1).lstrip()
            elif text_content_for_runs.startswith("[e]"): text_content_for_runs = "(e) " + text_content_for_runs.replace("[e]", "", 1).lstrip()
            elif text_content_for_runs.startswith("[f]"): text_content_for_runs = "(f) " + text_content_for_runs.replace("[f]", "", 1).lstrip()
            elif text_content_for_runs.startswith("[g]"): text_content_for_runs = "(g) " + text_content_for_runs.replace("[g]", "", 1).lstrip()
            elif text_content_for_runs.startswith("[ind]"):
                left_indent_value = Inches(4 / 2.54); text_content_for_runs = text_content_for_runs.replace("[ind]", "", 1).lstrip()
            
            if not text_content_for_runs and not (current_paragraph_style_name == 'ListBullet' and not text_content_for_runs): # Avoid adding truly empty paragraphs unless it was an empty bullet
                continue

            p = doc.add_paragraph(style=current_paragraph_style_name if current_paragraph_style_name != 'Normal' else None)
            pf = p.paragraph_format
            if left_indent_value: pf.left_indent = left_indent_value
            pf.space_after = space_after_val_pt 

            add_runs_from_text(p, text_content_for_runs, app_inputs)

            if current_paragraph_style_name == 'Normal':
                for run in p.runs:
                    if not run.font.name: run.font.name = 'Arial'
                    if not run.font.size: run.font.size = Pt(11)
    
    if doc.paragraphs: 
        if doc.paragraphs[-1].paragraph_format.space_after == Pt(0):
             doc.paragraphs[-1].paragraph_format.space_after = Pt(6)

    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)

    st.success("Client Care Letter Generated!")
    st.download_button(
        label="Download Word Document",
        data=doc_io,
        file_name=f"Client_Care_Letter_{client_name_input.replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
