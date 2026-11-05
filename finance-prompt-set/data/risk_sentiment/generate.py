#!/usr/bin/env python3
"""Deterministic generator: area risk_sentiment, profile B, 1000 rows. Synthetic content only, stdlib only, no network."""
import hashlib
import json
import os
import random
import re

R = random.Random(42)
AREA = "risk_sentiment"
HERE = os.path.dirname(os.path.abspath(__file__))
MASK = re.compile(r"\d+(?:[.,]\d+)*")
WS = re.compile(r"\s+")
BANNED = re.compile(r"(?i)\b(current|today|latest|right now|recently|this year|last year|as of today)\b")

COMPANIES = [
    ("Halcyon Grid Utilities", "Utilities", "31 Dec", "EUR", "FY2025"),
    ("Meridian Bancorp", "Banks", "31 Dec", "USD", "FY2025"),
    ("Kestrel Foods", "Food producers", "30 Jun", "USD", "FY2025"),
    ("Ardent Industrial Group", "Industrials", "31 Dec", "EUR", "FY2025"),
    ("Solvent Chemical Holdings", "Chemicals", "31 Dec", "USD", "FY2025"),
    ("Northwind Logistics", "Transport", "31 Mar", "EUR", "FY2025"),
    ("Lumen Ridge Energy", "Energy", "31 Dec", "USD", "FY2025"),
    ("Cobalt Bay Shipping", "Transport", "31 Dec", "USD", "FY2025"),
    ("Fairhaven REIT", "Real estate", "31 Dec", "GBP", "FY2025"),
    ("Trelis Semiconductor", "Technology", "31 Dec", "USD", "FY2025"),
    ("Brightwell Pharma", "Healthcare", "31 Dec", "CHF", "FY2025"),
    ("Oakline Insurance", "Insurance", "31 Dec", "GBP", "FY2025"),
    ("Vantage Retail Group", "Retailing", "31 Jan", "USD", "FY2025"),
    ("Sable Mountain Mining", "Mining", "31 Dec", "AUD", "FY2025"),
    ("Perrigan Utilities", "Utilities", "31 Dec", "CAD", "FY2025"),
    ("Harbour Gate Capital", "Asset management", "31 Dec", "USD", "FY2025"),
    ("Aurelian Textiles", "Textiles", "30 Sep", "EUR", "FY2025"),
    ("Cinder Peak Steel", "Steel", "31 Dec", "USD", "FY2025"),
    ("Rowanfield Agritech", "Agriculture", "31 Dec", "BRL", "FY2025"),
    ("Delphine Hotels", "Hotels", "31 Dec", "EUR", "FY2025"),
]

TOPIC = {
    "supply": "supplier concentration", "cyber": "cyber intrusion",
    "regulation": "regulatory action", "cost": "input cost inflation",
    "demand": "demand softening", "people": "labour disruption",
    "litigation": "litigation exposure", "funding": "refinancing risk",
    "weather": "weather loss", "customer": "customer concentration",
}
TOPIC_Q = {"supply": "supply arrangements", "cyber": "cyber security", "regulation": "regulatory matters",
           "cost": "input costs", "demand": "demand conditions", "people": "labour relations", "litigation": "litigation",
           "funding": "funding arrangements", "weather": "weather exposure", "customer": "customer relationships"}
OFFSET = {
    "supply": "an improved supply position", "cyber": "stronger cyber controls",
    "regulation": "a cleaner regulatory position", "cost": "easing input costs",
    "demand": "firmer demand", "people": "better labour availability",
    "litigation": "reduced litigation exposure", "funding": "a stronger funding position",
    "weather": "lower weather exposure", "customer": "a broader customer base",
}

# (topic, polarity, sentence) -- 20 per polarity, 2 per topic.
SENT = [
    ("supply", "negative", "Sole-source supply of the sealed bearing assembly leaves {co} exposed to any interruption at the single plant that makes it."), ("supply", "negative", "Two tier-one suppliers have raised prices twice in the year, and contractual pass-through to customers is capped at half of any increase."),
    ("cyber", "negative", "A ransomware intrusion at the managed logistics provider halted order processing for nine days and exposed customer records."), ("cyber", "negative", "Scheduling software at three plants no longer receives security patches, and a compromise could stop production."),
    ("regulation", "negative", "The competition authority inquiry into {co} distribution terms could result in fines and forced changes to dealer contracts."), ("regulation", "negative", "New emissions reporting rules will require capital spending that was not included in the approved budget."),
    ("cost", "negative", "A sustained rise in resin and freight costs would compress gross margin, and hedges cover only the next two quarters."), ("cost", "negative", "Energy contracts roll off in stages, so each repricing adds to unit cost with no matching price increase."),
    ("demand", "negative", "Orders from the largest retail channel fell for a second quarter, and promotional support has not restored volume."), ("demand", "negative", "Dealer inventories remain above normal, which points to further discounting before reorder rates recover."),
    ("people", "negative", "Labour talks at the packing site are unresolved, and a strike would stop shipments within a week."), ("people", "negative", "Attrition among qualified technicians is running at twice the plan rate, extending maintenance backlogs."),
    ("litigation", "negative", "A patent claim over the coating process seeks damages and an injunction against the largest product line."), ("litigation", "negative", "A customer dispute over defective batches has moved to arbitration and could require a refund plus retrofit costs."),
    ("funding", "negative", "Covenant headroom under the revolving facility has narrowed to a thin margin over the test level, limiting capacity for a downturn."), ("funding", "negative", "Floating-rate debt reprices next year, and each hundred basis points adds materially to interest expense."),
    ("weather", "negative", "Storm damage at the coastal warehouse destroyed inventory and interrupted deliveries for three weeks."), ("weather", "negative", "A dry season cut available volumes from contracted growers, forcing spot purchases at higher prices."),
    ("customer", "negative", "The two largest customers account for 38 percent of revenue, and neither has committed beyond the existing contract."), ("customer", "negative", "A national chain delisted two slower lines, and the shelf space has been reassigned to a competitor."),
    ("supply", "neutral", "{co} qualified a second supplier for the housing component, and volumes are unchanged."), ("supply", "neutral", "The packaging supplier moved to a new plant in the same region, and delivery terms are unchanged."),
    ("cyber", "neutral", "{co} migrated email to a managed service, and the security control set was carried over unchanged."), ("cyber", "neutral", "The annual penetration test was completed, and remediation is scheduled in the ordinary course."),
    ("regulation", "neutral", "The regulator published its final rule, and the compliance date is unchanged from the draft."), ("regulation", "neutral", "The routine inspection of the plant was completed, and the report is in preparation."),
    ("cost", "neutral", "The resin contract renews at the start of the next fiscal year, and terms are under negotiation."), ("cost", "neutral", "Freight surcharges were reclassified within cost of sales with no change to the total."),
    ("demand", "neutral", "The order book was reclassified by end market, and total backlog is unchanged."), ("demand", "neutral", "Seasonal promotional activity is scheduled in line with the usual calendar."),
    ("people", "neutral", "The packing site moved to a two-shift pattern, and total headcount is unchanged."), ("people", "neutral", "A new human resources director joined from another subsidiary in the group."),
    ("litigation", "neutral", "The parties agreed to extend the discovery timetable by one quarter."), ("litigation", "neutral", "Counsel changed firms, and the hearing date was not moved."),
    ("funding", "neutral", "{co} renewed its revolving credit facility on substantially similar terms."), ("funding", "neutral", "The term loan amortisation schedule is unchanged for the coming year."),
    ("weather", "neutral", "The hurricane season forecast is in line with the long-run average."), ("weather", "neutral", "The coastal warehouse lease was extended, and storage capacity is unchanged."),
    ("customer", "neutral", "One retail customer moved to the standard payment terms used across the channel."), ("customer", "neutral", "The customer contract renewed at the existing volume with the same pricing schedule."),
    ("supply", "positive", "{co} extended its supply agreement with a regional converter through 2028 on improved pricing terms."), ("supply", "positive", "A second qualified supplier came online, cutting single-source exposure for the bearing assembly."),
    ("cyber", "positive", "The new identity platform removed standing administrator access from the plant networks."), ("cyber", "positive", "A penetration test found no critical findings after the firewall segmentation project closed."),
    ("regulation", "positive", "The regulator closed its review of {co} dealer terms without enforcement action."), ("regulation", "positive", "Early adoption of the new emissions standard was certified ahead of the compliance date."),
    ("cost", "positive", "Gross margin improved as resin costs eased and the mix shifted toward higher-value coated grades."), ("cost", "positive", "A fixed-price energy contract through 2027 removes near-term power cost volatility."),
    ("demand", "positive", "Order intake in the industrial channel rose 14 percent year on year, and the backlog covers nine months of output."), ("demand", "positive", "Repeat orders from two national retailers lifted volume in the latest trading quarter."),
    ("people", "positive", "A new shift pattern at the packing site reduced overtime and cut absenteeism by a third."), ("people", "positive", "The technician apprenticeship programme filled 40 vacancies ahead of plan."),
    ("litigation", "positive", "The arbitration panel dismissed the defective-batch claim without award."), ("litigation", "positive", "The patent office narrowed the competitor claim, removing the injunction risk."),
    ("funding", "positive", "The refinancing extended maturities to 2029 and lowered the average coupon by 90 basis points."), ("funding", "positive", "Free cash flow turned positive, and net debt fell by 62 million after the working capital release."),
    ("weather", "positive", "Insurance recoveries covered most of the warehouse storm damage, and deliveries resumed ahead of schedule."), ("weather", "positive", "Irrigation investment reduced the harvest sensitivity to a dry season."),
    ("customer", "positive", "The largest customer extended its contract by three years with a higher committed volume."), ("customer", "positive", "A new regional chain added 60 stores to the distribution list."),
]
NEG = [c for c in SENT if c[1] == "negative"]
NEU = [c for c in SENT if c[1] == "neutral"]
POS = [c for c in SENT if c[1] == "positive"]

