# Lab 1 – Technical / Application Support

You're the new L2 support engineer at ShopFast. Production is broken in six different ways, there's a ticket queue, and last Friday's outage still has no root cause.

**Skills practised:** incident triage, root cause analysis, nginx, REST APIs with curl, Python debugging, PostgreSQL (EXPLAIN, indexes, pg_stat_activity), log analysis with grep/awk/Python, Bash scripting, runbooks and postmortems.

```bash
cd lab1-support
./lab.sh start      # first start: ~2-3 minutes
./lab.sh grade      # see your score at any time
```

Then open **TASKS.md**.

| Folder | What's in it |
|---|---|
| `tickets/` | The support queue |
| `logs/` | Friday's historical logs (Task 7) |
| `app/`, `nginx/`, `client/` | The system you're supporting |
| `work/` | **Your answers**, scripts and documents (graded) |
| `templates/` | Runbook and postmortem templates |
| `hints/` | Three levels of hints per task |
| `solutions/` | Model answers (try first!) |
| `CV_NOTES.md` | What you can put on your CV afterwards |

Resources: about 1.5 GB RAM, 2-core Codespace is enough.
