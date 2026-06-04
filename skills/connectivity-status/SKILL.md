________________


name: connectivity-status description: Show a list of all data-sources and their exact connectivity and scanning status. metadata: author: BigID version: 1.0.0 mcp-server: bigid
Connectivity Status
Produces a complete health snapshot of all BigID data sources by querying the Data Sources API, then classifying each source into one of nine status buckets based on scan history and connection test results.
When this skill triggers
* "What is the status of my data sources?"
* "What is the status of my connectors?"
* "Show me my connector health"
* "Which data sources have issues?"
* "Are all my connectors working?"
* "Which connectors haven't been scanned recently?"
* "Show me data source connectivity"
* Any variation of asking for a health overview of data sources or connectors


________________


Step 1 — Fetch all data sources
Call the BigID Data Sources API to retrieve all data sources:


POST /api/v1/ds-connections
body: { query: { limit: 200 } }

Use the BigID MCP server: post_v1_ds_connections on the Data Sources API.


Retrieve all pages if totalCount exceeds the limit.


________________


Step 2 — Classify each data source
For each data source, evaluate the following fields:


Field
	Meaning
	last_full_scan_at
	Unix timestamp (ms) of last successful full scan
	scan_is_success
	Boolean — did the most recent scan succeed?
	connectionStatusTest.is_success
	Boolean — did the last manual connection test succeed?
	connectionStatusTest.is_connection_ever_succeeded
	Boolean — has any connection test ever passed?
	connectionStatusScan.is_success
	Boolean — did the most recent pre-scan connection succeed?
	connectionStatusScan.is_connection_ever_succeeded
	Boolean — has the scan-time connection ever succeeded?
	enabled
	"yes" or "no" — is the DS active?
	

180-day threshold: A data source is considered "stale" if last_full_scan_at is more than 180 days before today.


Connection failed = connectionStatusTest.is_success === false OR connectionStatusScan.is_success === false.


Never connected = both is_connection_ever_succeeded fields are false or absent, AND no last_full_scan_at exists.


Draft = enabled === "no" or the DS has no scan config and no connection test ever run.


________________


Step 3 — Assign status bucket
Evaluate each DS against the following ordered rules (first match wins):


Priority
	Status bucket
	Condition
	1
	Draft
	enabled !== "yes" — data source is disabled/inactive
	2
	Never connected (test failed)
	No last_full_scan_at, no is_connection_ever_succeeded, and connectionStatusTest.is_success === false
	3
	Never scanned (scan failed)
	No last_full_scan_at AND scan_is_success === false
	4
	Never scanned
	No last_full_scan_at AND scan_is_success is not false (i.e. never attempted or unknown)
	5
	Last scan failed
	Has last_full_scan_at but scan_is_success === false
	6
	Last connection failed
	Has last_full_scan_at, scan OK, but connectionStatusTest.is_success === false OR connectionStatusScan.is_success === false
	7
	Stale — not scanned in 180+ days
	last_full_scan_at exists but is older than 180 days, and no other failure
	8
	Healthy with issues
	Scanned within 180 days but either last scan failed OR last connection failed
	9
	Healthy
	Scanned within 180 days, scan succeeded, connection OK
	

________________


Step 4 — Render the results
Present results using visualize:show_widget with:


Summary metric cards (top row):


* Total data sources
* Healthy (green)
* Issues (orange/yellow)
* Failed / Never scanned (red)
* Draft (gray)


Detailed table with columns:


* Data source name
* Type (e.g., S3 v2, MySQL, SharePoint)
* Status badge (color-coded by bucket)
* Last scanned (human-readable date or "—")
* Days since scan (or "never")
* Connection status icon


Color coding:


* Healthy → success (green)
* Healthy with issues → warning (orange)
* Stale → warning (orange)
* Last scan failed → danger (red)
* Last connection failed → danger (red)
* Never scanned → warning (orange)
* Never scanned (scan failed) → danger (red)
* Never connected → danger (red)
* Draft → secondary/muted (gray)


Sort order: danger statuses first, then warning, then healthy, then draft. Within each group, sort by days since scan descending.


________________


Step 5 — Post-render insights
After the widget, provide a short prose summary (3–5 sentences) calling out:


* The most critical issues requiring immediate attention
* Any patterns (e.g., all MySQL sources failing, a cluster of stale S3 sources)
* Recommended next actions (re-run test connection, check scanner logs, schedule a scan)


________________


Notes
* If the BigID MCP returns an empty list, state that no data sources were found and ask the user to confirm the environment.
* If scan_is_success is absent (not in the API response), treat it as unknown — do not classify as failed.
* connectionStatusScan reflects the connection made at scan time (more recent and reliable than connectionStatusTest for active sources). Prefer it when both are present.
* Always evaluate against the current date (today) for the 180-day staleness check.
* Do not expose raw field names or API responses to the user — synthesize into the status buckets above.