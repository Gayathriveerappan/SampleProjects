"""Create a five-page PDF from the fictional training RFP."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).parent
OUT = ROOT / "procurement_rfp.pdf"
INK = colors.HexColor("#202334")
VIOLET = colors.HexColor("#6952bf")
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverR", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=INK, alignment=TA_CENTER, spaceAfter=8))
styles.add(ParagraphStyle(name="SubR", parent=styles["Normal"], fontSize=8.5, leading=12, textColor=colors.HexColor("#657080"), alignment=TA_CENTER))
styles.add(ParagraphStyle(name="HeadR", parent=styles["Heading2"], fontSize=11.5, leading=14, textColor=VIOLET, spaceBefore=6, spaceAfter=4))
styles.add(ParagraphStyle(name="BodyR", parent=styles["BodyText"], fontSize=8, leading=10.6, textColor=INK, spaceAfter=4))
styles.add(ParagraphStyle(name="SmallR", parent=styles["BodyText"], fontSize=6.8, leading=8.2, textColor=INK))
styles.add(ParagraphStyle(name="THR", parent=styles["BodyText"], fontSize=7, leading=8.5, textColor=colors.white))

def p(text, style="BodyR"):
    return Paragraph(text.replace("&", "&amp;"), styles[style])

def tbl(rows, widths):
    data = [[p(str(v), "THR" if i == 0 else "SmallR") for v in row] for i, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0,0),(-1,0),INK), ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#f5f6f9"),colors.white]), ("GRID",(0,0),(-1,-1),.3,colors.HexColor("#d9dce4")), ("VALIGN",(0,0),(-1,-1),"TOP"), ("LEFTPADDING",(0,0),(-1,-1),5), ("RIGHTPADDING",(0,0),(-1,-1),5), ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    return t

def footer(canvas, doc):
    canvas.saveState(); canvas.setStrokeColor(colors.HexColor("#d7dbe5")); canvas.line(18*mm,13*mm,A4[0]-18*mm,13*mm)
    canvas.setFont("Helvetica",6.7); canvas.setFillColor(colors.HexColor("#727b8b"))
    canvas.drawString(18*mm,8*mm,"FICTIONAL CLASSROOM RFP · PMW-P1-INT-2026-01 · INR")
    canvas.drawRightString(A4[0]-18*mm,8*mm,str(doc.page)); canvas.restoreState()

story = [
 p("REQUEST FOR PROPOSAL", "CoverR"), p("Design, Tooling, Sampling & Supply of Molded TPE Floor Mats", "SubR"), Spacer(1,5*mm),
 tbl([["RFP reference","PMW-P1-INT-2026-01"],["Issue date","18 October 2026"],["Buyer / program","Pravaah Mobility Works / fictional P1 hatchback"],["Response","Technical and commercial proposal"],["Currency","Indian rupees (INR)"]],[48*mm,118*mm]),
 p("TRAINING SCENARIO ONLY", "HeadR"), p("The buyer, vehicle, suppliers, company histories, prices, capacities, quotations and terms in this package are invented. This is not an actual sourcing event, market benchmark, safety approval or purchase commitment. The five supplier responses supplied with the project are synthetic examples.","BodyR"),
 p("1. Invitation and purpose", "HeadR"), p("Pravaah Mobility Works invites proposals for engineering, tooling, fitment validation, pilot production and possible series supply of a four-piece molded thermoplastic elastomer (TPE) floor-mat set for the fictional P1 cabin. The product provides a beginner-friendly sourcing exercise with measurable fitment, material, tooling, quality, delivery and commercial factors.","BodyR"),
 p("The buyer seeks a supplier that can use controlled cabin inputs to develop a well-fitting set, establish repeatable production controls, support a gated pilot and quote transparent costs. Respondents shall identify assumptions, exclusions and deviations. Best value will consider evidence and execution risk as well as price. Any real award would require due diligence, negotiation, written nomination and a separate purchase order or contract. Forecast volumes are non-binding.","BodyR"),
 p("Program goals", "HeadR"), p("1. Fit all four floor positions without interfering with pedals, seat motion or approved retention features.<br/>2. Use a durable, cleanable material and consistent surface/edge design.<br/>3. Establish a controlled drawing, approved reference sample and first-article gate before pilot release.<br/>4. Clarify tooling custody, maintenance, cost components, tax, freight, warranty and change management.<br/>5. Compare evidence consistently using the weighted model in Section 8.","BodyR"),
 p("Buyer roles", "HeadR"), p("Procurement coordinates clarifications and commercial comparison; vehicle engineering controls interface data and fitment approval; quality approves the control plan and first article; receiving confirms packaging and delivery. Respondents shall nominate equivalent commercial, engineering and quality contacts. A live event would use one controlled clarification channel.","BodyR"),
 PageBreak(), p("SCOPE & PRODUCT REQUIREMENTS", "SubR"),
 p("2. Scope and planned quantities", "HeadR"), p("The requested scope includes input/design review, proposed material and construction, tooling concept and manufacture, samples, fitment corrections, first-article documentation, pilot production, readiness information, series pricing, packaging, delivery plan and warranty/support. Identify included, excluded and optional items separately, including subcontracted operations.","BodyR"),
 tbl([["Stage","Planning quantity","Condition"],["Fitment/sample","20 sets","For engineering review; state sample price and timing"],["Pilot","200 sets","Only after written sample approval and firm release"],["Annual planning","10,000 sets","Indicative and non-binding; firm POs/call-offs control"]],[34*mm,39*mm,93*mm]),
 p("If sample or pilot pricing differs from series supply, show it separately. State minimum order, batch size and capacity assumptions. No volume in this RFP guarantees future business.","BodyR"),
 p("3. Product specification", "HeadR"),
 tbl([["Attribute","Requirement / response requested"],["Set","One driver, one front passenger and two rear mats; identify and pack as four pieces"],["Material","Molded cleanable TPE; declare grade, source, hardness and recycled-content status"],["Appearance / thickness","Black or charcoal; consistent texture; nominal body around 3 mm; state tolerance"],["Fitment","Shaped to buyer-controlled floor template and retention samples; signed drawing controls"],["Anti-slip / edge","Textured underside or ribs; raised perimeter target 8–12 mm; state tolerance and checks"],["Heel zone","Reinforced driver wear area; state construction and inspection"],["Retention / safety","Compatible with supplied features; no sharp edges, loose parts, pedal or seat interference"],["Odour / cleaning","Describe internal controls and available evidence; numerical limits to be agreed"]],[38*mm,128*mm]),
 p("Alternatives require a written deviation request describing impact, risk and validation. Silence is not acceptance. Final CAD/template revision, retention interface, material grade, colour and tolerances must be frozen through controlled review.","BodyR"),
 PageBreak(), p("ENGINEERING, QUALITY & DELIVERY", "SubR"),
 p("4. Engineering, tooling and sample approval", "HeadR"), p("Shortlisted suppliers may receive the controlled floor template, retention samples and vehicle access arrangement after confidentiality and access steps. State required inputs and gaps. Submit a proposed drawing and critical-to-fit dimensions before tool freeze. Buyer review does not transfer design responsibility. A fitment review shall assess coverage, edge, clip engagement, pedal operation, seat travel, appearance and completeness. Written approval of the signed reference sample is required before pilot.","BodyR"),
 p("Describe tool type, expected life, prototype/production tooling scope, maintenance interval, storage, repair responsibility, included correction loops, tool identification, ownership and transfer conditions. Buyer-funded dedicated tooling should be identifiable and recoverable under agreed payment and contract obligations.","BodyR"),
 p("5. Manufacturing and quality plan", "HeadR"), p("Explain the process from incoming compound through molding, finishing, inspection, packing and dispatch. Identify outsourced processes. Provide a process flow or equivalent, draft control plan, first-article report, label example, nonconformance workflow and corrective-action timing.","BodyR"),
 p("At minimum, explain material identity and lot linkage; first-piece approval; dimensions, edge, retention and visual checks; lot/date/shift/tool traceability; suspect stock segregation and containment; and records/retained samples duration. State sampling frequency and sample size. Submit available certificates and test reports with scope/date. Do not claim certification or independent testing without evidence. Buyer may request audit or additional verification under agreed arrangements.","BodyR"),
 p("6. Capacity and delivery", "HeadR"), p("State available monthly capacity, production location, constraints, material lead assumptions, minimum lot, batch size and dispatch cadence. Give milestone timing from complete approved data and tooling PO: design review, tool completion, first sample, correction, sample approval, pilot, pilot completion and series readiness. Include recovery actions for delay, sample failure, capacity shortfall or material interruption.","BodyR"),
 tbl([["Logistics response","Supplier shall state"],["Destination","Buyer receiving plant in Pune area; exact site/hours to be confirmed"],["Dispatch / packaging","Ship-from point, pieces per carton/pallet and deformation/contamination protection"],["Freight / transit","Cost basis, transit assumption, insurance, delivery term and minimum quantity for rates"]],[39*mm,127*mm]),
 PageBreak(), p("COMMERCIAL & QUALIFICATION", "SubR"),
 p("7. Commercial response", "HeadR"), p("Quote in INR with validity and separately identify engineering/NRE, prototype and production tooling, sample sets, pilot unit price, series price per four-piece set, packaging, freight, insurance and GST. State volume price breaks and associated bands. Explain raw-material escalation formula, review interval and evidence. Escalation requires negotiation and written acceptance.","BodyR"),
 p("State payment milestones for tooling, samples, pilot and series; credit period; invoice trigger; cancellation exposure; minimum order commitment; and all exclusions. Mark open costs as “not included / to be quoted,” never zero. Clarify whether freight is actual, fixed, included above a threshold or excluded. Taxes and final delivery terms require confirmation in contracting.","BodyR"),
 p("8. Warranty and launch support", "HeadR"), p("State duration and start date, coverage, claim evidence, acknowledgement, containment response, corrective-action timing, replacement/credit timing, return handling and freight responsibility. Name launch support roles and escalation contacts. Claims should identify the lot; parties should agree disposition in writing.","BodyR"),
 p("9. Supplier qualification and response checklist", "HeadR"), p("Provide legal entity and manufacturing location, relevant product/process experience, capacity evidence, quality-system certificates if held, material source/sub-suppliers, references where permission exists, and constraints relevant to performance. Submit a signed response, compliance/deviation matrix, material evidence, tooling/sample/delivery schedule, quality/traceability plan, price breakdown, payment and warranty terms, assumptions, exclusions, risks and named contacts. All claims in the exercise remain unverified.","BodyR"),
 p("Confidentiality / intellectual property", "HeadR"), p("Buyer drawings, vehicle data, templates and samples remain controlled information and may be used only for the response and awarded work under an agreed confidentiality instrument. State pre-existing know-how and proposed design/tool rights. Rights, transfer and retention belong in the final signed contract; this paragraph is not a substitute for legal agreement.","BodyR"),
 PageBreak(), p("EVALUATION & SUBMISSION", "SubR"),
 p("10. Weighted evaluation method", "HeadR"), p("Score each criterion from 0 to 10 using submitted evidence and documented clarification. Weighted points = criterion weight × score ÷ 10; total possible is 100. Record a brief evidence note and uncertainty for every score. The score supports judgment and is not an automatic award. Buyer may apply pass/fail gates for safety interface, sample acceptance or qualification and may verify claims.","BodyR"),
 tbl([["Criterion","Weight","Evidence"],["Product and tooling capability","25%","Material/process, fitment, retention, tooling, correction and readiness"],["Quality and compliance","25%","Material evidence, first article, inspection, traceability, containment and records"],["Commercial value","20%","Normalized price/tooling/sample/freight/tax clarity, payment and total cost"],["Delivery and capacity","20%","Milestones, sample/pilot, capacity, cadence and recovery plan"],["Warranty and supplier support","10%","Coverage, claim response, containment, replacement and launch support"]],[45*mm,18*mm,103*mm]),
 p("Scoring guide: 0 = no usable evidence/unacceptable; 1–3 = major gaps or high risk; 4–6 = partial or moderate evidence; 7–8 = clear supported evidence with manageable gaps; 9–10 = complete, specific and verifiable evidence with low residual risk. Disclose and manage evaluator conflicts under the applicable buyer process.","BodyR"),
 p("11. Indicative schedule and submission", "HeadR"),
 tbl([["Activity","Target / basis"],["RFP issue","18 October 2026"],["Clarification window","Within 5 calendar days of issue"],["Response due","Within 12 calendar days of issue"],["Completeness review / scoring","After proposal receipt"],["Shortlist / clarification","As requested by buyer"],["Samples, pilot and series","Supplier timing; only after written approval and firm PO"]],[53*mm,113*mm]),
 p("Use reference PMW-P1-INT-2026-01; show proposal revision/date and supplier on every page. Submit one searchable PDF with technical and commercial sections and editable schedules if requested. In a real event the buyer would provide controlled destination and deadline/time zone; none is implied here.","BodyR"),
 p("12. Reservation and final checks", "HeadR"), p("Buyer may clarify, negotiate, reject nonresponsive offers, change volumes/schedule or cancel before award. Bid preparation costs remain with respondents. Any real award requires qualification, approved fitment/sample, agreed terms and authorized PO. Confirm compliance/deviations, separate recurring and one-time costs, GST/freight treatment, schedule/capacity, tool custody/maintenance, quality controls and warranty before considering an offer complete. Forecast is not a commitment. This classroom RFP creates no legal or commercial obligation.","BodyR"),
 p("END OF FICTIONAL RFP · PMW-P1-INT-2026-01", "SubR"),
]

doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=17*mm, leftMargin=17*mm, topMargin=14*mm, bottomMargin=18*mm, title="Pravaah P1 Fictional Procurement RFP", author="Synthetic classroom project")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
