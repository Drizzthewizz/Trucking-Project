---
name: "trucking-prospect-summary-skill"
description: "Trucking Prospect Summary (R&R Transportation)"
---

Trucking Prospect Summary (R&R Transportation)
Trigger: the message is just a USDOT number, MC number and/or a trucking company name, with nothing else. Start researching right away; don't ask what they want.
Audience: the R&R Insurance Transportation sales team, which targets trucking accounts, mainly in Wisconsin.

FMCSA API (QCMobile)
Base: https://mobile.fmcsa.dot.gov/qc/services/carriers
WebKey: [Use your locally configured FMCSA key; do not publish it]
Call it with curl in bash, adding ?webKey=[KEY] to every request. Responses are JSON; data sits under "content". A "Webkey not found" response means the key was revoked; tell the user and fall back to the websites.
Network check: if there are no ready-made links in the message and curl to FMCSA or DOT domains is blocked (a 403, connect_rejected, or an x-deny-reason header), stop before researching and tell the user in two short lines: their Claude plan blocks the direct data pull; run it from the Carrier Lookup page instead (https://trucking-prospect-summary-skill.netlify.app), which works on every plan. On a paid plan they can also allow all domains under Settings > Capabilities. Ask whether they want a lighter version from public websites in the meantime, and only continue if they say yes. If they continue, label the output "Limited run: FMCSA API and L&I not reached" at the top.
How to fetch, in this order:
1. If the user's message lists ready-made data links for this carrier (the Carrier Lookup page adds them), open every one with web_fetch. These work on every Claude plan, including Free. Use them before anything else.
2. Otherwise, use curl in bash for every URL in this skill that contains [DOT], [MC] or [NAME]. web_fetch rejects URLs built from a template.
3. Pages linked from a page you already fetched can be opened with web_fetch, except SMS inspection detail pages, which FMCSA rate-limits (see the inspection datasets instead).
4. If the message came from an MC number or company name, it won't include the inspection and VIN dataset links. Once you know the DOT number, tell the user that rerunning the DOT number on the Carrier Lookup page adds the full inspection, violation and fleet data.

1. Identify the carrier
•	By name: GET /name/[NAME]. Results list dotNumber, legalName, phyCity and phyState under content[].carrier. If several carriers match, list the candidates with city and state and ask which one. If the data came from ready-made links and curl is blocked, after the user picks a carrier, ask them to run that DOT number on the Carrier Lookup page so the full data links are included.
•	By MC: GET /docket-number/[MC] (number only, no "MC" prefix).
•	Confirm the legal name, DBA and address before going further.

2. Regulatory profile (FMCSA / DOT)
API pull (run first). Call all six at once:
•	profile: GET /[DOT] (fields under content.carrier)
•	basics: GET /[DOT]/basics
•	cargo: GET /[DOT]/cargo-carried
•	operation: GET /[DOT]/operation-classification
•	oos: GET /[DOT]/oos
•	authority: GET /[DOT]/authority
Profile field names: legalName, dbaName, phyStreet, phyCity, phyState, phyZipcode, statusCode, allowedToOperate, censusTypeId.censusTypeDesc, carrierOperation.carrierOperationDesc, totalPowerUnits, totalDrivers, safetyRating, safetyRatingDate, mcs150Outdated, crashTotal, fatalCrash, injCrash, towawayCrash, vehicleInsp, vehicleOosInsp, vehicleOosRate, driverInsp, driverOosInsp, driverOosRate, hazmatInsp, hazmatOosInsp, hazmatOosRate, bipdInsuranceOnFile, cargoInsuranceOnFile, bondInsuranceOnFile (insurance amounts are in thousands), commonAuthorityStatus, contractAuthorityStatus, brokerAuthorityStatus.
Authority fields (content[].carrierAuthority): prefix, docketNumber, authorizedForProperty, authorizedForBroker, authorizedForHouseholdGoods, commonAuthorityStatus, contractAuthorityStatus, brokerAuthorityStatus.
Known API gaps (always fill from the websites below):
•	No MCS-150 mileage, mileage year or MCS-150 date. Get these from SAFER.
•	No insurance carrier names or filing history. Get these from the L&I datasets below.
•	No authority grant dates. Get these from the authority history dataset below.
•	The national OOS averages in the API are from 2009-2010. Don't use them; compare against the current averages shown on the SAFER snapshot.
•	BASIC percentiles often come back "Not Public" with an old run date. Use alert flags from the BASIC dataset and the estimated percentiles from the browser lookups, not the API.
•	cargo-carried and oos can come back empty for active carriers. Treat empty as "not returned," not "none," and check SAFER.
Keep the run lean so it fits within a Free plan's usage: aim for about 30 page reads and 5 web searches in total. If a call errors or a needed field is missing, say so in the Sources list and mark it "Needed." Never guess a value the data doesn't contain. If the API is down, use the websites for everything.
Sources, in order:
•	SAFER Company Snapshot: https://safer.fmcsa.dot.gov/query.asp?searchtype=ANY&query_type=queryCarrierSnapshot&query_param=USDOT&query_string=[DOT]
•	SMS Complete Profile: https://ai.fmcsa.dot.gov/SMS/Carrier/[DOT]/CompleteProfile.aspx
•	Licensing & Insurance (L&I): li-public.fmcsa.dot.gov is behind a reCAPTCHA, so don't use it. Pull the same data from FMCSA's open datasets with curl in bash. DOT numbers are zero-padded to 8 digits (2177711 becomes 02177711). MC numbers are written as MC plus the number padded to 6 digits (MC767467, or MC012345 for 12345).
o	Current insurer, Motus system (check this first): https://data.transportation.gov/resource/c5y8-a4uz.json?usdot_number=[DOT, not padded] (fields: insurance_company_name, effective_date and trans_date as YYYYMMDD, policy_no, max_cov_amount in dollars, ins_form_code). FMCSA moved filings to its Motus system in 2025, and the older datasets below can lag new filings by weeks. If Motus shows a filing with a newer effective date than the older active filing, Motus is current: treat it as a carrier change and add it to the filing history table.
o	Older active insurance file: https://data.transportation.gov/resource/qh9u-swkp.json?dot_number=[8-digit DOT] (fields: name_company, policy_no, effective_date, max_cov_amount in thousands, mod_col_1 coverage type, trans_date)
o	All four datasets also accept docket_number=MC[6-digit MC] in place of dot_number.
o	Insurance history: https://data.transportation.gov/resource/6sqe-dvqs.json?dot_number=[8-digit DOT]&$order=effective_date (fields: effective_date, cancl_effective_date, mod_col_1 status, cancl_method, name_company, mod_col_3 coverage type, min_cov_amount in thousands)
o	Authority history: https://data.transportation.gov/resource/9mw4-x3tu.json?dot_number=[8-digit DOT] (fields: mod_col_1 authority type, original_action_desc, orig_served_date, disp_action_desc, disp_decided_date)
o	Revocations: https://data.transportation.gov/resource/sa6p-acbp.json?dot_number=[8-digit DOT] (fields: type_license, order1_serve_date, order2_type_desc, order2_effective_date)
o	Build a filing history table in Regulatory & Safety: carrier, effective, ended, how it ended. Flag carrier changes in the last 3 years, cancellations, and revocation notices with their dates.
o	Set the X-date from the filing pattern: the current filing's effective month and day, rolled forward to the next occurrence. Say it's inferred and to confirm on the first call.
o	If a dataset returns nothing or errors, mark that item "Needed" and say which dataset failed in the Sources list.
o	Filing freshness: FMCSA shows the insurer that filed the federal BMC-91X, not necessarily who writes the policy today. Filings stay active until cancelled, and FMCSA's free datasets can lag the live L&I system by days to weeks. If the current filing is more than 18 months old, say so and make "confirm the current carrier" a first-call question.
o	Suspension notices: check https://data.transportation.gov/resource/e67p-xyd5.json?usdot_number=[DOT] (order1_serve_date, order1_type_desc, order1_effective_date as YYYYMMDD). An involuntary suspension notice means the current insurer is cancelling and the authority is suspended on order1_effective_date unless new insurance is filed. Put it first in Red flags with the deadline; it's an urgent sales opportunity.
o	Motus authority status: https://data.transportation.gov/resource/nakq-58th.json?usdot_number=[DOT] (op_auth_status Active, Pending or Inactive). Pending means a new applicant whose authority can't be granted until liability insurance is filed.
•	Inspections and violations (FMCSA SMS input datasets, records in the 24-month window; fixed row limits can truncate results; DOT number NOT zero-padded):
o	Every inspection: https://data.transportation.gov/resource/rbkj-cgst.csv?dot_number=[DOT]&$select=unique_id,insp_date,report_state,insp_level_id,driver_oos_total,vehicle_oos_total,hazmat_oos_total,unit_type_desc,unit_make,vin,unit_type_desc2,unit_make2,vin2,basic_viol,unsafe_viol,fatigued_viol,dr_fitness_viol,subt_alcohol_viol,vh_maint_viol,hm_viol&$limit=2000 (date, state, inspection level, driver/vehicle/hazmat OOS, units and VINs, violation counts by BASIC; unique_id links to violations)
o	Every violation: https://data.transportation.gov/resource/8mt8-2mdr.csv?dot_number=[DOT]&$select=unique_id,insp_date,viol_code,basic_desc,section_desc,group_desc,oos_indicator,severity_weight,viol_unit&$limit=2000 (code, BASIC, description, OOS flag, severity, driver or vehicle)
o	These four links return CSV (a header row, then one row per record) to keep large fleets small enough to read. Dates come as DD-MON-YY text; sort them as dates, not alphabetically.
o	Use these for the full inspection picture in Regulatory & Safety: inspections by state (lanes), by month (activity trend), inspection levels, OOS events with dates, every violation grouped by BASIC with counts and the most recent date, repeat violations, and which units and VINs were involved. They replace the SMS inspection detail pages, which FMCSA rate-limits.
•	Crashes, BASIC alerts and census (same open data site, CSV, DOT number NOT zero-padded):
o	Every crash on record: https://data.transportation.gov/resource/aayw-vxb3.csv?dot_number=[DOT]&$select=report_date,report_state,city,location,fatalities,injuries,tow_away,federal_recordable,cargo_body_type_id&$limit=500 (dates are YYYYMMDD; includes older crashes, so filter to the last 24 months for the crash count and list older ones separately as history)
o	BASIC measures and alert flags: https://data.transportation.gov/resource/4y6x-dmck.csv?dot_number=[DOT] (fields ending in _ac are the alert flags, Y or N; use these when the SMS site hides alerts)
o	Full MCS-150 census: https://data.transportation.gov/resource/az4n-8mr2.json?dot_number=[DOT] (blank fields are left out of the response). Use it for:
  - Contact: company_officer_1 and company_officer_2 (owner or officer names), phone, cell_phone, fax, email_address. Put the officer name, phone and email in the Snapshot.
  - Equipment ownership: owntract, owntrail, owntruck (owned); trmtract, trmtrail, trmtruck (term-leased); trptract, trptrail, trptruck (trip-leased). Show owned vs. leased counts. When most tractors are term-leased, that usually means owner-operators: flag it and tie it to occupational accident, non-trucking liability, contingent liability and WC misclassification.
  - Cargo classes: every crgo_ field marked X (crgo_coldfood, crgo_meat, crgo_produce, crgo_metalsheet, crgo_bldgmat and so on). List them.
  - Radius: interstate_beyond_100_miles, interstate_within_100_miles and the intrastate fields (driver counts by radius).
  - Drivers: total_drivers, total_cdl, avg_drivers_leased_per_month.
  - Red flags: prior_revoke_flag and prior_revoke_dot_number (this carrier replaced a revoked DOT, a classic chameleon signal); mcsipstep and mcsipdate (FMCSA safety intervention status); safety_rating, review_type and review_date.
  - Also: mcs150_date, mcs150_mileage and year, add_date (when the DOT was created), recordable_crash_rate, dockets.
o	List crashes in Regulatory & Safety as a table: date, state, city or road, injuries, tow-away, and whether it counts in SMS.
o	Crashes counted in SMS: https://data.transportation.gov/resource/4wxs-vbns.csv?dot_number=[DOT] (report_date, severity_weight, time_weight, vehicle VIN). Match to the crash file using report_number and report_state, never date and state alone. A missing match is unresolved: it can reflect lag, scope, incomplete retrieval, or a record change. Do not infer DataQs removal or scoring status from absence. Check the explicit preventability disposition and current scoring rules.
o	Out-of-service orders: https://data.transportation.gov/resource/p2mt-9ige.json?dot_number=[DOT] (oos_date, oos_reason, status, rescind_date). Any order, active or rescinded, is a major red flag; put it at the top of Red flags.
o	Shippers on inspections: https://data.transportation.gov/resource/fx4q-ay7w.csv?dot_number=[DOT] (insp_date YYYYMMDD, report_state, location_desc, shipper_name from the bill of lading, gross_comb_veh_wt, insp_carrier_name). List the shippers in Operations (top ones first, with how many times each appeared), group them by industry to describe commodities, and note heavy gross weights. If insp_carrier_name changes over time (for example Inc to LLC), report it as a name change with dates.
•	When SAFER is thin, use aggregators found through web search, such as CarrierSource and Lanefinder. Skip TruckCodex and LoadWrap; they time out or block automated reads.
•	Browser lookups: messages from the Carrier Lookup page (formerly Run Summary) may include a "Browser lookups" block, run in the user's browser just before Claude opened. Use it as data:
o	Related carriers, with the reason for each match (same street address, phone, officer, email, prior revoked DOT, or shared power unit VINs). Put them in Red flags as a table: DOT, name, city, units, status, how they're connected. How to read them: a shared officer, phone or email, or a prior revoked DOT, is a strong link (affiliate or possible chameleon). Several shared VINs with one carrier suggests leasing, owner-operators moving between carriers, or a related company. A single shared VIN is usually a used truck sold between carriers; mention it briefly at most. Same street address alone is often a shared office building. State facts, never conclusions: say "connected by" and list the reasons.
o	Estimated BASIC percentiles: label them "estimated" every time, and say they come from a peer ranking of FMCSA's public measures, not official FMCSA percentiles.
o	If the block is missing or says lookups weren't available, skip it and don't mention it.
o	The block may also include a "Peer comparison" against same-size fleets in the carrier's state (OOS rates and BASIC measures, each with "better than X% of peers"). Use it in the Executive Summary and the client PDF: lead with the categories where they beat their peers (that's the underwriter pitch), then name the ones where they trail as the areas to fix. Say it's a comparison with same-size fleets in their state, calculated from FMCSA data.
o	The block may also include "DataQs opportunities": crashes that may not be the carrier's fault (no citation to their driver in a multi-vehicle crash, or an animal strike), crashes already ruled not preventable, moving violations that could come off if the tickets were dismissed, and the MCS-150 due date. Use them as given.
o	The block may also include page-calculated rankings: "Worst units" (power units and trailers ranked by current violation points, with OOS counts and top issues), "Driver behavior" (driver violation types ranked by points, and the trucks with the most driver violations), and "Safety plan" (problems ranked by points, with who owns the fix and a suggested fix). Treat these as derived internal priorities, not official SMS scores. Check completeness and calculation provenance; do not claim a repair immediately removes historical points.
•	Trends from the inspection and violation data (no extra reads needed):
o	Violations by quarter for the last 24 months, and last 12 months vs. the prior 12 by group (speeding, lane restriction, tires, brakes, HOS and so on). Call out anything up or down sharply.
o	Expiring soon: violations and crashes dated 21 to 24 months ago drop out of SMS in the next 90 days. List what's about to age off; it's good news to bring to the prospect.
o	Top trucks: join violations to inspections on unique_id and rank power units by total severity weight. Show the top 5 VINs with year, make and their violations: fixing those units moves the scores most.
o	Fleet trend: count distinct power unit VINs inspected per 12-month period, and compare with the MCS-150 power unit count. A big drop or jump is a call question.
•	Equipment: build an equipment list from the inspection data (VIN, unit type, year from the 10th character, make from the WMI, times inspected, last inspected date). Show a short summary in the output (counts by type, make and model year range) and offer the full list as a draft vehicle schedule. Reefer detection: check the trailer makes in the inspection data (unit_make2) and the census cargo classes (crgo_coldfood, crgo_meat, crgo_produce). A reefer maker (for example CIMC Reefer), "reefer" in the make, or a cold-food cargo class means refrigerated exposure. Never say "no reefer" without checking both; if it's unclear, say reefer use is unconfirmed and ask on the first call.
Capture:
•	Legal name, DBA, address, entity type, operating status, and carrier vs. broker authority
•	USDOT and MC numbers, authority grant dates, years in business
•	Power units, drivers, MCS-150 mileage with its year, and date of the last MCS-150 update
•	Operation classification, cargo classes carried, hazmat
•	Safety rating and its date; 24-month inspections with vehicle, driver and hazmat OOS rates compared with current national averages
•	Crashes (fatal, injury, tow-away) and BASIC percentiles or alerts
•	Current insurance carrier and filing history, including frequent carrier changes, cancellations and lapses
•	Red flags: chameleon or affiliated carriers (shared address, officers or phone), recent authority, stale MCS-150, conditional or unsatisfactory rating
•	Officer names, owned vs. leased equipment, cargo classes from the census
•	Related carriers, out-of-service orders, prior revoked DOT, MCSIP status
•	Flag discrepancies between sources, for example MCS-150 unit count vs. SMS

