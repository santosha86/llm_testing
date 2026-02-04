# Fixed SQL queries for category questions
Fuel_Type_Desc_quantity = """
SELECT
  "Fuel Type Desc",
  SUM("Requested Quantity") AS total_requested_quantity
FROM waybills
GROUP BY "Fuel Type Desc"
ORDER BY total_requested_quantity DESC
LIMIT 1;
"""

status_of_waybill = """
SELECT
  SUM(CASE WHEN "Waybill Status Desc" = 'Delivered' THEN 1 ELSE 0 END) AS delivered_count,
  SUM(CASE WHEN "Waybill Status Desc" = 'Expired' THEN 1 ELSE 0 END) AS expired_count,
  SUM(CASE WHEN "Waybill Status Desc" = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_count
FROM waybills;
"""

details_of_waybill = """
SELECT
  "Waybill Number",
  "Waybill Status Desc",
  "Waybill Status Date",
  "Waybill Status Time"
FROM waybills
WHERE "Waybill Number" = 'D6-25-0039536';
"""

waybills_for_contractor = """
SELECT *
FROM waybills
WHERE LOWER("Vendor Name") LIKE '%alhbbas%'
   OR LOWER("Vendor Name") LIKE '%trading%'
   OR LOWER("Vendor Name") LIKE '%transport%';
"""

contractor_wise_waybills = """
SELECT "Vendor Name", "Waybill Number"
FROM waybills
ORDER BY "ALHBBAS FOR TRADING, TRANSPORT";
"""

full_details = """
SELECT *
FROM waybills
WHERE "Waybill Number" = '1-25-0010844';
"""

vendor_rejected_requests = """
SELECT
  "Vendor Name",
  COUNT(*) AS rejected_count
FROM waybills
WHERE "Waybill Status Desc" = 'Rejected'
GROUP BY "Vendor Name"
ORDER BY rejected_count DESC
LIMIT 1;
"""

vendors_requests = """
SELECT
  "Vendor Name",
  COUNT(*) AS total_requests
FROM waybills
GROUP BY "Vendor Name"
ORDER BY total_requests DESC;
"""

# Mapping: question text -> SQL query
FIXED_QUERIES = {
    "How many waybills are Delivered / Expired / Cancelled?": status_of_waybill,
    "Which fuel type has the highest total requested quantity?": Fuel_Type_Desc_quantity,
    "What is the current status of waybill D6-25-0039536?": details_of_waybill,
    "Show full details of waybill 1-25-0010844": full_details,
    "Which waybills are assigned to ALHBBAS FOR TRADING, TRANSPORT?": waybills_for_contractor,
    "Show contractor-wise waybill list": contractor_wise_waybills,
    "Which vendor has the highest number of rejected requests": vendor_rejected_requests,
    "Which vendors created the most requests": vendors_requests,
}