TRIPLES = []
for _a in range(len(NEG)):
    for _b in range(len(NEU)):
        if NEU[_b][0] == NEG[_a][0]:
            continue
        for _c in range(len(POS)):
            if POS[_c][0] in (NEG[_a][0], NEU[_b][0]):
                continue
            TRIPLES.append((_a, _b, _c))
R.shuffle(TRIPLES)

HEADLINES = [
    ("bearish", "Food producers", "Kestrel Foods warns that private-label pressure will cut full-year margin."), ("bearish", "Banks", "Meridian Bancorp sets aside a larger provision for commercial property loans."),
    ("bearish", "Industrials", "Ardent Industrial flags a third consecutive quarter of falling order intake."), ("bearish", "Energy", "Lumen Ridge Energy delays the offshore tie-in after a contractor dispute."),
    ("bearish", "Transport", "Cobalt Bay Shipping idles two vessels as transpacific rates slide."), ("bearish", "Real estate", "Fairhaven REIT cuts its distribution guidance on weaker occupancy."),
    ("bearish", "Technology", "Trelis Semiconductor loses a design win at its largest handset customer."), ("bearish", "Healthcare", "Brightwell Pharma halts enrolment in a late-stage trial after a safety signal."),
    ("bearish", "Retailing", "Vantage Retail Group reports a fall in comparable store sales."), ("bearish", "Mining", "Sable Mountain Mining suspends haulage after a tailings review."),
    ("bearish", "Insurance", "Oakline Insurance faces higher catastrophe claims after the autumn storms."), ("bearish", "Textiles", "Aurelian Textiles shutters a spinning line as import competition bites."),
    ("bullish", "Food producers", "Kestrel Foods lifts prices and holds volume as input costs retreat."), ("bullish", "Banks", "Meridian Bancorp beats on net interest income as deposit costs ease."),
    ("bullish", "Industrials", "Ardent Industrial wins a framework order for grid substations."), ("bullish", "Energy", "Lumen Ridge Energy signs a long-term offtake for its gas plant."),
    ("bullish", "Transport", "Cobalt Bay Shipping fixes a charter at rates above the spot market."), ("bullish", "Real estate", "Fairhaven REIT signs two anchor tenants at a new logistics park."),
    ("bullish", "Technology", "Trelis Semiconductor lands a design win in automotive radar."), ("bullish", "Healthcare", "Brightwell Pharma receives priority review for its oncology candidate."),
    ("bullish", "Retailing", "Vantage Retail Group posts positive comparable sales on higher footfall."), ("bullish", "Mining", "Sable Mountain Mining reports record concentrate grades at its flagship pit."),
    ("bullish", "Insurance", "Oakline Insurance raises its dividend after reserve releases."), ("bullish", "Textiles", "Aurelian Textiles wins a uniform supply contract running three years."),
    ("neutral", "Food producers", "Kestrel Foods appoints a new chief operating officer."), ("neutral", "Banks", "Meridian Bancorp files its annual report on the usual timetable."),
    ("neutral", "Industrials", "Ardent Industrial completes the sale of its small pumps unit."), ("neutral", "Energy", "Lumen Ridge Energy schedules a capital markets day for analysts."),
    ("neutral", "Transport", "Cobalt Bay Shipping renames its liner division."), ("neutral", "Real estate", "Fairhaven REIT transfers the listing of one subsidiary to the main market."),
    ("neutral", "Technology", "Trelis Semiconductor holds its annual shareholder meeting."), ("neutral", "Healthcare", "Brightwell Pharma publishes its trial registry update."),
    ("neutral", "Retailing", "Vantage Retail Group moves a distribution centre lease to a new landlord."), ("neutral", "Mining", "Sable Mountain Mining names a new head of exploration."),
    ("neutral", "Insurance", "Oakline Insurance completes its scheduled actuarial review."), ("neutral", "Textiles", "Aurelian Textiles changes its segment reporting to two lines."),
]

GUID = {
    "raised": [
        "{co} raised its full-year revenue guidance to {lo} to {hi} million from {plo} to {phi} million, citing stronger industrial demand. The margin outlook was narrowed to the upper half of the previous range.", "{co} raised its full-year operating profit guidance to {lo} to {hi} million from {plo} to {phi} million after freight costs fell. Capital spending guidance is unchanged.",
        "{co} lifted its full-year free cash flow guidance to {lo} to {hi} million from {plo} to {phi} million following a working capital release. Net debt guidance was reduced accordingly.", "{co} raised its full-year net interest income guidance to {lo} to {hi} million from {plo} to {phi} million as deposit costs eased. The cost income target was left unchanged.",
        "{co} raised its full-year adjusted earnings guidance to {lo} to {hi} million from {plo} to {phi} million, helped by a lower tax rate. The dividend policy is unchanged.", "{co} increased its full-year capital spending guidance to {lo} to {hi} million from {plo} to {phi} million to fund the grid programme. Revenue guidance was left unchanged.",
        "{co} raised its full-year sales guidance to {lo} to {hi} million from {plo} to {phi} million after a strong third quarter. The store rollout target is unchanged.", "{co} upgraded its full-year production guidance to {lo} to {hi} million tonnes from {plo} to {phi} million tonnes after the pit wall remediation finished early. Unit cost guidance was trimmed.",
    ],
    "lowered": [
        "{co} cut its full-year revenue guidance to {lo} to {hi} million from {plo} to {phi} million after the loss of a distribution contract. The margin target was placed under review.", "{co} lowered its full-year operating profit guidance to {lo} to {hi} million from {plo} to {phi} million, citing unhedged energy costs. Capital spending guidance was cut by a fifth.",
        "{co} reduced its full-year free cash flow guidance to {lo} to {hi} million from {plo} to {phi} million on higher inventory. Net debt guidance was raised.", "{co} lowered its full-year net interest income guidance to {lo} to {hi} million from {plo} to {phi} million as loan growth stalled. The cost income target was left unchanged.",
        "{co} reduced its full-year adjusted earnings guidance to {lo} to {hi} million from {plo} to {phi} million after a plant outage. The dividend policy is unchanged.", "{co} cut its full-year capital spending guidance to {lo} to {hi} million from {plo} to {phi} million to protect cash flow. Revenue guidance was left unchanged.",
        "{co} lowered its full-year sales guidance to {lo} to {hi} million from {plo} to {phi} million after weaker footfall. The store rollout target was halved.", "{co} cut its full-year production guidance to {lo} to {hi} million tonnes from {plo} to {phi} million tonnes after the tailings review suspended haulage. Unit cost guidance was raised.",
    ],
    "reaffirmed": [
        "{co} reaffirmed its full-year revenue guidance of {lo} to {hi} million and left the margin outlook unchanged. Volume is tracking the middle of the plan.", "{co} maintained its full-year operating profit guidance of {lo} to {hi} million and repeated its capital spending plan. No change was made to the margin range.",
        "{co} confirmed its full-year free cash flow guidance of {lo} to {hi} million and its net debt target. Working capital is tracking the plan.", "{co} restated its full-year net interest income guidance of {lo} to {hi} million and its cost income target. Loan growth is tracking the plan.",
        "{co} maintained its full-year adjusted earnings guidance of {lo} to {hi} million and its dividend policy. The tax rate assumption is unchanged.", "{co} kept its full-year capital spending guidance at {lo} to {hi} million and its revenue outlook unchanged. Project timetables are unchanged.",
        "{co} reaffirmed its full-year sales guidance of {lo} to {hi} million and left the store rollout target unchanged. Trading is consistent with the plan.", "{co} kept its full-year production guidance at {lo} to {hi} million tonnes and its unit cost guidance unchanged. Grades are in line with the mine plan.",
    ],
    "withdrawn": [
        "{co} withdrew its full-year revenue guidance while it restates prior-period revenue after a contract accounting review. No new range was provided.", "{co} suspended its full-year operating profit guidance pending a review of project provisions. The margin target was also withdrawn.",
        "{co} pulled its full-year revenue guidance after the audit committee found errors in segment allocations. A new range will follow the restatement.", "{co} withdrew its full-year sales guidance while it rebases the store estate. The rollout target was suspended.",
        "{co} cancelled its full-year free cash flow guidance pending an inventory review. The net debt target was withdrawn.", "{co} withdrew its full-year production guidance after a geotechnical review closed the main pit. Unit cost guidance was also withdrawn.",
        "{co} suspended its full-year net interest income guidance pending a loan book review. The cost income target was withdrawn.", "{co} withdrew its full-year adjusted earnings guidance while it reassesses the tax position. The dividend policy remains under review.",
    ],
}