3. Operations profile
Search the company website, news, LinkedIn, driver job postings (lanes, equipment, pay, home time), reviews, and any litigation or accident news.
Summarize:
•	Commodities and industries served
•	Equipment: dry van, reefer, flatbed, tanker, heavy haul, dump and so on
•	Radius and lanes, terminals and yards
•	Use of owner-operators, brokerage or logistics arm, warehousing
•	Growth or acquisitions, key customers, notable incidents

4. Policy Summary snapshot
Fill the R&R Transportation Policy Summary fields:
•	Left block: Company Name, State, DOT#, MC#, Insurance Carrier, plus officer name, phone and email on file from the census
•	Right block: Years in Business, Power Units (owned vs. leased), Mileage, Utilization (miles per power unit), Specialty
•	Current Program grid: Auto Liability, Physical Damage, Cargo, General Liability and Work Comp, each with Carrier, Premium, Rate and Rating Basis. Public data usually covers only the AL and cargo carriers; mark everything else "Needed."
If the user attaches the Excel template (or a policy or CAB report), populate the .xlsx. Keep the template's formatting, write utilization as a formula, and add cell comments that cite sources.

5. Executive summary for R&R Transportation
•	Account fit: fleet size tier, radius, commodity, safety posture, and how attractive this is as a prospect or where it will be hard to place
•	Coverage focus tied to their actual exposures. Examples:
o	Hazmat: MCS-90, pollution
o	Reefer: reefer breakdown and spoilage
o	Flatbed or heavy haul: cargo securement, rigging, oversize and overweight
o	Owner-operators: occupational accident, contingent liability, non-trucking liability or bobtail, WC misclassification
o	Brokerage: contingent auto and contingent cargo
o	Intermodal: trailer interchange, non-owned trailer
o	Warehousing: warehouse legal liability, GL
o	Outside repair or maintenance work: garagekeepers legal liability, products/completed operations
o	Nuclear verdict exposure: excess or umbrella adequacy
o	Tech-heavy operations: cyber
•	Units and drivers (in Regulatory & Safety, right after the violations): a "Worst units" table of the top 5 to 10 power units and trailers ranked worst to best (VIN, year and make, points, OOS, violations, top issue, and the fix for that issue), then a short "Driver behavior" summary: the top driver violation types with counts, and the trucks with the most driver violations. Say plainly that FMCSA doesn't publish driver names, so the next step is the carrier's driver list and MVRs. Use plain names for violation groups (for example "Speeding 15+ mph over or in a work zone" instead of "Speeding 4", "Lane, route and truck restriction violations" instead of "Misc Violations").
•	Risk management strategies aimed at their weak spots: lead with the safety plan ranking (biggest point drivers first, each with its owner and fix), then BASIC alerts, OOS rates and crash history mapped to specific fixes such as telematics and dash cams, driver hiring and MVR standards, maintenance programs, and DataQs challenges
•	R&R deliverables to deploy, saying which gap each one fills:
o	R&R Transportation Supplemental Application
o	New-business submission checklist (R&R Trucking quote document)
o	Operating history table (year, power units, mileage, revenue)
o	Transportation Policy Summary (Excel)
•	First-call questions and next steps. If the carrier changed insurers in the last 3 years, include a question about what drove the switch.

