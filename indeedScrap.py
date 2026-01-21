import curl_cffi, requests, time
import sys
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, parse_qs
import builtins

# Wrap built-in print to also append output to log.txt
_orig_print = builtins.print
def _print_and_log(*args, **kwargs):
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    # Build the message string
    try:
        msg = sep.join(str(a) for a in args) + end
    except Exception:
        # Fallback in case of non-stringable objects
        msg = ' '.join(map(repr, args)) + end
    # Print to stdout using original print
    _orig_print(msg, end='')
    # Append to log file
    try:
        with open('/data/log.txt', 'a', encoding='utf-8') as lf:
            lf.write(msg)
    except Exception:
        # If logging fails, still continue silently
        pass

# Override builtins.print so all prints go through our logger
builtins.print = _print_and_log


session = curl_cffi.Session(
    impersonate="chrome131_android"
)

def fetch_url(url, save_path=None, allow_404=False):
    """Fetch URL with retries. If allow_404 is True, return on 404 (do not retry).
    If save_path is provided, save response content only for successful (2xx) responses.
    """
    while True:
        resp = session.get(url)
        code = resp.status_code
        if code // 100 == 2:
            break
        if allow_404 and code == 404:
            print(f"Received 404 for {url}, skipping as requested")
            break
        print(f"Received non-200 status code: {code}, retrying...")
        time.sleep(5)

    print(resp.status_code)
    # Do not write any HTML files to disk here (avoid creating .html files)
    return resp

if len(sys.argv) > 1 and sys.argv[1].strip():
    keyword = sys.argv[1]
else:
    keyword = "java dev"

keyword_encoded = requests.utils.quote(keyword)

url = f"https://fr.indeed.com/jobs?q={keyword_encoded}&l=Paris&radius=25"

print(f"Fetching URL: {url}")

resp = fetch_url(url)

# Extract titles and jk from the saved HTML


soup = BeautifulSoup(resp.content, 'html.parser')
results = []

job_cards = soup.find_all('a', {'data-jk': True})

for card in job_cards:
    jk = card.get('data-jk')
    title = card.get_text(strip=True)
    if title:  # Only add if title exists
        results.append({'title': title, 'jk': jk})

if not results:
    print("No job cards with `data-jk` found.")
else:
    jobs_data = []
    for idx, job in enumerate(results, start=1):
        jk = job['jk']
        view_url = f"https://fr.indeed.com/m/viewjob?jk={jk}"
        print(f"({idx}/{len(results)}) Fetching: {view_url}")

        # Save each job HTML to a separate file and get the response
        resp_job = fetch_url(view_url, save_path=f"job_{jk}.html", allow_404=True)

        # If not successful (including 404), skip parsing this job
        if resp_job.status_code // 100 != 2:
            print(f"Skipping jk={jk} due to status {resp_job.status_code}")
            continue

        # Parse the job HTML
        soup_job = BeautifulSoup(resp_job.content, 'html.parser')

        title_text = (soup_job.title.string or '').strip() if soup_job.title else ''
        parts = [p.strip() for p in title_text.split(' - ')]
        job_title = parts[0] if parts else ''
        location = parts[1] if len(parts) >= 2 else ''

        # JK and canonical
        jk_val = None
        canonical = ''
        can = soup_job.find('link', rel='canonical')
        if can and can.get('href'):
            canonical = can.get('href')
            qs = parse_qs(urlparse(canonical).query)
            jk_val = qs.get('jk', [None])[0]
        if not jk_val:
            share_meta = soup_job.find('meta', id='indeed-share-url')
            if share_meta and share_meta.get('content'):
                canonical = share_meta.get('content')
                qs = parse_qs(urlparse(canonical).query)
                jk_val = qs.get('jk', [None])[0]

        og_desc = soup_job.find('meta', property='og:description')
        company = og_desc.get('content').strip() if og_desc and og_desc.get('content') else None

        body_text = ' '.join([p.get_text(' ', strip=True) for p in soup_job.find_all('p')])

        contract = None
        for token in ['CDI', 'CDD', 'Freelance', 'Stage', 'Intérim', 'Alternance']:
            if token in body_text:
                contract = token
                break

        # Enhanced description extraction:
        # 1) Try LD+JSON description
        # 2) Look for common IDs/classes/attributes containing 'job' and 'desc'
        # 3) Look for itemprop=description or role=main
        # 4) Fallback: join all <p> or body text
        desc = ''

        # 1) LD+JSON
        ld_json_desc = None
        for script_tag in soup_job.find_all('script', type='application/ld+json'):
            try:
                ld = json.loads(script_tag.string or '{}')
                if isinstance(ld, dict) and ld.get('description'):
                    ld_json_desc = ld.get('description')
                    break
                # sometimes it's a list
                if isinstance(ld, list):
                    for item in ld:
                        if isinstance(item, dict) and item.get('description'):
                            ld_json_desc = item.get('description')
                            break
                    if ld_json_desc:
                        break
            except Exception:
                continue
        if ld_json_desc:
            desc = ld_json_desc.strip()
        else:
            # 2) heuristic selectors
            selectors = [
                '#jobDescriptionText',
                '[id*=job][id*=desc]',
                '[class*=job][class*=desc]',
                'div[itemprop=description]',
                'div[data-tn-component="jobDescription"]',
                '[role=main]',
                'main',
            ]
            main_node = None
            for sel in selectors:
                node = soup_job.select_one(sel)
                if node and node.get_text(strip=True):
                    main_node = node
                    break
            if main_node:
                desc = main_node.get_text('\n', strip=True)
            else:
                # 4) fallback: join all paragraphs; if none, use body text
                paras = [p.get_text(' ', strip=True) for p in soup_job.find_all('p') if p.get_text(strip=True)]
                if paras:
                    desc = '\n\n'.join(paras)
                else:
                    body = soup_job.body.get_text(' ', strip=True) if soup_job.body else ''
                    desc = body

        data = {
            'title': title_text,
            'job_title': job_title,
            'jk': jk_val or jk,
            'company': company,
            'location': location,
            'canonical': view_url.replace('/m/viewjob', '/viewjob'),
            'contract': contract,
            'description': desc,
        }
        jobs_data.append(data)

        # Sleep between requests
        time.sleep(2)

    # Write combined JSON
    with open('jobs_all.json', 'w', encoding='utf-8') as jf:
        json.dump(jobs_data, jf, ensure_ascii=False, indent=2)

    print(f'Wrote {len(jobs_data)} jobs to jobs_all.json')