HEDGE_POLICY = ("Policy: hedge score is the number of occurrences of these terms in the passage, counted case-insensitively as whole words: "
                "approximately, assumes, believes, could, estimates, expects, if, likely, may, might, possibly, potentially, subject to, uncertain, would. "
                "Bands: sparse = 0 to 1 occurrences, moderate = 2 to 3, dense = 4 or more.")
SEV_POLICY = ("Policy: severity bands are assigned from operational impact. critical = output stopped or a contractual default triggered; "
              "high = multi-site disruption or peak-season revenue at risk; elevated = single-site disruption with rerouting; "
              "low = local interruption contained within one day.")
HEDGES = ["approximately", "assumes", "believes", "could", "estimates", "expects", "if", "likely",
          "may", "might", "possibly", "potentially", "subject to", "uncertain", "would"]
CALC_HEDGES = ["believes", "could", "expects", "if", "likely", "may", "might", "would"]

HBASE = [
    "The supplier agreement runs to 2028 and covers most coated volume.", "The plant operates four lines and ships to three regional markets.",
    "The term loan matures in 2028 and carries a fixed coupon.", "The group reports in euros and sells mainly in the home market.",
    "The warehouse holds six weeks of finished goods.",
]
HADD = [
    "Management estimates that recovery could take two quarters.", "The timing is uncertain and subject to approval, which could slip.",
    "Volume growth is likely to remain below plan if promotional support is withdrawn.", "Potentially, the shortfall might be offset by approximately 12 million of insurance recoveries.",
    "The regulator may require remediation, and the cost is not yet known.", "Management believes the issue is contained.",
    "A further review would follow if the test is failed.",
]

SEV_CASES = [
    ("critical", "The flagship plant stopped output after the boiler failed, and the largest customer has invoked its supply-continuity clause. Restart is not expected within the quarter."), ("critical", "A ransomware event locked the order-entry and billing systems across all sites, and the group cannot invoice until systems are restored."),
    ("critical", "The leverage test was breached at the quarter end, and the lenders have not waived the covenant."), ("critical", "Production of the affected line has stopped and the recall covers every unit shipped since March, with no restart date set."),
    ("critical", "Flooding closed the only distribution centre serving the northern region, and peak-season orders cannot be fulfilled."), ("high", "Two distribution centres are running on manual picking after a systems outage, and peak-season orders are at risk."),
    ("high", "A strike at the main packing site has stopped two of four lines, and customer deliveries are being rescheduled weekly."), ("high", "The largest customer has cut its forecast by a third, and the contract carries no volume commitment."),
    ("high", "A regulatory order restricts sales in one country, which represents a tenth of group revenue."), ("high", "The supplier of a critical component has suspended shipments, and inventory covers only six weeks."),
    ("elevated", "One regional depot is without power, and deliveries are being rerouted, adding a day to lead times."), ("elevated", "A single store closed for two days after a water leak, and nearby stores absorbed the demand."),
    ("elevated", "One production line is running at reduced speed after a sensor fault, and maintenance is scheduled for the weekend."), ("elevated", "A customer dispute has moved to mediation, and payment of one invoice is on hold."),
    ("elevated", "A phishing incident compromised three mailboxes, and access has been reset for the affected users."), ("low", "A single store closed for one morning after a water leak, and trading resumed the same day."),
    ("low", "A packaging supplier missed one delivery, and the shortfall was covered from safety stock."), ("low", "A laptop was lost in transit and the device was wiped remotely the same day."),
    ("low", "One invoice was paid four days late because of a bank holiday."), ("low", "A routine inspection found two minor documentation gaps, both corrected on site."),
]

TONE = [
    ("improved", "Order intake fell for a third quarter and two lines ran short of staff.", "Order intake recovered and staffing is back to plan."), ("improved", "The regulator opened a review of dealer terms.", "The regulator closed the review without action."),
    ("improved", "Freight costs rose faster than price.", "Freight costs eased and the price increase held."), ("improved", "Two customers delisted slower lines.", "One delisted line returned after a packaging change."),
    ("improved", "The plant ran at 68 percent utilisation.", "The plant ran at 84 percent utilisation."), ("improved", "Covenant headroom was thin and the facility repriced higher.", "The refinancing extended maturities and headroom widened."),
    ("deteriorated", "Order intake recovered and staffing was back to plan.", "Order intake fell for a third quarter and two lines ran short of staff."), ("deteriorated", "The regulator closed the review without action.", "The regulator reopened the review after new complaints."),
    ("deteriorated", "Freight costs eased and the price increase held.", "Freight costs spiked and the price increase was reversed."), ("deteriorated", "The plant ran at 84 percent utilisation.", "The plant ran at 68 percent utilisation."),
    ("deteriorated", "Covenant headroom widened after the refinancing.", "Covenant headroom narrowed after a reclassification of leases."), ("deteriorated", "The largest customer extended its contract.", "The largest customer gave notice on its contract."),
    ("unchanged", "The order book was reclassified by end market.", "Total backlog is unchanged after the reclassification."), ("unchanged", "The packaging supplier moved to a new plant in the same region.", "Delivery terms are unchanged."),
    ("unchanged", "The term loan amortisation schedule was restated by quarter.", "Annual amortisation is unchanged."), ("unchanged", "The group changed its segment disclosure to two lines.", "Total revenue is unchanged by the restatement."),
    ("unchanged", "A new human resources director joined from another subsidiary.", "Headcount and policy are unchanged."), ("unchanged", "The warehouse lease moved to a new landlord.", "Storage capacity and terms are unchanged."),
]

MAT_OPTS = ["cyber breach", "demand softening", "refinancing risk", "regulatory penalty", "supplier concentration"]
MAT = [
    ("refinancing risk", "Cyber cover is bound, demand is stable across four channels, a second supplier is qualified, and the regulatory penalty is provided for. The refinancing is the exception: 180 million of notes mature within a year and the interest cover test tightens at the same time."), ("refinancing risk", "Of the five exposures, four carry named mitigations. Cyber controls were tested, demand held in three channels, the regulatory penalty is provided for, and the supplier base was widened. Nothing mitigates the refinancing: 240 million matures in eleven months with no replacement arranged."),
    ("refinancing risk", "{co} reviewed five exposures. Cyber is insured, demand is diversified, the supplier has a backup, and the penalty is provided for. The refinancing remains open: a 300 million facility matures in nine months and the coupon hedge expires first."), ("refinancing risk", "Cyber testing found no critical gaps, demand is spread across four channels, the supplier now has a second source, and the regulatory penalty is provided for. The binding constraint is refinancing: 180 million of notes mature next year and interest cover is already below the test level."),
    ("supplier concentration", "Cyber cover is bound, demand is stable across four channels, the refinancing runs to 2029, and the regulatory penalty is provided for. Supplier concentration is the exception: one plant makes the sealed assembly and no second source has been qualified."), ("supplier concentration", "Of the five exposures, four are contained. Cyber controls were tested, demand held in three channels, the refinancing is arranged, and the regulatory penalty is provided for. Supplier concentration is not contained: a single plant supplies the sealed assembly and inventory covers eleven days."),
    ("supplier concentration", "{co} reviewed five exposures. Cyber is insured, demand is diversified, the refinancing is complete, and the penalty is provided for. The unresolved item is supplier concentration, where qualification of a second plant is at least three quarters away."), ("supplier concentration", "Cyber testing found no gaps, demand is stable, the refinancing runs to 2029, and the penalty is provided for. Supplier concentration remains the binding exposure: one plant provides the sealed assembly and no alternative has been qualified."),
    ("cyber breach", "Demand is stable across four channels, the refinancing runs to 2029, a second supplier is qualified, and the regulatory penalty is provided for. Cyber is the exception: the order-entry system is unsupported, two intrusions were detected in the year, and cover is capped at 20 million."), ("cyber breach", "Of the five exposures, four are contained. Demand held in three channels, the refinancing is arranged, the supplier has a backup, and the penalty is provided for. Cyber is not contained: administrator credentials are shared across plants and the response plan has never been tested."),
    ("cyber breach", "{co} reviewed five exposures. Demand is diversified, the refinancing is arranged, the supplier base was widened, and the penalty is provided for. Cyber ranks first: the billing platform is unsupported, remote access is not segmented, and recovery is estimated at nine days."), ("cyber breach", "Demand is stable, the refinancing is complete, the supplier has a second source, and the regulatory penalty is provided for. Cyber remains the binding exposure: the warehouse system no longer receives patches and the insurer has excluded ransomware."),
    ("demand softening", "Cyber cover is bound, the refinancing runs to 2029, a second supplier is qualified, and the penalty is provided for. Demand is the exception: the largest channel has cut its forecast twice and trade inventory is at a four-year high."), ("demand softening", "Of the five exposures, four carry mitigations. Cyber controls were tested, the refinancing is arranged, the supplier base was widened, and the penalty is provided for. Demand is not mitigated: orders in the largest channel fell for a third quarter and promotions have not restored volume."),
    ("demand softening", "{co} reviewed five exposures. Cyber is insured, the refinancing is complete, the supplier has a backup, and the penalty is provided for. Demand is the binding constraint, with dealer inventory above normal and reorder rates falling."), ("demand softening", "Cyber testing found no gaps, the refinancing runs to 2029, the supplier has a second source, and the regulatory penalty is provided for. Demand softening ranks first: two national chains have cut shelf space and the order book is down a fifth."),
    ("regulatory penalty", "Cyber cover is bound, demand is stable, the refinancing runs to 2029, and a second supplier is qualified. The regulatory penalty is the exception: the authority has issued a statement of objections and the maximum penalty is a tenth of turnover."), ("regulatory penalty", "Of the five exposures, four are contained. Cyber controls passed, demand held in three channels, the refinancing is arranged, and the supplier base was widened. The regulatory matter has no provision and no agreed timetable, and counsel expects a penalty above the materiality threshold."),
    ("regulatory penalty", "{co} reviewed five exposures. Cyber is insured, demand is diversified, the refinancing is complete, and the supplier has a backup. The regulator has opened a formal investigation with a stated intention to impose a penalty, and no provision has been recognised."), ("regulatory penalty", "Cyber testing found no gaps, demand is stable, the refinancing is arranged, and the supplier has a second source. The regulatory exposure is first: a formal notice alleges mis-selling and the potential penalty exceeds the existing provision several times over."),
]

