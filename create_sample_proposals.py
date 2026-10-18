"""Generate five fictional Indian supplier quotations for a simple auto part."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

OUT = Path(__file__).parent / "sample_proposals"
OUT.mkdir(exist_ok=True)
INK = colors.HexColor("#202334")
VIOLET = colors.HexColor("#6952bf")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Cover", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=23,
                          leading=27, textColor=INK, alignment=TA_CENTER, spaceAfter=8))
styles.add(ParagraphStyle(name="Sub", parent=styles["Normal"], fontSize=9, leading=13,
                          textColor=colors.HexColor("#657080"), alignment=TA_CENTER))
styles.add(ParagraphStyle(name="Head", parent=styles["Heading2"], fontSize=12, leading=15,
                          textColor=VIOLET, spaceBefore=7, spaceAfter=5))
styles.add(ParagraphStyle(name="Body2", parent=styles["BodyText"], fontSize=8.8, leading=12,
                          textColor=INK, spaceAfter=5))
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=7.6, leading=9.5, textColor=INK))
styles.add(ParagraphStyle(name="TableHead", parent=styles["BodyText"], fontSize=7.6, leading=9.5, textColor=colors.white))

COMMON = "Pravaah P1 is a fictional small hatchback created only for this classroom exercise. The buyer requests a four-piece, black, molded TPE cabin floor-mat set (two front and two rear mats), compatible with a buyer-supplied floor template and retention-point sample. The set should have an anti-slip underside, a raised edge, a reinforced driver's heel zone, no sharp edges, and no interference with pedals or seat movement. Supplier fitment and material claims are illustrative and require buyer validation."

SUPPLIERS = [
    {
        "file": "bharatmold_components.pdf", "name": "BharatMold Components Pvt. Ltd.", "city": "Pune, Maharashtra",
        "tag": "PRECISION TOOLING · PREMIUM FINISH",
        "summary": "BharatMold offers a four-piece TPE set with detailed fitment controls, a reinforced heel pad, and a carefully documented mould-validation sequence. The proposal is the highest priced, with a longer tooling cycle, but includes robust quality records and a clear warranty response.",
        "material": "TPE compound, nominal 3.5 mm working section, charcoal black, textured anti-slip underside, 10 mm raised perimeter, reinforced driver's heel pad, and molded location windows for the supplied retention points. First articles will be checked against the buyer's template; the supplier asks for digital surface data and one physical cabin sample before tooling release.",
        "quality": "BharatMold proposes incoming compound identification, first-piece approval, a 12-point fitment checklist, dimensional checks on 5 sets per shift, and batch-level traceability. A first-article inspection report is included before pilot dispatch. Material odour and abrasion checks are described as internal checks; independent test reports are not attached. Nonconforming lots are quarantined pending buyer disposition.",
        "tooling": "New aluminium prototype tool followed by a production mould after fitment sign-off. Tool design review in week 1, first articles in week 4, correction window in week 5. Tool ownership transfers to the buyer after full payment; storage and annual maintenance are included for year one.",
        "unit": "INR 1,185", "tool": "INR 6,50,000", "lead": "30 calendar days after drawing and sample approval", "capacity": "12,000 sets/month",
        "terms": "50% tooling advance, balance after first-article approval. Product payment net 30 days. GST extra at applicable rate; freight to Pune buyer warehouse estimated at INR 42/set and charged at actuals.",
        "warranty": "12 months from dispatch against manufacturing defects. Acknowledgement within 1 business day and containment plan within 3 business days. Replacement parts shipped with the next weekly dispatch.",
        "experience": "The fictional company profile describes 14 years in molded automotive interior trim, including mats and console liners. Named quality and tooling contacts are provided in the quotation; reference visits can be arranged after shortlisting.",
    },
    {
        "file": "deccan_polymer_works.pdf", "name": "Deccan Polymer Works", "city": "Chennai, Tamil Nadu",
        "tag": "LOWEST UNIT PRICE · QUICK START",
        "summary": "Deccan proposes an economical black TPE mat set with a short sample lead time and the lowest quoted unit price. The quote keeps tooling simple. Several quality evidence items and final fitment details are left for confirmation after receiving the buyer's sample.",
        "material": "Reprocessed-content TPE blend, nominal 2.5 mm thickness, basic pebble texture, 8 mm edge lip, and a stitched heel patch. Retention cut-outs will follow the template. The compound grade, recycled-content percentage, odour test method, and dimensional tolerance are not specified in this offer.",
        "quality": "Operators will visually inspect edges and confirm fit on one sample vehicle before pilot production. The proposal does not include a written control plan, lot traceability format, material certificate, or defined inspection frequency. The supplier will discuss a defect limit after the first sample review.",
        "tooling": "One soft production mould is proposed from the supplied template. A fit sample is targeted in 10 working days; one minor correction is included. Additional design changes may incur charges. Tool custody remains with Deccan unless separately negotiated.",
        "unit": "INR 790", "tool": "INR 2,50,000", "lead": "14 calendar days to first sample; 18 days to pilot", "capacity": "7,000 sets/month",
        "terms": "30% tooling advance and balance before dispatch. Product payment 50% with order, 50% before dispatch. GST extra; delivery freight quoted separately once the buyer location is confirmed.",
        "warranty": "6 months against visible manufacturing defects. Claims should include photographs and batch label. Replacement timing and freight responsibility are not committed in the offer.",
        "experience": "The fictional supplier describes small-batch polymer moulding for aftermarket accessories and three years of automotive trim work. No OEM references or formal automotive quality certification are included.",
    },
    {
        "file": "narmada_auto_plastics.pdf", "name": "Narmada Auto Plastics", "city": "Vadodara, Gujarat",
        "tag": "BALANCED COST · CONTROLLED PILOT",
        "summary": "Narmada offers a balanced four-piece TPE set with a defined pilot, fitment checks, and staged tooling approval. Its commercial quote is mid-range and identifies taxes, freight, and payment assumptions. The supplier provides a practical warranty and supplier-support plan.",
        "material": "Virgin TPE, nominal 3.0 mm body, black matte grain, 10 mm raised edge, molded anti-slip ribs, and a 2.5 mm heel reinforcement. Retention windows match the buyer's sample clips. A small colour chip and one set of material coupons will be submitted with first articles.",
        "quality": "Narmada proposes an approved sample record, go/no-go fitment gauge, first-piece inspection, 5-piece hourly visual and dimensional sampling, batch labels, and a simple corrective-action log. Material lot certificates are retained for 2 years. The proposal includes a 20-set pilot approval gate before the 200-set trial lot.",
        "tooling": "Tool drawing review in week 1, soft-tool sample by day 15, fitment trial by day 18, and pilot release after signed approval. Two fitment correction loops are included. Tool ownership transfers after payment; quarterly preventive maintenance is included for year one.",
        "unit": "INR 965", "tool": "INR 3,80,000", "lead": "21 calendar days to approved sample; 25 days to pilot", "capacity": "10,000 sets/month",
        "terms": "40% tooling advance, 60% after approved sample. Product payment net 30 days after accepted delivery. GST extra; freight to buyer plant estimated at INR 35/set. Quote valid for 60 days; resin price reviewed if polymer index changes by more than 8%.",
        "warranty": "12 months from delivery for material or workmanship defects. Acknowledge in 1 business day, initial containment within 48 hours, and replacement within 7 working days after claim approval.",
        "experience": "The fictional company profile describes nine years producing molded interior and under-bonnet polymer parts for Indian vehicle programs. A quality engineer is assigned to the pilot and monthly supplier reviews are offered.",
    },
    {
        "file": "kaveri_trim_systems.pdf", "name": "Kaveri Trim Systems", "city": "Bengaluru, Karnataka",
        "tag": "ESTABLISHED TRIM SUPPLIER · STRONG SERVICE",
        "summary": "Kaveri presents a mature trim operation with strong customer support and a responsive warranty process. It offers mid-to-high pricing and good monthly capacity. The proposal is less specific about tool design inputs and dimensional controls than the best documented response.",
        "material": "Molded TPE, nominal 3.2 mm thickness, black with a ribbed underside and 9 mm raised border. A separate heel reinforcement is bonded to the driver's mat. Exact compound grade and pedal-clearance tolerance will be selected after a vehicle fitment study.",
        "quality": "The plant uses incoming inspection and a final visual check, with digital batch records for production orders. A first-article fitment sign-off is offered. The quote does not state sample frequency, dimensional acceptance limits, or whether compound batch certificates will accompany each shipment. A control plan can be drafted at nomination.",
        "tooling": "A prototype tool and fit trial are included. Kaveri requests the vehicle for a one-day fitment study but does not include travel. Tool design approval is expected within 10 days of receiving all buyer data; production tool revision count is to be agreed after the study.",
        "unit": "INR 1,045", "tool": "INR 4,20,000", "lead": "24 calendar days after all fitment data are received", "capacity": "15,000 sets/month",
        "terms": "50% tooling advance and 50% at first-article sign-off. Product payment net 45 days. GST extra; freight is included for monthly orders above 1,000 sets. Small-lot transport billed at actuals.",
        "warranty": "18 months against manufacturing defects. Dedicated account contact during launch, response to claims within 24 hours, and replacement within 5 working days after defect confirmation.",
        "experience": "The fictional company describes 18 years in cabin trim and molded accessories with multiple passenger-vehicle programs. It offers three customer references after a mutual NDA. The response does not attach reference letters.",
    },
    {
        "file": "eastern_mobility_components.pdf", "name": "Eastern Mobility Components", "city": "Kolkata, West Bengal",
        "tag": "MATERIAL KNOW-HOW · LONGER TRANSIT PLAN",
        "summary": "Eastern Mobility proposes a durable, easy-clean mat set and provides good material handling detail. Its unit price is competitive, but the tooling and transport lead time is the longest in the group, and the delivery plan has little schedule buffer.",
        "material": "TPE with nominal 3.4 mm body, black, raised 11 mm edge, molded heel zone, and directional anti-slip texture. The supplier offers two hardness options for buyer selection. Retention points will be confirmed from physical samples before the final mould design.",
        "quality": "Material batches are tracked to incoming supplier lots. Operators inspect every mat for flash and surface marks; a 3-piece dimensional sample is checked each production shift. The proposal includes a first-article fit check and a packing checklist, but does not define a formal corrective-action timeline or independent test reports.",
        "tooling": "A single-cavity prototype tool is followed by a production mould. The supplier estimates 4 weeks for a first sample due to toolmaker queue and interstate sample shipment. One tool adjustment is included; further changes are billed at cost. Buyer ownership applies after full tooling payment.",
        "unit": "INR 990", "tool": "INR 3,10,000", "lead": "40 calendar days to first sample; 47 days to pilot", "capacity": "8,000 sets/month",
        "terms": "30% tooling advance, 40% after first article, and 30% after pilot approval. Product payment net 30 days. GST extra; freight to the buyer's western India plant estimated at INR 68/set with weekly dispatches.",
        "warranty": "12 months against manufacturing defects. Claims reviewed within 3 business days; approved replacements dispatched within 10 working days. A quarterly quality call is included.",
        "experience": "The fictional company profile describes 11 years in molded rubber and polymer automotive accessories, including floor liners for aftermarket channels. It reports 8,000-set monthly capacity but gives no OEM program references.",
    },
]


def para(text, style="Body2"):
    return Paragraph(text.replace("&", "&amp;"), styles[style])


def table(rows, widths):
    data = [[para(str(value), "TableHead" if row_index == 0 else "Small") for value in row]
            for row_index, row in enumerate(rows)]
    obj = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    obj.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f5f6f9"), colors.white]),
        ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#d9dce4")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return obj


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d7dbe5"))
    canvas.line(18*mm, 13*mm, A4[0]-18*mm, 13*mm)
    canvas.setFont("Helvetica", 6.8)
    canvas.setFillColor(colors.HexColor("#727b8b"))
    canvas.drawString(18*mm, 8*mm, "FICTIONAL INDIAN SUPPLIER · SYNTHETIC CLASSROOM QUOTATION · INR")
    canvas.drawRightString(A4[0]-18*mm, 8*mm, str(doc.page))
    canvas.restoreState()


def build(item):
    doc = SimpleDocTemplate(str(OUT / item["file"]), pagesize=A4, rightMargin=17*mm, leftMargin=17*mm,
                            topMargin=14*mm, bottomMargin=18*mm,
                            title=f"{item['name']} | Fictional Floor Mat Quotation",
                            author="Synthetic classroom project")
    story = [para("PRAVAAH P1 · TECHNICAL & COMMERCIAL OFFER", "Sub"), Spacer(1, 4*mm),
             para(item["name"], "Cover"), para(f"{item['city']}  ·  {item['tag']}", "Sub"),
             Spacer(1, 3*mm), para("SYNTHETIC CLASSROOM DOCUMENT — NOT A REAL COMPANY OR QUOTE. All supplier names, locations, prices, capacity, experience claims and offers are invented.", "Body2"),
             para("1. Offer summary", "Head"), para(item["summary"]),
             para("This response addresses a four-piece set (two front and two rear mats) for the fictional Pravaah P1 hatchback. The intended sourcing sequence is 20 fitment/sample sets, a 200-set pilot after approval, then purchase orders against a non-binding annual planning forecast of 10,000 sets."),
             para("2. Proposed product configuration", "Head"), para(item["material"]),
             table([["Characteristic", "Supplier response / status"], ["Material and colour", item["material"]],
                    ["Set configuration", "Four molded mats: driver, front passenger and two rear positions"],
                    ["Vehicle interface", "Final contours and retention features depend on buyer template and physical sample"],
                    ["Safety gate", "Buyer fitment approval required; no pedal, seat-track or retention interference permitted"]],
                   [39*mm, 127*mm]),
             para("3. Company profile and scope", "Head"), para(item["experience"]),
             para("Included scope is proposed design review, tooling/sample activity and production supply as described in this offer. The parties must confirm whether packaging, testing, freight, fixture validation and engineering changes are included before nomination."),
             PageBreak(), para("ENGINEERING, TOOLING & QUALITY PLAN", "Sub"),
             para("4. Engineering and fitment method", "Head"),
             para("Supplier will review the buyer's controlled floor template, retention-point samples and nominated vehicle interface before freezing tool geometry. The parties should record datum points, critical contours, permitted thickness variation, heel-zone boundary, edge height and clip engagement on a signed drawing. First articles should be checked in the actual cabin with pedals fully operated and seats moved through their complete travel. Written approval of the reference sample is a release condition."),
             para("5. Tooling plan", "Head"), para(item["tooling"]),
             table([["Tooling checkpoint", "Proposed control"], ["Input review", "Buyer drawing, floor sample, retention samples and approved material definition"],
                    ["Design freeze", "Supplier drawing and critical dimensions reviewed before tool manufacture"],
                    ["First article", "Fitment review, visual review and dimensional report before pilot"],
                    ["Correction / ownership", item["tooling"]]], [42*mm, 124*mm]),
             para("6. Manufacturing and quality controls", "Head"), para(item["quality"]),
             para("7. Inspection and records requested at launch", "Head"),
             para("For each lot, the buyer should agree the inspection level and retain a signed first-article record, material/compound lot reference, production date and shift, quantity inspected, defect disposition and packing identification. Supplier records and any test evidence listed here remain supplier statements until verified by the buyer. The quote does not imply certification unless specifically documented."),
             PageBreak(), para("DELIVERY & COMMERCIAL RESPONSE", "Sub"),
             para("8. Delivery and capacity plan", "Head"),
             para(f"Supplier-stated capacity is {item['capacity']}. The stated lead is {item['lead']}. These are planning statements and remain subject to approved input data, tool readiness, sample acceptance, material availability and a firm purchase order."),
             table([["Milestone", "Planning basis", "Release evidence"],
                    ["Design / tool review", "After receipt of complete buyer inputs", "Signed drawing and tool plan"],
                    ["Fitment sample", item["lead"], "Buyer fitment and first-article approval"],
                    ["Pilot", "200 sets after sample release", "Pilot inspection and written PO release"],
                    ["Series supply", "Indicative 10,000 sets/year; forecast non-binding", "Firm PO and agreed call-off schedule"]],
                   [38*mm, 63*mm, 65*mm]),
             para("Supplier should identify its dispatch point, weekly/monthly cadence, packaging quantity, transit assumptions, escalation contact and recovery action for a missed milestone. Buyer should confirm delivery address and receiving hours."),
             para("9. Commercial quotation", "Head"),
             table([["Cost element", "Quoted response"], ["Unit price", f"{item['unit']} per four-piece set, before GST"],
                    ["One-time tooling", item["tool"]], ["Sample / pilot lead", item["lead"]],
                    ["Capacity", item["capacity"]], ["Tax, freight and payment", item["terms"]]], [48*mm, 118*mm]),
             para("Price comparison must normalize GST, freight, tooling, sample charges, packaging, payment timing and any resin escalation. No total landed cost is inferred where the quote leaves a charge open. Applicable tax treatment should be confirmed by the parties at contracting."),
             PageBreak(), para("WARRANTY, RISKS & ACCEPTANCE", "Sub"),
             para("10. Warranty and launch support", "Head"), para(item["warranty"]),
             para("Claim workflow to agree: buyer identifies lot and defect with photos/sample; supplier acknowledges and contains suspect stock; both parties determine root cause and disposition; corrective action is recorded; replacement, credit or rework is authorized in writing. Warranty start date and freight responsibility must be stated in the purchase order."),
             para("11. Deviations, assumptions and open decisions", "Head"),
             para("Open items before award include final CAD/template revision, retention clip interface, compound grade and hardness, thickness tolerance, odour/cleanability criteria, colour, acceptance sample, inspection frequency, packaging, freight destination, GST, tool maintenance/custody, warranty start date and claim freight. Any item not explicitly included above is an assumption requiring buyer confirmation."),
             para("12. Supplier risk register", "Head"),
             table([["Risk / dependency", "Potential effect", "Proposed action"],
                    ["Late or incomplete buyer fitment data", "Tool/sample timing moves", "Confirm input checklist and freeze date"],
                    ["Material grade not frozen", "Fit, feel or quality variation", "Approve grade and retained reference coupon"],
                    ["Pilot defects or geometry change", "Rework and series delay", "Use signed first article and gated pilot"],
                    ["Forecast treated as firm demand", "Excess or insufficient capacity", "Release only against firm PO/call-off"]], [46*mm, 52*mm, 68*mm]),
             para("13. Validity and authorization", "Head"),
             para("Synthetic comparison validity: 60 days from 18 October 2026. This exercise document is not a binding offer, purchase order, certification or verified reference. Before a real award, verify legal identity, statutory/tax details, bank details, capacity, quality evidence and all commercial terms independently."),
             Spacer(1, 3*mm), para("END OF FICTIONAL FOUR-PAGE PROPOSAL", "Sub")]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUT / item["file"])


for supplier in SUPPLIERS:
    build(supplier)
