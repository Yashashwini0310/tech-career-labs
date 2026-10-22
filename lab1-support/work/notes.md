# Lab 1 - Investigation notes
## ticket-1001 - Site Down (502 Bad Gateway)
-*Symptom*: the site returned 502 for every request in the port 8080
-*Investigation*: API healthy on port 5000 (API with curl /health 200 OK) but not in 8080 (nginx - return connect failed error to upstream: 5001)
-*Root Cause*: nginx failed while trying to connect with 5001, when checked the config file, the API connection was routed to 5001 instead of 5000. API listens on 5000
-*Fix*: changed the 5001 to 5000 in the nginx.conf, and restarted the site
-*Verified*: Checked the health of bothe nginx and API. Both return curl /health 200 OK; grade T1 = 10/10
-*learned*: 502 = proxy can't reach the upstream ; 402 = upstream reached, route doesn't exist

## ticket
- **Symptom:**
- **Investigation:**
- **Root cause:**
- **Fix:**
- **Verified:**
- **Learned:**