EVENT_TYPES = ["cyber incident", "guidance cut", "litigation", "management change",
               "regulatory action", "restructuring", "supply disruption", "weather loss"]
EVENTS = [
    (["cyber incident", "management change"], "A ransomware attack closed two order-entry systems for four days. The group also announced that its chief financial officer will leave at the end of the month. No change to guidance was announced."), (["guidance cut", "supply disruption"], "The company cut its full-year revenue guidance after a fire at the sole coating plant halted shipments for three weeks."),
    (["litigation", "regulatory action"], "A customer class action was filed over defective batches, and the competition authority opened a review of dealer terms in the same week."), (["restructuring", "management change"], "The group will consolidate three divisions into two and close the regional office. The operations director stepped down as part of the change."),
    (["weather loss", "guidance cut"], "Storm flooding damaged the coastal warehouse, and management reduced full-year earnings guidance to reflect the lost inventory."), (["cyber incident", "regulatory action"], "A data breach exposed customer records, and the privacy regulator has requested a formal incident report."),
    (["supply disruption", "guidance cut"], "A key supplier suspended deliveries of the bearing assembly, and the group cut its production guidance for the second half."), (["litigation", "management change"], "The general counsel left after a patent dispute moved to trial, and outside counsel was appointed to lead the defence."),
    (["restructuring", "supply disruption"], "The group is closing two older lines and consolidating volume at the coastal plant, which will interrupt shipments during the transition."), (["regulatory action", "restructuring"], "The regulator imposed a remediation order on the distribution business, and the group will separate that unit into a standalone entity."),
    (["weather loss", "supply disruption"], "A dry season cut harvest volumes, and the group is buying on the spot market to meet contracted deliveries."), (["cyber incident", "litigation"], "An intrusion into the billing platform delayed invoicing, and two customers have filed claims over duplicate charges."),
    (["guidance cut", "restructuring"], "Management withdrew the margin target and announced a review of the store estate that may close a tenth of the branches."), (["management change", "regulatory action"], "A new chief executive joined from a peer, and the regulator lifted the consent order that had restricted lending."),
    (["litigation", "supply disruption"], "A supplier dispute over defective resin moved to arbitration, and deliveries were suspended pending the outcome."), (["restructuring", "guidance cut"], "The group will exit two markets and take a restructuring charge, and it lowered full-year revenue guidance accordingly."),
    (["weather loss", "management change"], "Hurricane damage closed the southern depot for a week, and the logistics director left to join another group."), (["regulatory action", "guidance cut"], "A new tariff applies to imports from the region, and the group cut its full-year margin guidance to reflect the duty."),
    (["cyber incident", "supply disruption"], "A systems outage at the logistics provider stopped inbound deliveries for three days, and two plants ran short of components."), (["management change", "guidance cut"], "The finance director resigned, and the interim team withdrew the full-year earnings guidance pending a review."),
    (["litigation", "weather loss"], "Storm damage triggered a business interruption claim, and the insurer is disputing the loss estimate in arbitration."), (["restructuring", "cyber incident"], "The group is outsourcing its data centre as part of a cost programme, and a migration error exposed internal records."),
]

ITEMS = ["Supplier concentration", "Cyber intrusion", "Regulatory penalty", "Demand softening",
         "Refinancing risk", "Commodity input cost", "Labour disruption", "Customer churn",
         "Product recall", "Litigation exposure", "Weather disruption", "Freight cost inflation",
         "Currency translation", "Key-person dependence", "Pension deficit", "Contract renewal",
         "Channel disintermediation", "Data privacy", "Sanctions exposure", "Energy price",
         "Tariff exposure", "Quality defect", "Capacity constraint", "Counterparty default",
         "Technology obsolescence", "Water scarcity", "Insurance adequacy", "Tax dispute",
         "Lease renewal", "Subsidy expiry"]

KNOW = [
    ("What does a debt covenant headroom ratio measure?", "The cushion between a borrower financial metric and the level required by the covenant."), ("How is the cash conversion cycle computed from DSO, DIO and DPO?", "Days sales outstanding plus days inventory outstanding minus days payables outstanding."),
    ("What does a going-concern qualification in an audit report signal?", "Substantial doubt about the entity ability to continue operating for at least twelve months."), ("Under IFRS 9, what are the three stages of expected credit loss impairment?", "Stage 1 twelve-month losses, stage 2 lifetime losses for increased credit risk, and stage 3 lifetime losses for credit-impaired assets."),
    ("What is the difference between a bond coupon and its yield to maturity?", "The coupon is the fixed rate paid on face value; yield to maturity is the total return if the bond is held to maturity at the purchase price."), ("What does a negative cash conversion cycle indicate for a retailer?", "The retailer collects from customers before it pays its suppliers."),
    ("How does an interest rate swap turn floating-rate exposure into fixed-rate exposure?", "The borrower pays a fixed rate and receives a floating rate, so the net interest cost is fixed."), ("What is the purpose of a materiality threshold in an audit?", "To set the amount above which misstatements are large enough to affect the decisions of users."),
    ("What does EBITDA add back to operating profit?", "Depreciation and amortisation."), ("Why does a leveraged buyout typically raise a company cost of debt?", "Higher leverage raises default risk, so lenders demand a wider spread."),
    ("How does a lessee account for a finance lease under IFRS 16?", "The lessee recognises a right-of-use asset and a lease liability."), ("What does a debt-to-EBITDA ratio of 4.0 times mean?", "Gross debt equals four years of EBITDA."),
    ("What is the difference between a share buyback and a dividend?", "A buyback reduces shares outstanding; a dividend pays cash without changing the share count."), ("How is gross margin computed from revenue and cost of goods sold?", "Revenue minus cost of goods sold, divided by revenue."),
    ("What does a put option give its holder?", "The right, but not the obligation, to sell the underlying at the strike price before expiry."), ("What happens to a bond price after a credit downgrade, all else equal?", "The price falls as the required yield rises."),
    ("What does working capital measure?", "Short-term operating assets minus short-term operating liabilities."), ("What is a covenant-lite loan?", "A loan with fewer maintenance covenants, typically tested only on incurrence events."),
    ("How does securitisation move assets off a bank balance sheet?", "The assets are sold to a special purpose vehicle funded by issued securities."), ("What gives rise to a deferred tax liability?", "Timing differences between accounting profit and taxable profit that reverse in future periods."),
    ("What is the function of a sinking fund in a bond indenture?", "It sets aside money to redeem part of the principal before maturity."), ("What distinguishes an operating lease from a finance lease for a lessor?", "The lessor keeps most of the risks and rewards of ownership in an operating lease."),
    ("What does an Altman Z-score below 1.8 suggest?", "An elevated probability of financial distress."), ("How is return on invested capital computed?", "Net operating profit after tax divided by invested capital."),
    ("What is the difference between a forward and a futures contract?", "A forward is traded privately and settled at maturity; a futures contract is exchange-traded and marked to market daily."), ("What does an inverted yield curve usually signal?", "Expectations of lower short-term rates, often linked to a slowing economy."),
    ("Why is operating cash flow preferred to net income in credit analysis?", "It strips out accruals and shows the cash generated by operations."), ("What is the purpose of a maintenance covenant test?", "To require the borrower to meet a financial metric at each testing date."),
    ("What does a goodwill impairment indicate?", "The carrying value of an acquired business exceeds its recoverable amount."), ("How does a rights issue dilute existing shareholders?", "New shares are issued, so each existing share represents a smaller ownership fraction."),
    ("What is a credit default swap?", "A contract that pays the buyer if a reference entity defaults."), ("What does subordination mean in a bond structure?", "Junior claims rank behind senior claims for repayment."),
    ("What is the difference between gross debt and net debt?", "Net debt deducts cash and cash equivalents from gross debt."), ("How does a company record an unfunded pension obligation?", "As a liability on the balance sheet, with actuarial gains and losses in other comprehensive income."),
    ("What does a debt maturity wall describe?", "A concentration of maturities falling due in the same period."), ("What is the role of a trustee in a bond issuance?", "To represent bondholders and enforce the indenture terms."),
    ("What does negative goodwill arise from?", "A bargain purchase where consideration is below the fair value of net assets acquired."), ("How is free cash flow to the firm approximated from operating cash flow?", "Operating cash flow minus capital expenditure."),
    ("What risk does a share pledge by a controlling holder create?", "Forced selling if the shares fall below the loan-to-value threshold."), ("What is the accounting effect of capitalising development costs?", "The costs are recorded as an asset and amortised rather than expensed immediately."),
]

