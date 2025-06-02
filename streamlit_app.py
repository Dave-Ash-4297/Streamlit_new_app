import streamlit as st
from docx import Document
from docx.shared import Pt, Inches, Cm # Added Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH # Added for justification
import io
from datetime import datetime
import re

# --- Desired Default Font ---
DEFAULT_FONT_NAME = "HelveticaNeueLT Pro 45 Lt"
DEFAULT_FONT_SIZE = Pt(11)

# --- Helper function (add_runs_from_text) ---
def add_runs_from_text(paragraph, text_line, app_inputs):
    text_line = text_line.replace("[qu 1 set out the nature of the dispute - start and end lower case]", app_inputs.get('qu1_dispute_nature', ""))
    text_line = text_line.replace("[qu 2 set out the immediate steps that will be taken (this maybe a review of the facts and papers to allow you to advise in writing or making initial court applications or taking the first step, prosecuting or defending in a mainstream action). If you have agreed to engage counsel or other third party to assist you should also say so here – start and end lower case]", app_inputs.get('qu2_initial_steps', ""))
    text_line = text_line.replace("[qu3 Explain the estimated time scales to complete the Work. Start capital and end full stop]", app_inputs.get('qu3_timescales', ""))
    text_line = text_line.replace("£ [qu4_ what is the value of the estimated initial costs xx,xxx?]", f"£{app_inputs.get('qu4_initial_costs_estimate', 'XX,XXX')}")

    parts = re.split(r'(\[bold\]|\[end bold\]|\[italics\]|\[end italics\]|\[underline\]|\[end underline\]|\[end\])', text_line)
    is_bold = False; is_italic = False; is_underline = False
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
            run.font.name = DEFAULT_FONT_NAME 
            run.font.size = DEFAULT_FONT_SIZE 
            
# --- Color Palette & UI Styling (condensed) ---
MAIN_BG = "#022933"; MAIN_TEXT = "#FFFFFF"; INPUT_FIELD_BG = "#D3D3D3"; 
INPUT_LABEL_TEXT = "#FFFFFF"; BUTTON_BG = "#98FB98"; BUTTON_TEXT = "#FFFFFF"; SIDEBAR_BG = "#033b4a"
st.set_page_config(layout="wide", page_title="Ramsdens Client Care Letter Generator", page_icon="https://www.ramsdens.co.uk/wp-content/themes/ramsdens/favicon.ico")
st.markdown(f"""<style> /* ... CSS from previous version ... */ </style>""", unsafe_allow_html=True) # Full CSS assumed

# --- App Title & UI Inputs (condensed) ---
st.title("Ramsdens Client Care Letter Generator")
firm_details = {
    "name": "Ramsdens Solicitors LLP", "short_name": "Ramsdens", # ... other details
    "person_responsible_name": "Paul Pinder", # ... all other firm details
    "marketing_address": "Ramsdens Solicitors LLP, Oakley House, 1 Hungerford Road, Edgerton, Huddersfield, HD3 3AL"
}
st.sidebar.header("Letter Details"); our_ref = st.sidebar.text_input("Our Reference", "PP/LEGAL/RAM001/001"); your_ref = st.sidebar.text_input("Your Reference", ""); letter_date = st.sidebar.date_input("Letter Date", datetime.today())
st.sidebar.header("Client Information"); client_name_input = st.sidebar.text_input("Client Name", "Mr. Smith"); client_address_line1 = st.sidebar.text_input("Address 1", "123 Example St"); client_address_line2 = st.sidebar.text_input("Address 2", "SomeTown"); client_postcode = st.sidebar.text_input("Postcode", "EX4 MPL"); client_type = st.sidebar.radio("Client Type:", ("Individual", "Corporate"))
st.sidebar.header("Case Details"); claim_assigned_input = st.sidebar.radio("Claim Assigned?", ("Yes", "No")); track_options = ["Small Claims Track", "Fast Track", "Intermediate Track", "Multi Track"]; selected_track_input = st.sidebar.selectbox("Track?", track_options)
st.header("Dynamic Content"); qu1_dispute_nature_input = st.text_area("Q1", "dispute"); qu2_initial_steps_input = st.text_area("Q2", "steps"); qu3_timescales_input = st.text_area("Q3", "timescales"); qu4_initial_costs_estimate_input = st.text_input("Q4 Costs Est.", "1,500")
st.header("Fee Table Insertion"); fee_table_content_input = st.text_area("Fee Table", "Partner: £XXX")
app_inputs = {'qu1_dispute_nature': qu1_dispute_nature_input, 'qu2_initial_steps': qu2_initial_steps_input, 'qu3_timescales': qu3_timescales_input, 'qu4_initial_costs_estimate': qu4_initial_costs_estimate_input, 'fee_table_content': fee_table_content_input, 'client_type': client_type, 'claim_assigned': claim_assigned_input == "Yes", 'selected_track': selected_track_input}; app_inputs.update(firm_details)

