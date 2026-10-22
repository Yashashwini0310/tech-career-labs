# Tech Career Labs

Hands-on practice environments for five tech roles, built around one fictional Irish online retailer, **ShopFast**. Each lab gives you a realistic work situation, broken systems or messy data, graded tasks, hints and model solutions.

| Lab | Role | Status | Main tools |
|---|---|---|---|
| [Lab 1](lab1-support/) | Technical / Application Support | ✅ Ready | nginx, Flask API, PostgreSQL, logs, Bash, tickets |
| Lab 2 | Database Administrator (DBA) | 🔜 Next | PostgreSQL, SQL Server, MySQL, backups, tuning |
| Lab 3 | Data Analyst / BI | 🔜 | SQL, Pandas, A/B testing, Excel, Power BI, Metabase |
| Lab 4 | Data Engineer / Data Ops | 🔜 | Airflow, dbt, PySpark/Delta, Kafka, Databricks, Snowflake |
| Lab 5 | Cloud / DevOps | 🔜 | Docker, Kubernetes, Helm, GitHub Actions, Jenkins, Terraform, Grafana |

All labs share the same ShopFast dataset: 20,000 customers, 500 products, 200,000 orders and 450,000 order items from Jan 2025 to Oct 2026. Skills you learn in one lab carry into the next.

---

## Setup: GitHub Codespaces (nothing to install on your laptop)

**1. Put this folder on GitHub (one time)**
1. Sign in at github.com and click **New repository**. Name it `tech-career-labs`, set it to **Public** so recruiters can see it, and click **Create repository**.
2. On the new repo page, click **uploading an existing file**, drag in all the files and folders from this zip, and click **Commit changes**.
   (If you know git: `git init && git add . && git commit -m "Initial labs" && git push`.)

**2. Open it in a Codespace**
1. On your repo page, click the green **Code** button → **Codespaces** tab → **⋯** → **New with options**.
2. Choose **Machine type: 2-core** for Labs 1–3. Use **4-core** for Labs 4–5.
3. Click **Create codespace**. VS Code opens in your browser after 2–3 minutes, with Docker ready.

**3. Start a lab**
In the terminal at the bottom of the screen:
```bash
cd lab1-support
./lab.sh start
```
When a port opens, Codespaces shows a popup. Click **Open in Browser** to see it, or just use `curl` in the terminal.

**4. Stop when you finish (important)**
- Free accounts get **120 core-hours a month**: about 60 hours on a 2-core machine, or 30 on a 4-core.
- When you're done: click the green **Codespaces** button at the bottom left → **Stop Current Codespace**. It also stops by itself after 30 minutes idle.
- Your work is saved while the codespace is stopped. **Commit your `work/` folder to GitHub** regularly (Source Control icon on the left → message → Commit → Sync).
- Don't add a payment method under GitHub billing, and you can never be charged.

### Running on your own laptop instead
Install Docker Desktop, plus Git and Python 3. Then clone the repo and run the same `./lab.sh start` from **Git Bash** or **WSL**. Each lab needs 2–6 GB of RAM.

---

## How every lab works
1. `./lab.sh start` builds the environment.
2. Read `TASKS.md`: the scenario, then 8–12 tasks worth 100 points.
3. Put your answers, scripts and documents in `work/`.
4. `./lab.sh grade` checks the live system and your files, and shows your score.
5. Stuck? `hints/HINTS.md` has three levels of hints. `solutions/` has model answers.
6. At 80+, read `CV_NOTES.md` for honest CV bullets and interview stories.

`./lab.sh reset` starts the lab again from scratch. `./lab.sh clean` removes its containers and images to free space.

## Honesty rule
These are **practice projects**. List them under **Projects** on your CV ("Production Support Simulation" and so on), never as work experience.