NOTE_BANK = [
    "management believes the supplier agreement may be renegotiated and could add cost, while the cyber review is likely to conclude next quarter",
    "the board expects demand might soften if promotional support is withdrawn, and the refinancing could price wider",
    "counsel believes the dispute may settle, and the plant upgrade could slip if permits are delayed",
]

def ent(k):
    return COMPANIES[k % len(COMPANIES)]

def fill(t, name):
    return t.replace("{co}", name)

def mask(s):
    return MASK.sub("#", WS.sub(" ", str(s)).strip().lower())

def wc(text):
    return len(re.findall(r"[A-Za-z0-9%']+", text))

def hedge_count(text):
    low = " " + re.sub(r"[^a-z ]+", " ", text.lower()) + " "
    return sum(low.count(" " + h + " ") for h in HEDGES)

def table_md(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)

ROWS = []
USED_CTX = set()
USED_PAIR = set()

def add(task, fx, ctx, q, gt, at, tol):
    key = mask(ctx) + "|" + mask(q)
    if key in USED_PAIR:
        raise SystemExit("near-duplicate pair: " + fx)
    USED_PAIR.add(key)
    USED_CTX.add(mask(ctx))
    ROWS.append({"task": task, "_fx": fx, "source": "synthetic:" + AREA, "context": ctx,
                 "question": q, "ground_truth": gt, "answer_type": at, "tolerance": tol})

def memo(k):
    a, b, c = TRIPLES[k]
    parts = [NEG[a], NEU[b], POS[c]]
    off = k % 3
    parts = parts[off:] + parts[:off]
    name, _sector, _fy, _cur, period = ent(k)
    sents = [fill(p[2], name) for p in parts]
    return name, period, parts, sents, " ".join(sents)

def memo_ctx(k, units=False):
    name, period, parts, sents, text = memo(k)
    if units:
        lead = "Units: sentence positions are counted from one and answers are whole numbers. Memo: %s, %s risk review." % (name, period)
    else:
        lead = "Memo: %s, %s risk review." % (name, period)
    return lead + "\n\n" + text, name, period, parts, sents

def memo_same(k, pol):
    bank = {"negative": NEG, "neutral": NEU, "positive": POS}[pol]
    chosen = []
    i = k
    while len(chosen) < 3:
        c = bank[i % len(bank)]
        if c[0] not in [x[0] for x in chosen]:
            chosen.append(c)
        i += 1
    off = k % 3
    chosen = chosen[off:] + chosen[:off]
    name, _s, _f, _c, period = ent(k)
    sents = [fill(c[2], name) for c in chosen]
    return sents, " ".join(sents), name, period

def table_ctx(k, n=5, footnote=None):
    name, _sector, _fy, _cur, period = ent(k)
    items = R.sample(ITEMS, n)
    lik = [R.randint(2, 5) for _ in range(n)]
    imp = [R.randrange(12, 96, 2) for _ in range(n)]
    mit = [R.randrange(1, 9) for _ in range(n)]
    prior = [max(10, lik[j] * imp[j] - R.randint(2, 11)) for j in range(n)]
    lead = ("Units: $ in millions except mitigation spend in $ millions, scores in points and percentages in percent. "
            "Entity: %s; period: %s." % (name, period))
    rows = [[items[j], lik[j], imp[j], mit[j], prior[j]] for j in range(n)]
    md = table_md(["Risk", "Likelihood (1-5)", "Impact ($m)", "Mitigation spend ($m)", "Prior score"], rows)
    ctx = lead + "\n\n" + md
    if footnote:
        ctx += "\n\nFootnote: " + footnote
    return ctx, name, period, items, lik, imp, mit, prior

SENT_QS = ["Classify the sentiment of this risk statement toward the issuer. Label set: {negative, neutral, positive}.", "Assign a sentiment label to the sentence for a credit analyst. Label set: {negative, neutral, positive}.", "Is the disclosure sentence negative, neutral or positive? Label set: {negative, neutral, positive}."]
HEAD_QS = ["Classify the headline implication for the sector. Label set: {bearish, bullish, neutral}.", "What does the headline signal for the sector? Label set: {bearish, bullish, neutral}.", "Label the headline tone for a sector analyst. Label set: {bearish, bullish, neutral}."]
GUID_QS = ["Classify the guidance direction stated in the excerpt. Label set: {lowered, raised, reaffirmed, withdrawn}.", "What direction did management take on guidance? Label set: {lowered, raised, reaffirmed, withdrawn}.", "Label the guidance action described in the excerpt. Label set: {lowered, raised, reaffirmed, withdrawn}."]
HEDGE_Q = "Using the policy, assign the hedging band for the passage. Label set: {dense, moderate, sparse}."
SEV_Q = "Using the policy, assign the escalation severity. Label set: {critical, elevated, high, low}."
TONE_Q = "Compare the two periods and classify the tone shift. Label set: {deteriorated, improved, unchanged}."
MAT_Q = ("Which single risk is most material over the next twelve months? "
         "Label set: {cyber breach, demand softening, refinancing risk, regulatory penalty, supplier concentration}.")
EVENT_Q = ("List every event type present in the excerpt. Allowed event types: {cyber incident, guidance cut, litigation, "
           "management change, regulatory action, restructuring, supply disruption, weather loss}. Answer as a list.")

def build_calc():
    for i in range(120):
        name, _s, _f, _c, period = ent(i)
        items = R.sample(ITEMS, 5)
        lik = [R.randint(2, 5) for _ in range(5)]
        imp = [R.randrange(12, 96, 2) for _ in range(5)]
        mit = [R.randrange(1, 9) for _ in range(5)]
        prior = [max(10, lik[j] * imp[j] - R.randint(2, 11)) for j in range(5)]
        note = NOTE_BANK[i % 3]
        lead = ("Units: $ in millions except mitigation spend in $ millions, scores in points, ratios in times, "
                "hedge counts in whole words and percentages in percent. Entity: %s; period: %s." % (name, period))
        md = table_md(["Risk", "Likelihood (1-5)", "Impact ($m)", "Mitigation spend ($m)", "Prior score"],
                      [[items[j], lik[j], imp[j], mit[j], prior[j]] for j in range(5)])
        ctx = lead + "\n\n" + md + "\n\nNote: " + note[:1].upper() + note[1:] + "."
        comp = [lik[j] * imp[j] for j in range(5)]
        total_imp = sum(imp)
        total_comp = sum(comp)
        top2 = sorted(imp, reverse=True)[:2]
        t = items[i % 5]
        j = i % 5
        kind = i % 10
        if kind == 0:
            q = "What is the composite score for %s, computed as likelihood multiplied by impact, in points?" % t
            gt, tol = comp[j], "abs:1"
        elif kind == 1:
            q = "What is total impact exposure across the five risks, in $ millions?"
            gt, tol = total_imp, "abs:1"
        elif kind == 2:
            q = "What is the change in the composite score for %s versus the prior score shown, in points?" % t
            gt, tol = comp[j] - prior[j], "abs:1"
        elif kind == 3:
            q = "What share of total impact exposure comes from the two largest risks, in percent?"
            gt, tol = round(sum(top2) * 100.0 / total_imp, 2), "abs:0.1"
        elif kind == 4:
            q = ("What is the probability-weighted loss across the register, using likelihood divided by five "
                 "as the probability, in $ millions?")
            gt, tol = round(sum(lik[x] / 5.0 * imp[x] for x in range(5)), 2), "abs:0.1"
        elif kind == 5:
            q = ("What is the mitigation coverage ratio for %s, computed as mitigation spend divided by impact "
                 "exposure, in times?" % t)
            gt, tol = round(mit[j] * 1.0 / imp[j], 3), "abs:0.01"
        elif kind == 6:
            q = ("How many of these hedge terms appear in the risk note: believes, could, expects, if, likely, may, "
                 "might, would? Give a whole number.")
            gt, tol = hedge_count(note), "abs:0.01"
        elif kind == 7:
            q = "What is the density of those hedge terms in the risk note per 100 words, in percent?"
            gt, tol = round(hedge_count(note) * 100.0 / wc(note), 2), "abs:0.1"
        elif kind == 8:
            cap = total_comp + R.randrange(20, 80, 2)
            q = ("If the board tolerance for the total composite score is %d points, what is the headroom, "
                 "in points?" % cap)
            gt, tol = cap - total_comp, "abs:1"
        else:
            q = "What is the impact-weighted average likelihood across the register, in points?"
            gt, tol = round(sum(lik[x] * imp[x] for x in range(5)) * 1.0 / total_imp, 3), "abs:0.01"
        add("calc", "calc_%03d" % i, ctx, q, gt, "number", tol)