# --- Precedent Text (unchanged) ---
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
Further to our recent discussions, we now write to confirm the terms under which Ramsdens Solicitors LLP [bold](“Ramsdens”)[end] will act for you. As a firm that is regulated by the Solicitors Regulation Authority, we are required to send you this letter which contains specific and prescribed information.
[]
We enclose with this letter our Terms and Conditions of Business which must be read in conjunction with this letter. These documents are a formal communication and the language used is reflective of that. We hope that you understand. Please take the time to read these documents carefully. Where there is any conflict between this letter and our Terms and Conditions of Business, the terms of this letter will prevail. Your continuing instructions in this matter will amount to your acceptance of our Terms and Conditions of Business.
[]
[bold]Your Instructions[end]
[]
We are instructed in relation to [qu 1 set out the nature of the dispute - start and end lower case] [bold](“the Dispute”)[end]. Per our recent discussions [qu 2 set out the immediate steps that will be taken (this maybe a review of the facts and papers to allow you to advise in writing or making initial court applications or taking the first step, prosecuting or defending in a mainstream action). If you have agreed to engage counsel or other third party to assist you should also say so here – start and end lower case] [bold](“the Work”)[end].
[]
This matter may develop over time and the nature of disputes is that opposing parties often seek to present facts and matters in a way that is favourable to their own case. We therefore cannot predict every eventuality but we will work with you to advise on any significant developments and review the overall strategy should that be required. Insofar as changes in the future may have a material impact on any cost estimates provided, we will discuss that with you. We will notify you of any material changes by telephone or in correspondence and we will of course always confirm any verbal advice in writing whenever you request that from us.
[]
[bold]Timescales[end]
[]
[qu3 Explain the estimated time scales to complete the Work. Start capital and end full stop]
[]
[bold]Action Required To Be Taken By You[end]
[]
[underline]Client Identification and Money Laundering[end]
[]
[indiv]Solicitors are required by law to obtain evidence of their client’s identity and address to satisfy money laundering and client identification regulations. This includes clients that are corporate entities.[end indiv]
[corp]Solicitors are required by law to obtain evidence of their client’s identity and address to satisfy money laundering and client identification regulations. This includes clients that are corporate entities.
[a]We will make our own enquiries and obtain documentation from Companies House to identify our corporate client. If you believe Companies House’s records to be out of date, please let us know as soon as possible. We may also require documentation or information from the company itself.
[b]We are also obliged to identify the individuals at the corporate client who provide us with instructions, which usually means directors of limited companies or members/partners in LLPs, and sometimes we must do the same for “beneficial owners”. Either situation may include you as the recipient of this letter, but may also include other people at the business. We will tell you who else may be required to provide identification.[end corp]
[]
To comply with the individual identity requirement, you have two options:
[]
We can carry out a remote ID verification of you and your ID documents using a SmartSearch facility. If you would like us to verify your identification remotely please provide your name, address, date of birth, personal email and mobile number. Once the search has been undertaken, SmartSearch will send you a text or email with a link to use on your smartphone which will require you to take a photo of your ID document and then yourself which it will then upload to its system that will check the document, provide us with a copy, and verify that you are the person on the ID document. The process is quick and easy, and avoids you having to send in ID documents to us. OR:
[]
You can provide us with two documents referred to in the list below, one photographic and one showing your current address. If you are local to any of our offices please call with your original documents and they will be copied whilst you wait and the copies forwarded to us.
[bp]Current signed passport;
[bp]Household utility bill;
[bp]Residence permit issued by the Home Office to EEA nationals on sight of own country passport;
[bp]Current UK or EEA photo-card driving licence; or
[bp]National Identity Card containing a photograph.
[]
Please note that until these identification requirements have been satisfied, we may not be able to accept any money from you or make any substantial progress with your matter. It is therefore important that you provide your documents as soon as possible to avoid any delays.
[]
[underline]Document Preservation and Disclosure[end]
[]
In the event that your matter is litigated before a Court, all parties will be required to give full disclosure of all material relevant to the Dispute. It is therefore essential that you preserve any and all such material that includes correspondence, documents, emails, text and SMS messages and/or other electronic communications of any sort. Your disclosure obligations include an obligation to disclose material that may harm your case or help your opponent’s case, as well as those on which you may rely or which help. If any device on which any such material is stored is to be disposed of or ceases to be used, you must ensure that copies are kept of the material.
[]
[bold]People Responsible For Your Case[end]
[]
I shall be the person with responsibility for your case. My name is {person_responsible_name} and I am a {person_responsible_title} with the firm. My work will be carried out under the supervision of {supervisor_name} who is a {supervisor_title} of the firm.
[]
The easiest way to communicate with me will be either by telephone on {person_responsible_phone}, my mobile {person_responsible_mobile}, or via email to {person_responsible_email}.
[]
There may be occasions when I am not immediately available to speak or meet with you and in these circumstances you should ask to speak to my Assistant, {assistant_name} who will be able to help you.
[]
At Ramsdens we aim to provide the best possible service to our clients and in order to do this we may arrange for one of our client care team to contact you to discuss how we are doing and what we might do better. Please let us know if you would prefer not to be contacted by our team during our handling of your matter. We do however, need to know from you if you feel dissatisfied about the service you are receiving. Should you have any occasion to feel unhappy about our service please let me know straight away and I will discuss this with you. If you are unable to resolve matters with me and still have concerns regarding our service, contact {supervisor_contact_for_complaints} who will attempt to resolve your concerns with you. Formal complaints will be dealt with in accordance with our Firm's complaints procedures which can be provided on request. In the event you are not satisfied with our handling of your complaint you can contact the Legal Ombudsman, full details will be given as part of our complaints procedure.
[]
You also have a right to complain about any bill sent by us by applying to the Court for an assessment of the bill under Part III of the Solicitors Act 1974.
[]
[bold]Costs and Disbursements[end]
[]
[underline]Costs[end]
[]
Our charges to you will be calculated and incurred on a time-spent basis. Time will be recorded on your matter in units of six minutes for letters (generally representing a unit per page or part thereof), emails written (again, representing a unit per equivalent to a page of normal letter) and telephone calls made and received.
[]
Our current hourly charge-out rates, exclusive of VAT, are as follows:
[]
[FEE_TABLE_PLACEHOLDER]
[]
Our hourly charge-out rates are reviewed periodically and we will notify you of any increases. We will also notify you of any changes in the status of legal personnel and their hourly charge-out rate. Unless otherwise agreed with you, we will account to you every month for the fees that have been incurred in relation to this matter. If you require an up to date statement of fees incurred at any time then please ask us and we will provide you with that information. Unless otherwise stated, interim bills are on account of costs and are usually prepared taking into account the value of the time recorded against the matter as at the date of the interim bill. If we hold any monies on account of your costs when an invoice is raised, these monies will be utilised towards discharging the invoice.
[]
[underline]Disbursements[end]
[]
Our hourly charge-out rates do not include expenses for which we will be responsible on your behalf. These expenses are referred to as disbursements and may include travel or accommodation expenses, Court fees or the costs of Barristers or expert witnesses. Where possible, we will endeavour to seek your permission prior to instructing a third party in relation to your matter.
[]
We will not pay out any disbursements on your behalf until the monies have been paid by you.
[]
[underline]Legal Expenses Insurance[end]
[]
[indiv]It may be that you or a member of your household has the benefit of legal expenses insurance that might cover you for legal costs in connection with this matter. If you wish us tocheck your eligibility, please let us have a copy of the relevant insurance schedule and policy document. Alternatively you may be entitled to have your liability for costs paid by another person; for example, an employer or Trade Union. Again, please let us know if you wish us to assist you in checking such eligibility. Please note that you will remain responsible for our charges until such time as any legal expenses insurers have agreed to cover you for our legal costs.[end indiv]
[corp]It may be possible to purchase “After the Event” legal expenses insurance cover to cover your opponents, or, possibly, your costs in this matter. If you wish to explore the possibility of such insurance cover, please let us know. Please bear in mind, though, that there will be costs involved in making an application for cover, and it is likely that a large premium (the amount of which will depend on the amount of costs protected and the prospects of success) will be payable at the outset and possibly on any subsequent anniversary of the inception of the policy.[end corp]
[]
[underline]Your Costs Responsibility to Ramsdens[end]
[]
Our charges to you are not contingent upon the result of your case. You are primarily responsible for the payment of our costs and disbursements. Whilst we may be able to recover a portion of your costs from your opponent, this is not always possible and does not affect your primary responsibility to pay our costs and disbursements.
[]
[underline]Section 74 Solicitors Act 1974 Agreement & Recovery of Costs[end]
[]
It is common in litigation that even where costs are recoverable from an opponent, such recovery will not equate to the level of costs incurred by the successful party. Our agreement expressly permits us to charge an amount of costs greater than that which you will recover or could have recovered from your opponent, and expressly permits payment of such sum.
[]
This part of our agreement is made under section 74(3) of the Solicitors Act 1974 and Civil Procedure Rules 46.9 (2) and (3).
[]
If a Court orders your opponent to pay your costs, you should be aware that:
[]
[a]You will have to pay the costs to us in the first instance and you may then be reimbursed when cleared funds are received from your opponent.
[b]You are unlikely to recover the entirety of our charges from your opponent. In most cases there will be a shortfall between our charges to you and the amount of costs that you may recover from your opponent. This shortfall may arise because your claim is subject to the fixed recoverable costs regime (see below) or because there is a difference between our hourly charge-out rates and the guideline hourly charge-out rates that are considered by the Court when assessing some costs. In so far as any costs or disbursements are of an unusual nature or amount, these costs might not be recoverable from your opponent.
[c]In the unlikely event that your claim is subject to the fixed recoverable costs regime (see below) and the fixed costs recoverable from your opponent exceed the level of our charges calculated and incurred on a time-spent basis, you agree that the charges due to us from you will be the amount of fixed costs recoverable from your opponent.
[d]Your opponent may refuse to comply with the Court’s order. If they do not pay, then you may seek to enforce the Court’s order (for example by sending in the bailiffs or obtaining a charge over property owned by them). However, you should be aware that this itself costs more money and takes time.
[e]Your opponent may have very little by way of assets or they may simply disappear. If this happens then you will not be able to recover your costs or indeed any other monies awarded to you. That is why it is important that in financial disputes you consider now whether your opponent has sufficient assets to pay you a lump sum or instalments as appropriate.
[f]There may be points during your case (including at its conclusion) where you are successful only in part on the issues in it, as a result of which you are entitled to payment of some of your costs by your opponent.
[g]If your opponent receives funding from the Community Legal Service, there are statutory controls on the amount of costs that can be recovered from them. In these circumstances, it is highly unlikely that the Court will make an order that your opponent would have to contribute anything to your costs.
[]
[underline]Fixed Recoverable Costs[end]
[]
Depending upon the value and complexity of a claim, the Court will allocate it to one of four ‘tracks’ when managing the case. If a claim is successful and a Court orders one party to pay the other’s costs, the amount of the costs that can be recovered may be fixed by the Court.
[]
[all_sc]From the information that you have supplied us with, the claim has already been allocated to the Small Claims Track which is the normal track for claims with a monetary value of £10,000 or less.
[]
Having been allocated to the Small Claims Track, the normal rule is that only the following limited costs are recoverable by a successful party:
[bp]Any Court fees paid.
[bp]Fixed issue costs ranging between £50 and £125.
[bp]Loss of earnings not exceeding £95 per person per day.
[bp]Expenses reasonably incurred in travelling to and from and attending a Court hearing
[bp]A sum not exceeding £750 for any expert’s fees.
[]
There are some exceptions to the normal rule and the Court can award costs against a party that has acted unreasonably. However, in practice such awards are rare.[end all_sc]
[all_ft]From the information that you have supplied us with, the claim has already been allocated to the Fast Track which is the normal track for claims with a monetary value of between £10,000 and £25,000.
[]
Having been allocated to the Fast Track, the Court has also assigned your/your opponent’s claim to a Band 1/2/3/4. This means that as the Claimant/Defendant in the proceedings, we know that the costs that may be recoverable from your opponent/you will be fixed dependent upon the stage of the proceedings in which the claim is resolved. A table setting out these fixed recoverable costs is enclosed with this letter.[end all_ft]
[all_int]From the information that you have supplied us with, the claim has already been allocated to the Intermediate Track which is the normal track for claims with a monetary value of between £25,000 and £100,000.
[]
Having been allocated to the Intermediate Track, the Court has also assigned your/your opponent’s claim to Band 1/2/3/4. This means that as the Claimant/Defendant in the proceedings, we know that the costs that may be recoverable from your opponent/you will be fixed dependent upon the stage of the proceedings in which the claim is resolved. A table setting out these fixed recoverable costs is enclosed with this letter.[end all_int]
[all_mt]From the information that you have supplied us with, the claim has already been allocated to the Multi-Track which is the normal track for claims with a monetary value of over £100,000.
[]
Having been allocated to the Multi-Track, this means that the fixed costs regime does not apply to your/your opponent’s claim and the general rule that the ‘loser pays the winner’s costs’ will apply, subject to any costs budgeting that has been implemented by the Court and the caveats set out above under the heading [italics]Section 74 Solicitors Act 1974 Agreement & Recovery of Costs[end italics].[end all_mt]
[sc]From the information that you have supplied us with, it is likely that were Court proceedings to be commenced, the claim would be allocated to the Small Claims Track which is the normal track for claims with a monetary value of £10,000 or less.
[]
Upon allocation to the Small Claims Track, the normal rule is that only the following limited costs are recoverable by a successful party:
[]
[bp]Any Court fees paid.
[bp]Fixed issue costs ranging between £50 and £125.
[bp]Loss of earnings not exceeding £95 per person per day.
[bp]Expenses reasonably incurred in travelling to and from and attending a Court hearing
[bp]A sum not exceeding £750 for any expert’s fees.
[]
There are some exceptions to the normal rule and the Court can award costs against a party that has acted unreasonably. However, in practice such awards are rare.[end sc]
[ft]From the information that you have supplied us with, it is likely that were Court proceedings to be commenced, the claim would be allocated to the Fast Track which is the normal track for claims with a monetary value of between £10,000 and £25,000.
[]
Upon allocation to the Fast Track, the Court will assign your/your opponent’s claim to one of four ‘bands’ depending upon the complexity and number of issues in the claim. When the claim is assigned, as the Claimant/Defendant in the proceedings, we will know that the costs that may be recoverable from your opponent/you will be fixed dependent upon the stage of the proceedings in which the claim is resolved. A table setting out these fixed recoverable costs is enclosed with this letter.[end ft]
[int]From the information that you have supplied us with, it is likely that were Court proceedings to be commenced, the claim would be allocated to the Intermediate Track which is the normal track for claims with a monetary value of between £25,000 and £100,000.
[]
Upon allocation to the Intermediate Track, the Court will assign your/your opponent’s claim to one of four ‘bands’ depending upon the complexity and number of issues in the claim. When the claim is assigned, as the Claimant/Defendant in the proceedings, we will know that the costs that may be recoverable from your opponent/you will be fixed dependent upon the stage of the proceedings in which the claim is resolved. A table setting out these fixed recoverable costs is enclosed with this letter.[end int]
[mt]From the information that you have supplied us with, it is likely that were Court proceedings to be commenced, the claim would be allocated to the Multi-Track which is the normal track for claims with a monetary value of in excess of £100,000.
[]
Upon allocation to the Multi-Track, the fixed costs regime will not apply to your/your opponent’s claim and the general rule that the ‘loser pays the winner’s costs’ will apply, subject to any costs budgeting that has been implemented by the Court and the caveats set out above under the heading [italics]Section 74 Solicitors Act 1974 Agreement & Recovery of Costs[end italics].[end mt]
[]
[underline]Costs Advice[end]
[]
From the information you have provided us with to date, we estimate that our costs for the initial stage of the Work will be £ [qu4_ what is the value of the estimated initial costs xx,xxx?] plus VAT. If any further work is required thereafter, we will discuss the likely associated costs with you beforehand.
[]
It is always difficult to give an indication of the likely costs to be incurred in cases of this type. This is because it is impossible to say at this stage when the case may be brought to a conclusion and the amount of work that may be required to reach that point. The vast majority of cases are settled without the need for Court proceedings and of those where Court proceedings are commenced, the majority are settled without a trial. The actual amount of costs to be incurred will depend upon the arguments being advanced and the amount and nature of the evidence involved. The more evidence that is required, the greater the amount of time that will be spent on it by the parties and the Court and, therefore, the greater the costs.
[]
The involvement of expert evidence (such as in the form of valuation evidence) will also contribute to an increase in the costs involved.
[]
In the event that it may appear that our initial estimate of costs may be exceeded, we will notify you of these changes. We will review our estimate of costs at least every six months.
[]
There may be occasions during the conduct of your case where significant disbursements or major amounts of chargeable time are due to be incurred. We reserve the right to seek payment in advance for these commitments, and routinely do so. In the event that we do seek such payment in advance and it is not made by any reasonable deadline set, we reserve the right to cease acting for you in this matter. In the event that we do cease to act we would attempt to mitigate the impact that doing so would have on your case but it is possible that your case may be prejudiced as a result. We also reserve the right to cease acting for you in the event that any bills rendered to you are not paid within the timescale required.
[]
To this extent, you agree with us that our retainer in this matter is not to be considered an entire agreement, such that we are not obliged to continue acting for you to the conclusion of the matter and are entitled to terminate your retainer before your case is concluded. We are required to make this clear because there has been legal authority that in the absence of such clarity a firm was required to continue acting in a case where they were no longer being funded to do so.
[]
You have a right to ask for your overall cost to be limited to a maximum and we trust you will lialiaise with us if you wish to limit your costs. We will not then exceed this limit without first obtaining your consent. However this does mean that your case may not be concluded if we have reached your cost limit.
[]
In Court or some Tribunal proceedings, you may be ordered to pay the costs of
someone else, either in relation to the whole of the costs of the case if you are unsuccessful or in relation to some part or issue in the case. Also, you may be ordered to pay the costs of another party during the course of proceedings in relation to a particular application to the Court. In such case you will need to provide this firm with funds to discharge such liability within seven days as failure to do so may prevent your case progressing. Please be aware that once we issue a Court or certain Tribunal claims or counterclaim on your behalf, you are generally unable to discontinue your claim or counterclaim without paying the costs of your opponent unless an agreement on costs is reached.
[]
[bold]Limitation of Liability[end]
[]
The liability of Ramsdens Solicitors LLP, its partners and employees in any circumstances whatsoever, whether in contract, tort, statute or otherwise and howsoever caused (including our negligence) for loss or damage arising from or in connection with the provision of services to you shall be limited to the sum of £3,000,000.00 (three million pounds) excluding costs and interest.
[]
[bold]Bank Accounts and Cybercrime[end]
[]
Should we ask you to pay money to us during the course of your matter then please send your funds to our account held with {bank_name} at {bank_address} to:
[]
[]
[ind]Account Name: {account_name}
[ind]Sort Code: {sort_code}
[ind]Account Number: {account_number}
[]
Should you receive any email correspondence regarding our bank account details please telephone your usual contact at Ramsdens before sending your first payment to verify that the details you have been given are correct. We would never advise our clients of any change in our bank account details by email. Should this happen please treat the email as suspicious and contact us immediately. Please do not send any funds until you have verified that the details are correct.
[]
Similarly, if an occasion arises whereby we need to send money to you, we will not accept your bank account details by email without further verification. It is likely that we will telephone you to confirm that the details supplied to us are correct.
[]
[bold]Quality Standard[end]
[]
Our firm is registered under the Lexcel quality standard of the Law Society. As a result of this we are or may become subject to periodic checks by outside assessors. This could mean that your file is selected for checking, in which case we would need your consent for inspection to occur. All inspections are, of course, conducted in confidence. If you prefer to withhold consent, work on your file will not be affected in any way. Since very few of our clients do object to this we propose to assume that we do have your consent unless you notify us to the contrary. We will also assume, unless you indicate otherwise, that consent on this occasion will extend to all future matters which we conduct on your behalf. Please do not hesitate to contact us if we can explain this further or if you would like us to mark your file as not to be inspected. Alternatively if you would prefer to withhold consent please put a line through this section in the copy letter and return to us.
[]
[bold]Data Protection[end]
[]
The enclosed Privacy Notice explains how and why we collect, store, use and share your personal data. It also explains your rights in relation to your personal data and how to contact us or supervisory authorities in the event you have a complaint. Please read it carefully. This Privacy Notice is also available on our website, www.ramsdens.co.uk.
[]
Our use of your personal data is subject to your instructions, the EU General Data Protection Regulation (GDPR), other relevant UK and EU legislation and our professional duty of confidentiality. Under data protection law, we can only use your personal data if we have a proper reason for doing so. Detailed reasons why we may process your personal data are set out in our Privacy Notice but examples are:
[]
[]To comply with our legal and regulatory obligations;
[a]For the performance of our contract with you or to take steps at your request before entering into a contract; or
[b]For our legitimate interests or those of a third party, including:
[bp]Operational reasons, such as recording transactions, training and quality control;
[bp]Updating and enhancing client records;
[bp]Analysis to help us manage our practice; and
[bp]Marketing, such as by sending you updates about subjects and/or events that may be of interest to you.
[]
However, this does not apply to processing sensitive personal data about you, as defined. If it is necessary to process this data for the continued provision of our services to you, we will need your explicit consent for doing so and will request this from you as required.
[]
[bold]Marketing Communications[end]
[]
We would like to use your personal data to send you updates (by email, telephone or post) about legal developments that might be of interest to you and/or information about our services.
[]
This will be done pursuant to our Privacy Notice (referred to above), which contains more information about our and your rights in this respect.
[]
You have the right to opt out of receiving promotional communications at any time, by:
[]
[a]Contacting us by email on {marketing_email};
[b]Using the ‘unsubscribe’ link in emails; or
[c]Writing to Marketing Department at: {marketing_address}.
[]
Yours sincerely,
[]
[]
[]
{name}
Solicitor
""".strip()

# --- Document Generation Logic ---
if st.button("Generate Client Care Letter"):
    doc = Document()
    
    style = doc.styles['Normal']
    style.font.name = DEFAULT_FONT_NAME
    style.font.size = DEFAULT_FONT_SIZE

    lines = precedent_content.split('\n')
    
    in_indiv_block = False; in_corp_block = False; active_track_block_type = None
    main_paragraph_counter = 0
    in_main_numbered_section = False
    
    # Indentation values
    numbered_para_left_indent_cm = 0.75
    numbered_para_first_line_indent_cm = -0.75 # Hanging indent
    numbered_para_tab_stop_cm = 0.75

    sub_item_marker_effective_margin_cm = 0.75 # (a) or bullet aligns with parent text
    sub_item_text_additional_indent_cm = 0.5
    sub_item_left_indent_cm = sub_item_marker_effective_margin_cm + sub_item_text_additional_indent_cm # 1.25 cm
    sub_item_first_line_indent_cm = -sub_item_text_additional_indent_cm # -0.5 cm
    sub_item_tab_stop_cm = sub_item_left_indent_cm # Tab for text after (a)

    ind_item_indent_cm = 0.75 # Default for [ind] items, can be adjusted

    FIRST_NUMBERED_PARAGRAPH_CONTAINS = "Further to our recent discussions, we now write to confirm the terms under which Ramsdens Solicitors LLP"
    STOP_NUMBERING_IF_LINE_IS = "Yours sincerely,"

    track_tags_map = {
        '[all_sc]': ("Yes", "Small Claims Track"), '[all_ft]': ("Yes", "Fast Track"),
        '[all_int]': ("Yes", "Intermediate Track"), '[all_mt]': ("Yes", "Multi Track"),
        '[sc]': ("No", "Small Claims Track"), '[ft]': ("No", "Fast Track"),
        '[int]': ("No", "Intermediate Track"), '[mt]': ("No", "Multi Track")
    }

    for line_raw in lines:
        current_line_stripped_for_logic = line_raw.strip()
        content_to_process_for_runs = current_line_stripped_for_logic 

        line_had_start_tag = False; line_had_end_tag = False
        
        if current_line_stripped_for_logic == "[indiv]": in_indiv_block = True; continue
        if current_line_stripped_for_logic == "[end indiv]": in_indiv_block = False; continue
        if current_line_stripped_for_logic == "[corp]": in_corp_block = True; continue
        if current_line_stripped_for_logic == "[end corp]": in_corp_block = False; continue
        
        is_pure_track_control_tag = False
        if not active_track_block_type: 
            for tag_key in track_tags_map:
                if current_line_stripped_for_logic == tag_key:
                    active_track_block_type = tag_key; is_pure_track_control_tag = True; break
        if active_track_block_type and not is_pure_track_control_tag: 
            end_tag_for_current_block = f"[end {active_track_block_type[1:-1]}]"
            if current_line_stripped_for_logic == end_tag_for_current_block:
                active_track_block_type = None; is_pure_track_control_tag = True
        if is_pure_track_control_tag: continue

        if content_to_process_for_runs.startswith("[indiv]"): in_indiv_block = True; line_had_start_tag = True; content_to_process_for_runs = content_to_process_for_runs.removeprefix("[indiv]")
        if content_to_process_for_runs.endswith("[end indiv]"): line_had_end_tag = True; content_to_process_for_runs = content_to_process_for_runs.removesuffix("[end indiv]")
        if content_to_process_for_runs.startswith("[corp]"): in_corp_block = True; line_had_start_tag = True; content_to_process_for_runs = content_to_process_for_runs.removeprefix("[corp]")
        if content_to_process_for_runs.endswith("[end corp]"): line_had_end_tag = True; content_to_process_for_runs = content_to_process_for_runs.removesuffix("[end corp]")
        
        if not active_track_block_type:
            for tag_key in track_tags_map:
                if content_to_process_for_runs.startswith(tag_key): active_track_block_type = tag_key; line_had_start_tag = True; content_to_process_for_runs = content_to_process_for_runs.removeprefix(tag_key); break
        if active_track_block_type:
            end_tag_for_current_block = f"[end {active_track_block_type[1:-1]}]"
            if content_to_process_for_runs.endswith(end_tag_for_current_block): line_had_end_tag = True; content_to_process_for_runs = content_to_process_for_runs.removesuffix(end_tag_for_current_block)

        should_render_based_on_client_type = not ((in_indiv_block and app_inputs['client_type'] != "Individual") or \
                                               (in_corp_block and app_inputs['client_type'] != "Corporate"))
        should_render_based_on_track = True
        if active_track_block_type:
            target_assignment, target_track = track_tags_map[active_track_block_type]
            current_assignment = "Yes" if app_inputs['claim_assigned'] else "No"
            if not (current_assignment == target_assignment and app_inputs['selected_track'] == target_track):
                should_render_based_on_track = False
        should_render_final = should_render_based_on_client_type and should_render_based_on_track
        
        final_content_after_stripping = content_to_process_for_runs.strip()
        
        current_content_substituted = final_content_after_stripping 
        current_content_substituted = current_content_substituted.replace("{our_ref}", our_ref) # ... and all other substitutions
        current_content_substituted = current_content_substituted.replace("{your_ref}", your_ref)
        current_content_substituted = current_content_substituted.replace("{letter_date}", letter_date.strftime('%d %B %Y'))
        current_content_substituted = current_content_substituted.replace("{client_name_input}", client_name_input)
        current_content_substituted = current_content_substituted.replace("{client_address_line1}", client_address_line1)
        current_content_substituted = current_content_substituted.replace("{client_address_line2_conditional}", client_address_line2 if client_address_line2 else "")
        current_content_substituted = current_content_substituted.replace("{client_postcode}", client_postcode)
        for key, val_firm in firm_details.items():
            current_content_substituted = current_content_substituted.replace(f"{{{key}}}", str(val_firm))

        if not in_main_numbered_section and FIRST_NUMBERED_PARAGRAPH_CONTAINS in current_content_substituted:
            in_main_numbered_section = True
        
        paragraph_number_prefix = ""; current_left_indent_cm = 0.0; current_first_line_indent_cm = 0.0
        current_tab_stops_cm = [] # List of tab stop positions in cm
        is_this_a_main_numbered_paragraph = False
        is_this_a_sub_item = False # for [bp] or [a]

        is_pure_heading = (final_content_after_stripping.startswith(("[bold]", "[underline]")) and final_content_after_stripping.endswith("[end]"))

        if current_content_substituted == STOP_NUMBERING_IF_LINE_IS:
            in_main_numbered_section = False 
        elif in_main_numbered_section:
            is_excluded_from_numbering = False
            if current_line_stripped_for_logic == "[]": is_excluded_from_numbering = True
            elif final_content_after_stripping.startswith("[bp]"): is_excluded_from_numbering = True; is_this_a_sub_item = True
            elif re.match(r'\[([a-g])\]', final_content_after_stripping): is_excluded_from_numbering = True; is_this_a_sub_item = True
            elif is_pure_heading: is_excluded_from_numbering = True
            elif current_content_substituted == "[FEE_TABLE_PLACEHOLDER]": is_excluded_from_numbering = True
            elif final_content_after_stripping.startswith("[ind]"): is_excluded_from_numbering = True # [ind] itself is not numbered
            elif not final_content_after_stripping : is_excluded_from_numbering = True
            elif (in_indiv_block or in_corp_block): # Plain paras in these blocks are not main numbered
                 is_excluded_from_numbering = True

            if not is_excluded_from_numbering:
                main_paragraph_counter += 1
                paragraph_number_prefix = f"{main_paragraph_counter}.\t" # Add tab after number
                is_this_a_main_numbered_paragraph = True
        
        if current_line_stripped_for_logic == "[]": 
            if doc.paragraphs and should_render_final: 
                 doc.paragraphs[-1].paragraph_format.space_after = Pt(12)
            continue 
        elif should_render_final and (final_content_after_stripping or current_line_stripped_for_logic == ""): 
            text_for_runs_final = paragraph_number_prefix + current_content_substituted # Initial text
            
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY # Justify all main body paragraphs
            
            para_style_to_apply = 'Normal'
            local_prefix_for_ab_item = ""

            if is_this_a_main_numbered_paragraph:
                pf.left_indent = Cm(numbered_para_left_indent_cm)
                pf.first_line_indent = Cm(numbered_para_first_line_indent_cm)
                pf.tab_stops.add_tab_stop(Cm(numbered_para_tab_stop_cm))
            elif is_this_a_sub_item:
                pf.left_indent = Cm(sub_item_left_indent_cm)
                pf.first_line_indent = Cm(sub_item_first_line_indent_cm)
                pf.tab_stops.add_tab_stop(Cm(sub_item_tab_stop_cm))
                
                if final_content_after_stripping.startswith("[bp]"):
                    para_style_to_apply = 'ListBullet' # Use Word's bullet
                    text_for_runs_final = current_content_substituted.replace("[bp]", "", 1).lstrip() # Remove tag for text
                else: # [a], [b] etc.
                    match_ab = re.match(r'\[([a-g])\](.*)', final_content_after_stripping)
                    if match_ab:
                        local_prefix_for_ab_item = f"({match_ab.group(1)})\t" # Add tab after (a)
                        text_for_runs_final = local_prefix_for_ab_item + match_ab.group(2).lstrip()
            elif final_content_after_stripping.startswith("[ind]"):
                pf.left_indent = Cm(ind_item_indent_cm) # Simple indent for [ind]
                text_for_runs_final = current_content_substituted.replace("[ind]", "", 1).lstrip()
            elif is_pure_heading: # Headings don't get the justify/indent of main paras unless specified
                pf.alignment = None # Let heading style control alignment or default to left
            
            if para_style_to_apply != 'Normal':
                p.style = para_style_to_apply


            if current_content_substituted == "[FEE_TABLE_PLACEHOLDER]":
                # Fee table specific formatting (already justified by default paragraph rule if not a heading)
                # pf.alignment = None # or WD_ALIGN_PARAGRAPH.LEFT if preferred
                pf.left_indent = Cm(0)
                pf.first_line_indent = Cm(0)
                pf.tab_stops.clear_all()
                fee_lines = app_inputs['fee_table_content'].split('\n')
                # The placeholder itself is handled by add_runs, so we write fee lines *instead*
                doc.paragraphs[-1].text = "" # Clear the placeholder paragraph
                for fee_line in fee_lines:
                    p_fee = doc.add_paragraph(); 
                    p_fee.paragraph_format.space_after = Pt(6); 
                    p_fee.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT # Fee table usually left
                    add_runs_from_text(p_fee, fee_line, app_inputs)
                if doc.paragraphs: doc.paragraphs[-1].paragraph_format.space_after = Pt(0)
            elif final_content_after_stripping or current_line_stripped_for_logic == "": 
                add_runs_from_text(p, text_for_runs_final, app_inputs)
            
            pf.space_after = Pt(0) # Default, next "[]" will override for 12pt

        if line_had_end_tag:
            original_content_ending_with_tag = line_raw.strip() 
            if original_content_ending_with_tag.endswith("[end indiv]"): in_indiv_block = False
            if original_content_ending_with_tag.endswith("[end corp]"): in_corp_block = False
            if active_track_block_type and original_content_ending_with_tag.endswith(f"[end {active_track_block_type[1:-1]}]"):
                active_track_block_type = None
        
    if doc.paragraphs and doc.paragraphs[-1].paragraph_format.space_after == Pt(0):
        doc.paragraphs[-1].paragraph_format.space_after = Pt(6)

    doc_io = io.BytesIO(); doc.save(doc_io); doc_io.seek(0)
    st.success("Client Care Letter Generated!")
    st.download_button("Download Word Document", data=doc_io, file_name=f"Client_Care_Letter_{client_name_input.replace(' ', '_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    