6. Premium estimate
Put this in its own table directly after the Snapshot section. Rows: Auto Liability, Cargo, Physical Damage, and Total (AL + Cargo + PD). Columns: Low, Mid, High, and Basis.
Rating data first. Before estimating, read the memory file /areas/premium-estimating.md (inside a Project, the same path under the Project's memory folder). It holds carrier-specific rating info the user has asked to remember, such as rates per unit or per mile, PD rates, cargo rates, schedule credits and debits, and actual quotes. Use the closest matching carrier and class. If the prospect's current carrier has stored rates, estimate the incumbent renewal with them. When nothing on file fits, or the file doesn't exist yet, fall back to market benchmarks and say so.
Auto Liability. Estimate per power unit and cross-check per mile against the MCS-150 mileage. Adjust for:
•	Radius and commodity
•	Vehicle and driver OOS rates vs. current national averages
•	Crashes in the last 24 months
•	Unsafe Driving and HOS findings
•	Years in business
•	State of domicile
•	Limit, assumed $1M CSL unless known
Physical Damage: value the fleet from VINs.
•	Pull tractor and trailer VINs from FMCSA's inspection dataset, one read each, any fleet size. DOT number here is NOT zero-padded.
o	Power units: https://data.transportation.gov/resource/rbkj-cgst.csv?dot_number=[DOT]&$select=unit_type_desc,vin,count(*)%20as%20inspections&$group=unit_type_desc,vin&$order=inspections%20DESC&$limit=300
o	Trailers: https://data.transportation.gov/resource/rbkj-cgst.csv?dot_number=[DOT]&$select=unit_type_desc2,vin2,count(*)%20as%20inspections&$group=unit_type_desc2,vin2&$order=inspections%20DESC&$limit=300
o	Each row is one distinct VIN with how many times it was inspected in the last 24 months. Units with more inspections are the active fleet. If a fleet has more than 300 units, these are the 300 most-inspected, so treat them as a sample and extrapolate.
o	Don't open SMS inspection detail pages (/SMS/Event/Inspection/...) for VINs; FMCSA rate-limits them. Use them only if both dataset links fail, and then read at most 10.
•	Only use VINs from this carrier's own inspection records. Never take VINs from web search results; a similar company name is a different carrier.
•	De-duplicate the VINs and decode the model year from the 10th character: 1=2001, 2=2002, 3=2003, 4=2004, 5=2005, 6=2006, 7=2007, 8=2008, 9=2009, A=2010, B=2011, C=2012, D=2013, E=2014, F=2015, G=2016, H=2017, J=2018, K=2019, L=2020, M=2021, N=2022, P=2023, R=2024, S=2025, T=2026, V=2027. Letters repeat every 30 years; for trucks assume the most recent match. If the message includes "Equipment seen at roadside (VINs decoded by NHTSA)" or decoded units from the Carrier Lookup page, use those makes, models, weight classes and engines as given. Otherwise decode with NHTSA's free vPIC batch decoder using curl: POST to https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/ with the form body format=json&data=VIN1;VIN2 (up to 50 VINs per call); it returns ModelYear, Make, Model, BodyClass, GVWR, EngineManufacturer, EngineModel, TrailerType, TrailerBodyType and TrailerLength. If NHTSA isn't reachable, decode the make from the first 3 characters (WMI) in code. Common WMIs: 4V4 Volvo; 1FU, 1FV, 3AK, 3AL Freightliner; 1XK, 2NK Kenworth; 1XP, 2NP Peterbilt; 1HS, 3HS, 1HT, 3HT International; 1M1, 1M2 Mack; 4WK Western Star; 1UY Utility; 1GR Great Dane; 1JJ Wabash; 3H3 Hyundai Translead; 5V8 Vanguard; 1DW Stoughton; 1PT Trailmobile. Value tractors by model (a 2024 Kenworth T680 is worth more than a 2024 day cab) when the model is known.
•	Apply current used ACV by year and type, run in code rather than estimated in prose.
•	Extrapolate the average to the MCS-150 tractor and trailer counts. Report the sample coverage, for example "49 of 66 tractors."
•	Apply a PD rate as a percentage of stated value.
•	Flag reefer units as a separate value driver.
Cargo. Estimate per unit, adjusted for:
•	Commodity: reefer, meat, metals, high-theft loads
•	Reefer breakdown coverage
•	Assumed limit
Show the basis for every figure. State the assumptions, and mark each line's confidence as Benchmark (no stored rating data) or Carrier-rated (uses stored data). The total covers AL, Cargo and PD only; note that GL, WC and umbrella are excluded.

DataQs and "we can fix this"
•	FMCSA's DataQs system lets a carrier challenge records on its safety profile. The two that move scores most: crashes reviewed under the Crash Preventability Determination Program (eligible types include being rear-ended, hit while stopped or parked, hit by a wrong-way, impaired or sleeping driver, and animal strikes, among others), and violations tied to citations that were dismissed or reduced in court.
•	From the SMS crash file (https://data.transportation.gov/resource/4wxs-vbns.json?dot_number=[DOT]): not_preventable = true means already excluded from the Crash Indicator; citation_issued_desc tells whether their driver was cited. Join to the crash file on report_number for vehicles_in_accident and crash_event_seq_id_desc.
•	A crash is worth challenging when it counts in the score, is not already not preventable, their driver wasn't cited, and it was multi-vehicle or an animal strike. Never claim a crash will be removed; say it may qualify and the police report decides.
•	How to file (put this in Servicing): the carrier makes a free login at dataqs.fmcsa.dot.gov under its USDOT, files a Request for Data Review for each crash under the Crash Preventability Determination Program with the police report and any dash cam video, and files one for each dismissed or reduced citation with the court paperwork. A crash found not preventable stays listed but stops counting in the Crash Indicator.
•	Use it as a prospecting hook: "We found [N] crashes on your record that may not be your fault, and we can help you get them out of your crash score."

Three buckets
•	End the Executive Summary with three short sections: Prospecting (why call now: renewal timing, recent switch, suspension notice, carrier churn, the DataQs hook, one compliment from the peer comparison), Marketing (what to tell underwriters: peer wins, crashes already ruled not preventable, clean inspection rate, points dropping, fleet age, years in business, and the questions they'll ask), and Servicing (how to improve the account: DataQs items, the top safety plan fixes, violations aging off, MCS-150 due date, and confirming the liability filing is current).
•	The MCS-150 is due every two years: the last digit of the USDOT number sets the month (1 is January, 0 is October) and the second-to-last digit sets the year (odd digit, odd years; even digit, even years).

Output
•	Reply in chat with clear headings, in this order: Snapshot, Premium Estimate, Regulatory & Safety, Operations, Executive Summary.
•	Date the data ("FMCSA data as of …").
•	Never invent facts. If something isn't public, say it's needed from the insured. Premium estimates are the one place figures are modeled; label them as estimates and show their basis.
•	End with a Sources list. Include the FMCSA API pull with its date, the L&I datasets used, and any fallback sites actually used.
•	After the Sources list, end the turn with a button prompt using the ask_user_input tool. One question: "What do you want next?" Options: "Client PDF report", "Draft vehicle schedule", "Populate Excel template", "Turn into a Doc". Multi-select (they can skip). If the button tool isn't available, ask the same thing in one line of text, including "or nothing for now."
•	Draft vehicle schedule (on request only): a table of every power unit and trailer from the equipment list (unit type, VIN, year, make, times inspected, last inspected), most-active units first, with blank Stated Value and Notes columns. Mark likely non-owned trailers (seen once, on out-of-state pool or shipper plates) separately. Offer it as an Excel file the rep can send the prospect to confirm and fill in values. Don't build any of these until the user picks one.

7. Client-facing report (on request only)
Trigger: run this only when the user picks "Client PDF report" from the button prompt, or asks for a client report in words. Never run it automatically. Use the data from sections 1 to 6 already in the conversation; don't re-pull FMCSA data unless the user asks or the data is more than a day old.
Purpose: a clean, branded version of the snapshot, premium estimate, and executive summary that the rep can send to the prospect. Internal notes stay out.
Logo: use assets/rr-transportation-logo.png. If that file isn't available, download it with curl from https://trucking-prospect-summary-skill.netlify.app/rr-transportation-logo.png. Place it top-left in the header at full width of the header band on white. Don't recolor, stretch, crop, or redraw it. If both are unavailable (Free and Pro plans usually block the download), don't stop with an error. Ask the user in one short message to save the logo from https://trucking-prospect-summary-skill.netlify.app/rr-transportation-logo.png and attach it to the chat, then build the report as soon as it arrives. Never redraw or substitute the logo.
Colors: deep teal (#2E5D5F) for headings and key figures; warm tan (#B8A77F) for dividers, labels, and accents; white background; dark gray (#333333) for body text. Use only these values.
Typography: a serif for display headings to match the R&R wordmark; a clean sans-serif for body text and tables. Use web-safe fallbacks.
Layout, in order: header with logo and company name, DOT and MC; Snapshot; Premium Estimate table; Regulatory and Safety; Operations; Coverage and Risk Recommendations; Next Steps; Sources. Aim for 3 to 5 pages.
Footer on every page: "R&R Insurance Transportation Division", the report date, and "Premium figures are estimates, not a quote or binder. Regulatory data from FMCSA as of [date]."
Client-facing rules:
•	Write to the prospect in plain language. Spell out any BASIC or MCS-150 term in a few words the first time it appears.
•	Leave out internal material: rep commentary, references to stored rating files, and any pricing that came from another agency's filings.
•	Premium Estimate table: show Low, Mid, High and a plain-language basis (for example, "based on fleet size, mileage, and safety record"). No "Benchmark" or "Carrier-rated" labels, no carrier names tied to rates, and no references to stored or outside rating data.
•	Red flags go in as facts from public records, with the date, framed as items to address (for example, "MCS-150 last updated in 2019; we'll ask for a current filing"). Preserve uncertainty: label inferences, omit unsupported allegations, and never convert an estimate into a fact.
•	Safety improvements: include a short "Where to focus" table with the top 3 to 5 problems from the safety plan (plain-language problem, how many violations, the fix) and the top 3 units to fix first (VIN, year and make, top issue). Frame it as help, not criticism: "fixing these first would lower your scores fastest."
•	Every "Needed" item becomes a Next Steps item to request from the insured.
•	Premium figures stay labeled as estimates, with their basis shown.
Output: export the report as a PDF and present it. Keep the chat reply as described above.

Evolving
•	When the user asks to change the format or add sources, give them the updated skill text to re-upload (the installed skill is read-only).
•	When the API returns a field name that differs from what this skill expects, tell the user so they can update this file.
•	When the user shares carrier rating info and asks to remember it, add it to /areas/premium-estimating.md (inside a Project, the same path under the Project's memory folder) under that carrier: class or commodity, rate and its basis (per unit, per mile, % of value), limits and deductibles, territory, and the date. When a quote comes back on an account we estimated, record the estimate vs. the actual so the benchmarks can be recalibrated.


Calculation safeguards: distinguish unavailable data from zero. Treat the latest returned federal liability filing as a filing, not confirmation of a current policy. Cargo and excess filings must not be selected as primary liability. Insurer-transition counts are not distinct-insurer counts. Report missing identifiers and capped datasets as incomplete. Renewal dates remain unconfirmed hypotheses.