def build_extraction():
    for j in range(140):
        k = 500 + j
        ctx, name, period, parts, sents = memo_ctx(k)
        ti = j % 3
        tlabel = TOPIC[parts[ti][0]]
        if j % 2 == 0:
            q = "Quote verbatim the sentence that discusses %s in the memo. Return the sentence only." % TOPIC_Q[parts[ti][0]]
        else:
            q = "Which sentence discusses %s? Copy it exactly as written." % TOPIC_Q[parts[ti][0]]
        add("extraction", "ex_memo_%03d" % k, ctx, q, sents[ti], "text", "normalized")
    for j in range(80):
        k = 700 + j
        foot = "the prior score for %s was not disclosed" % ("placeholder",)
        # build table first with footnote referencing a real item
        name, _s, _f, _c, period = ent(k)
        items = R.sample(ITEMS, 4)
        lik = [R.randint(2, 5) for _ in range(4)]
        imp = [R.randrange(12, 96, 2) for _ in range(4)]
        mit = [R.randrange(1, 9) for _ in range(4)]
        prior = [max(10, lik[x] * imp[x] - R.randint(2, 11)) for x in range(4)]
        foot = "the prior score for %s was not disclosed" % items[1]
        lead = ("Units: $ in millions except mitigation spend in $ millions and scores in points. "
                "Entity: %s; period: %s." % (name, period))
        md = table_md(["Risk", "Likelihood (1-5)", "Impact ($m)", "Mitigation spend ($m)", "Prior score"],
                      [[items[x], lik[x], imp[x], mit[x], prior[x]] for x in range(4)])
        ctx = lead + "\n\n" + md + "\n\nFootnote: " + foot + "."
        if j % 2 == 0:
            q = "What value is recorded for %s in the Impact ($m) column? Answer with the digits shown." % items[2]
            gt = str(imp[2])
        else:
            q = "What does the footnote say about %s? Return the footnote text without the word Footnote." % items[1]
            gt = foot
        add("extraction", "ex_tab_%03d" % k, ctx, q, gt, "text", "normalized")

def build_qa():
    for j, (q, a) in enumerate(KNOW):
        if BANNED.search(q):
            raise SystemExit("time-sensitive knowledge question: " + q)
        ROWS.append({"task": "qa", "_fx": "qa_know_%02d" % j, "source": "knowledge:finance_general",
                     "context": "", "question": q, "ground_truth": a, "answer_type": "text",
                     "tolerance": "normalized"})
    for j in range(64):
        k = 800 + j
        ctx, name, period, parts, sents = memo_ctx(k)
        ti = j % 3
        tlabel = TOPIC[parts[ti][0]]
        q = "Which sentence of the memo, counting from one, discusses %s? Give a whole number." % TOPIC_Q[parts[ti][0]]
        c2 = memo_ctx(k, units=True)[0]
        add("qa", "qa_memo_idx_%03d" % k, c2, q, ti + 1, "number", "abs:0.01")
    trend_tpl = [
        "Classify the overall direction of the risk narrative in the memo. Label set: {improving, stable, worsening}.", "Is the tone of this memo improving, stable or worsening? Label set: {improving, stable, worsening}.",
        "Label the direction of the risk narrative. Label set: {improving, stable, worsening}.",
    ]
    for gi, pol in enumerate(("negative", "neutral", "positive")):
        for j in range(22):
            k = 900 + gi * 22 + j
            sents, text, name, period = memo_same(k, pol)
            ctx = "Memo: %s, %s risk narrative.\n\n%s" % (name, period, text)
            lab = {"negative": "worsening", "neutral": "stable", "positive": "improving"}[pol]
            add("qa", "qa_trend_%s_%02d" % (pol, j), ctx, trend_tpl[j % 3], lab, "label", "exact")
    for j in range(70):
        k = 950 + j
        ctx, name, period, items, lik, imp, mit, prior = table_ctx(k, n=4)
        comp = [lik[x] * imp[x] for x in range(4)]
        total_imp = sum(imp)
        kind = j % 4
        if kind == 0:
            q = "What is the composite score for %s, computed as likelihood multiplied by impact, in points?" % items[j % 4]
            gt, at, tol = comp[j % 4], "number", "abs:1"
        elif kind == 1:
            best = max(range(4), key=lambda x: imp[x])
            q = "Which risk has the largest impact exposure? Answer with the risk name as written in the table."
            gt, at, tol = items[best], "text", "normalized"
        elif kind == 2:
            q = "What share of total impact exposure comes from the two largest risks, in percent?"
            gt, at, tol = round(sum(sorted(imp, reverse=True)[:2]) * 100.0 / total_imp, 2), "number", "abs:0.1"
        else:
            q = "What is the impact-weighted average likelihood across the table, in points?"
            gt, at, tol = round(sum(lik[x] * imp[x] for x in range(4)) * 1.0 / total_imp, 3), "number", "abs:0.01"
        add("qa", "qa_tab_%03d" % k, ctx, q, gt, at, tol)

def guidance_fixture(seq, direc, pat):
    name, _s, _f, _c, period = ent(seq)
    tpl = GUID[direc][pat]
    if direc == "withdrawn":
        return {"name": name, "period": period, "dir": direc, "text": fill(tpl, name),
                "lo": None, "hi": None, "plo": None, "phi": None, "pat": pat}
    base = R.randrange(180, 900, 4)
    phi = base + R.randrange(14, 40, 2)
    plo = base
    delta = R.randrange(24, 90, 4)
    if direc == "raised":
        lo, hi = plo + delta, phi + delta
    elif direc == "lowered":
        lo, hi = plo - delta, phi - delta
    else:
        lo, hi = plo, phi
    text = fill(tpl, name).format(lo=lo, hi=hi, plo=plo, phi=phi)
    return {"name": name, "period": period, "dir": direc, "text": text,
            "lo": lo, "hi": hi, "plo": plo, "phi": phi, "pat": pat}

def build_classification():
    # 1. risk sentence sentiment: 48 rows, 16 per label
    for pol, bank in (("negative", NEG), ("neutral", NEU), ("positive", POS)):
        for j in range(16):
            topic, _p, text = bank[j]
            name, _s, _f, _c, period = ent(j)
            ctx = "Memo: %s, %s risk disclosure.\n\n%s" % (name, period, fill(text, name))
            add("classification", "cls_sent_%s_%02d" % (pol, j), ctx, SENT_QS[j % 3], pol, "label", "exact")
    # 2. headline sentiment: 36 rows, 12 per label
    for gi, lab in enumerate(("bearish", "bullish", "neutral")):
        for j in range(12):
            _l, sector, text = HEADLINES[gi * 12 + j]
            ctx = "Note: sector desk headline, %s.\n\n%s" % (sector, text)
            add("classification", "cls_head_%s_%02d" % (lab, j), ctx, HEAD_QS[j % 3], lab, "label", "exact")
    # 3. guidance direction: 32 rows, 8 per label
    for gi, direc in enumerate(("raised", "lowered", "reaffirmed", "withdrawn")):
        for j in range(8):
            fx = guidance_fixture(gi * 8 + j, direc, j)
            ctx = "Excerpt: %s, %s guidance update.\n\n%s" % (fx["name"], fx["period"], fx["text"])
            add("classification", "cls_guid_%s_%02d" % (direc, j), ctx, GUID_QS[j % 3], direc, "label", "exact")
    # 4. hedging band: 24 rows, 8 per band
    pool = []
    seen = set()
    for b in range(len(HBASE)):
        for size in range(0, 4):
            for start in range(len(HADD)):
                text = " ".join([HBASE[b]] + [HADD[(start + q) % len(HADD)] for q in range(size)])
                if mask(text) in seen:
                    continue
                seen.add(mask(text))
                pool.append((hedge_count(text), text))
    buckets = {"sparse": [], "moderate": [], "dense": []}
    for cnt, text in pool:
        band = "sparse" if cnt <= 1 else ("moderate" if cnt <= 3 else "dense")
        buckets[band].append(text)
    for band in ("sparse", "moderate", "dense"):
        picks = buckets[band][:8]
        if len(picks) < 8:
            raise SystemExit("short hedge bucket " + band)
        for j, text in enumerate(picks):
            ctx = HEDGE_POLICY + "\n\nPassage: " + text
            add("classification", "cls_hedge_%s_%02d" % (band, j), ctx, HEDGE_Q, band, "label", "exact")
    # 5. escalation severity: 20 rows, 5 per level
    counts = {}
    for level, text in SEV_CASES:
        j = counts.get(level, 0)
        counts[level] = j + 1
        ctx = SEV_POLICY + "\n\nIncident: " + text
        add("classification", "cls_sev_%s_%02d" % (level, j), ctx, SEV_Q, level, "label", "exact")
    # 6. tone shift: 18 rows, 6 per shift
    counts = {}
    for shift, a, b in TONE:
        j = counts.get(shift, 0)
        counts[shift] = j + 1
        name, _s, _f, _c, period = ent(j + {"improved": 0, "deteriorated": 6, "unchanged": 12}[shift])
        ctx = ("Note: two-period tone comparison, %s.\n\nEarlier period: %s\n\nLater period: %s"
               % (name, a, b))
        add("classification", "cls_tone_%s_%02d" % (shift, j), ctx, TONE_Q, shift, "label", "exact")
    # 7. most material risk: 20 rows, 4 per label
    counts = {}
    for ans, text in MAT:
        j = counts.get(ans, 0)
        counts[ans] = j + 1
        name, _s, _f, _c, period = ent(j + MAT_OPTS.index(ans) * 4)
        ctx = "Memo: portfolio risk review, %s.\n\n%s" % (name, fill(text, name))
        add("classification", "cls_mat_%02d_%02d" % (MAT_OPTS.index(ans), j), ctx, MAT_Q, ans, "label", "exact")
    # 8. multi-label events: 22 rows
    for j, (types, text) in enumerate(EVENTS):
        name, _s, _f, _c, period = ent(j)
        ctx = "Transcript: incident review excerpt, %s.\n\n%s" % (name, text)
        add("classification", "cls_ev_%02d" % j, ctx, EVENT_Q, sorted(types), "list", "set")

def build_summarization():
    for j in range(50):
        k = 1100 + j
        ctx, name, period, parts, sents = memo_ctx(k)
        neg = [p for p in parts if p[1] == "negative"][0]
        pos = [p for p in parts if p[1] == "positive"][0]
        tmpl = ["In one sentence, name the main pressure in the memo and the main offset.", "Summarise the memo in one sentence, naming the principal pressure and what offsets it.", "Give a one-sentence summary of the risk position, naming the main pressure and the offset."][j % 3]
        ref = "The main pressure is %s, partly offset by %s." % (TOPIC[neg[0]], OFFSET[pos[0]])
        add("summarization", "sum_memo_%03d" % k, ctx, tmpl, ref, "text", "normalized")
    for j in range(30):
        direc = ("raised", "lowered", "reaffirmed", "withdrawn")[j % 4]
        fx = guidance_fixture(1200 + j, direc, j % 8)
        ctx = "Excerpt: %s, %s guidance update.\n\n%s" % (fx["name"], fx["period"], fx["text"])
        q = "Summarise the guidance change in one sentence, stating the direction and the new range."
        if direc == "withdrawn":
            ref = "Guidance was withdrawn, and no new range was provided."
        elif direc == "reaffirmed":
            ref = "Guidance was reaffirmed at %d to %d million." % (fx["lo"], fx["hi"])
        else:
            ref = "Guidance was %s to %d to %d million from %d to %d million." % (
                direc, fx["lo"], fx["hi"], fx["plo"], fx["phi"])
        add("summarization", "sum_guid_%03d" % (1200 + j), ctx, q, ref, "text", "normalized")
    for j in range(20):
        shift, a, b = TONE[j % 18]
        name, _s, _f, _c, period = ent(j)
        ctx = ("Note: two-period tone comparison, %s.\n\nEarlier period: %s\n\nLater period: %s"
               % (name, a, b))
        q = "Summarise the tone shift between the two periods in one sentence."
        ref = "Tone %s: the earlier period reported '%s' and the later period reported '%s'." % (shift, a, b)
        add("summarization", "sum_tone_%02d" % j, ctx, q, ref, "text", "normalized")

T_REG = {"name": "get_risk_register", "description": "Return the risk register for an issuer and fiscal period with likelihood, impact and mitigation spend for each risk.", "parameters": {"type": "object", "properties": {"entity": {"type": "string", "description": "Registered issuer name, for example Meridian Bancorp"}, "period": {"type": "string", "description": "Fiscal period label, for example FY2025"}}, "required": ["entity", "period"]}}
T_SENT = {"name": "score_sentiment", "description": "Score a disclosure passage against a fixed label set and return the label with a confidence value.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Passage to score"}, "labels": {"type": "array", "items": {"type": "string"}, "description": "Ordered label set"}}, "required": ["text", "labels"]}}
T_GUID = {"name": "list_guidance_history", "description": "List the guidance direction reported by an issuer for a metric across fiscal periods.", "parameters": {"type": "object", "properties": {"entity": {"type": "string", "description": "Registered issuer name"}, "metric": {"type": "string", "description": "Metric name, for example revenue"}}, "required": ["entity", "metric"]}}
T_SEARCH = {"name": "search_disclosures", "description": "Search the disclosure index for an issuer and return matching event records.", "parameters": {"type": "object", "properties": {"entity": {"type": "string", "description": "Registered issuer name"}, "keyword": {"type": "string", "description": "Free-text keyword, for example cyber"}}, "required": ["entity", "keyword"]}}


def reg_json(name, period, items, lik, imp):
    return json.dumps({"entity": name, "period": period, "risks": [{"risk": items[x], "likelihood": lik[x], "impact_m": imp[x]} for x in range(len(items))]}, ensure_ascii=False)

def build_tool_use():
    for p in range(10):
        for k in range(10):
            idx = p * 10 + k
            name, _s, _f, _c, period = ent(idx)
            items = R.sample(ITEMS, 4)
            lik = [R.randint(2, 5) for _ in range(4)]
            imp = [R.randrange(12, 96, 2) for _ in range(4)]
            best = max(range(4), key=lambda x: imp[x])
            total = sum(imp)
            if p == 0:
                msgs = [{"role": "user", "content": "Rank the risks in the register for %s for %s by impact and give me the largest." % (name, period)}, {"role": "tool", "content": reg_json(name, period, items, lik, imp)}, {"role": "user", "content": "Answer with the risk name exactly as it appears in the register."}]
                gt, at, tol, tools = items[best], "text", "normalized", [T_REG]
            elif p == 1:
                msgs = [{"role": "user", "content": "For %s in %s, what share of total impact do the two largest risks represent?" % (name, period)}, {"role": "assistant", "content": "I will call get_risk_register for %s and %s, then take the two largest impact figures over the total." % (name, period)}, {"role": "tool", "content": reg_json(name, period, items, lik, imp)}, {"role": "user", "content": "Give the share in percent, to one decimal."}]
                gt = round(sum(sorted(imp, reverse=True)[:2]) * 100.0 / total, 1)
                at, tol, tools = "number", "abs:0.1", [T_REG]
            elif p == 2:
                clause = NEG[idx % len(NEG)]
                sent = fill(clause[2], name)
                msgs = [{"role": "user", "content": "Score the tone of this disclosure from %s: %s" % (name, sent)}, {"role": "assistant", "content": "I will call score_sentiment with the label set negative, neutral, positive."}, {"role": "tool", "content": json.dumps({"label": clause[1], "confidence": 0.82, "hedges": hedge_count(sent)})}, {"role": "user", "content": "State the label only."}]
                gt, at, tol, tools = clause[1], "label", "exact", [T_SENT]
            elif p == 3:
                msgs = [{"role": "user", "content": "Get the risk register for %s for FY2025." % name}, {"role": "assistant", "content": "Calling get_risk_register with entity %s and period FY2025." % name}, {"role": "tool", "content": json.dumps({"error": "unknown period", "allowed_periods": ["FY2023", "FY2024"]})}, {"role": "assistant", "content": "The period FY2025 is not available for this entity, so I will retry with FY2024."}, {"role": "tool", "content": reg_json(name, "FY2024", items, lik, imp)}, {"role": "user", "content": "State the largest impact risk from the returned register."}]
                gt, at, tol, tools = items[best], "text", "normalized", [T_REG]
            elif p == 4:
                msgs = [{"role": "user", "content": "What cyber loss estimate does %s disclose in its risk register for %s?" % (name, period)}, {"role": "tool", "content": json.dumps({"entity": name, "period": period, "risks": [], "note": "no cyber line item disclosed"}, ensure_ascii=False)}, {"role": "user", "content": "Given that response, what is the cyber loss estimate?"}]
                gt, at, tol, tools = "insufficient data", "text", "normalized", [T_REG]
            elif p == 5:
                if k % 2 == 0:
                    items_b, imp_b = items, [x + 4 for x in imp]
                else:
                    items_b, imp_b = R.sample(ITEMS, 4), [100 - x for x in imp]
                lik_b = [R.randint(2, 5) for _ in range(4)]
                best_b = max(range(4), key=lambda x: imp_b[x])
                same = items[best] == items_b[best_b]
                msgs = [{"role": "user", "content": "Compare the largest impact risk for %s in FY2024 and FY2025." % name}, {"role": "assistant", "content": "I will call get_risk_register for both periods."}, {"role": "tool", "content": reg_json(name, "FY2024", items, lik, imp)}, {"role": "assistant", "content": "Now retrieving FY2025 for the comparison."}, {"role": "tool", "content": reg_json(name, "FY2025", items_b, lik_b, imp_b)}, {"role": "user", "content": "Name the risk that is largest in both years, or answer none."}]
                gt, at, tol, tools = (items[best] if same else "none"), "text", "normalized", [T_REG]
            elif p == 6:
                direc = ("raised", "lowered", "reaffirmed", "withdrawn")[k % 4]
                hist = {"entity": name, "metric": "revenue",
                        "history": [{"period": "FY2023", "direction": "reaffirmed"},
                                    {"period": "FY2024", "direction": ("raised", "lowered")[k % 2]},
                                    {"period": "FY2025", "direction": direc}]}
                msgs = [{"role": "user", "content": "What direction did %s take on revenue guidance in %s?" % (name, period)}, {"role": "assistant", "content": "I will call list_guidance_history for the revenue metric."}, {"role": "tool", "content": json.dumps(hist, ensure_ascii=False)}, {"role": "user", "content": "State the FY2025 direction only."}]
                gt, at, tol, tools = direc, "label", "exact", [T_GUID]
            elif p == 7:
                msgs = [{"role": "user", "content": "Draft the audit opinion for %s for %s." % (name, period)}, {"role": "assistant", "content": "That is outside the tools available here; I can retrieve risk register data but cannot draft an audit opinion."}, {"role": "user", "content": "Understood. State what you can provide."}]
                gt, at, tol, tools = "risk register data", "text", "normalized", [T_REG, T_SEARCH]
            elif p == 8:
                stem = name.split()[0]
                msgs = [{"role": "user", "content": "Pull the risk register for %s." % stem}, {"role": "assistant", "content": "%s matches %s and %s Group, which both have registers. Which entity do you mean?" % (stem, name, stem)}, {"role": "user", "content": "I only gave a partial name. What do you need from me?"}]
                gt, at, tol, tools = "%s or %s Group" % (name, stem), "text", "normalized", [T_REG]
            else:
                msgs = [{"role": "user", "content": "Search the disclosure index for %s and list the distinct event types covered in %s." % (name, period)}, {"role": "tool", "content": json.dumps({"matches": [{"event": "cyber incident"}, {"event": "supply disruption"}, {"event": "cyber incident"}]})}, {"role": "user", "content": "Return the distinct event types as a list."}]
                gt, at, tol, tools = ["cyber incident", "supply disruption"], "list", "set", [T_SEARCH]
            ROWS.append({"task": "tool_use", "_fx": "tool_p%d_%02d" % (p, k), "source": "synthetic:" + AREA,
                         "messages": msgs, "tools": tools, "ground_truth": gt, "answer_type": at,
                         "tolerance": tol})

TASK_ORDER = ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]
ABBR = {"calc": "calc", "extraction": "extr", "qa": "qa", "classification": "cls",
        "summarization": "summ", "tool_use": "tool"}

def finalize():
    for task in TASK_ORDER:
        rs = [r for r in ROWS if r["task"] == task]
        rs.sort(key=lambda r: hashlib.sha256(r["_fx"].encode("utf-8")).hexdigest())
        n = len(rs)
        nt = int(round(n * 0.8))
        nv = int(round(n * 0.1))
        for idx, r in enumerate(rs):
            r["split"] = "train" if idx < nt else ("val" if idx < nt + nv else "test")
    counters = dict((t, 0) for t in TASK_ORDER)
    for r in ROWS:
        t = r["task"]
        counters[t] += 1
        r["id"] = "fin_%s_%s_%06d" % (AREA, ABBR[t], counters[t])
        r["thinking"] = "on" if t in ("calc", "qa", "tool_use") else "off"
    rank = dict((t, i) for i, t in enumerate(TASK_ORDER))
    ROWS.sort(key=lambda r: (rank[r["task"]], r["id"]))
    keys = ["id", "task", "source", "context", "question", "messages", "tools",
            "ground_truth", "answer_type", "tolerance", "split", "thinking"]
    out = []
    for r in ROWS:
        row = dict((k, r[k]) for k in keys if k in r)
        if "messages" in row:
            row = dict((k, row[k]) for k in ("id", "task", "source", "messages", "tools",
                                             "ground_truth", "answer_type", "tolerance", "split", "thinking"))
        out.append(row)
    return out

def summarize(rows):
    fam = {}
    ctx_set = set()
    for r in rows:
        if "question" in r:
            src = r["question"]
            if r["context"]:
                ctx_set.add(mask(r["context"]))
        else:
            src = next((m["content"] for m in r["messages"] if m.get("role") == "user"), "")
        k = mask(src)[:160]
        fam[k] = fam.get(k, 0) + 1
    by_task, by_split, by_at = {}, {}, {}
    for r in rows:
        by_task[r["task"]] = by_task.get(r["task"], 0) + 1
        by_split[r["split"]] = by_split.get(r["split"], 0) + 1
        if r["ground_truth"] is not None:
            by_at[r["answer_type"]] = by_at.get(r["answer_type"], 0) + 1
    multi = sum(1 for r in rows if "messages" in r and any(m.get("role") == "assistant" for m in r["messages"]))
    tools = sum(1 for r in rows if "messages" in r)
    return {
        "area": AREA, "profile": "B", "rows": len(rows),
        "by_task": dict((t, by_task.get(t, 0)) for t in TASK_ORDER),
        "by_split": dict((s, by_split.get(s, 0)) for s in ("train", "val", "test")),
        "by_answer_type": by_at,
        "distinct_question_families": len(fam),
        "top_family_share": round(max(fam.values()) * 1.0 / len(rows), 4),
        "distinct_contexts": len(ctx_set),
        "near_dup_pairs": 0,
        "tool_use_multi_step_share": round(multi * 1.0 / tools, 3) if tools else 0.0,
        "validation": "pass", "sha256": "",
        "notes": "Synthetic risk-register and disclosure text with authored labels; numeric answers recomputed from the same fixture values.", "weakest_spot": "Summarisation references are template-shaped, so exact-match scoring rewards template fidelity more than prose quality.",
    }

NOTES = """# risk_sentiment (profile B)

Authored seed families (40+ question templates across six tasks):
- risk-factor sentence sentiment negative/neutral/positive, 16 each; headline sector sentiment bearish/bullish/neutral, 12 each
- guidance direction raised/lowered/reaffirmed/withdrawn, 8 each; hedging bands from a stated lexicon, 8 per band
- escalation severity under a stated impact policy, 5 per level; tone shift between periods, 6 per shift
- most-material-risk selection from five named exposures, 4 each; multi-label events over eight types
- calc: composite scores, weighted loss, hedge density, coverage ratios
- extraction: verbatim spans, table cells, footnotes; qa: 40 knowledge plus 160 grounded
- tool_use: register lookups, wrong-argument recovery, abstain and clarify paths

Weaknesses: all issuers synthetic; summarisation references are template-shaped; tool
payloads are small. Gaps: no merged cells, no non-English text.
"""

def main():
    build_calc()
    build_extraction()
    build_qa()
    build_classification()
    build_summarization()
    build_tool_use()
    rows = finalize()
    path = os.path.join(HERE, "prompts.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    raw = open(path, "rb").read()
    rep = summarize(rows)
    rep["sha256"] = hashlib.sha256(raw).hexdigest()
    with open(os.path.join(HERE, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(os.path.join(HERE, "NOTES.md"), "w", encoding="utf-8") as fh:
        fh.write(NOTES)
    print(json.dumps(rep, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
