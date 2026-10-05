"""Publish a verified Quick Tunnel origin to KV; never deploy or handle app credentials."""
import argparse
import os
import queue
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / 'praxis-dashboard'
TUNNEL_URL = re.compile(r'https://[a-z0-9]+(?:-[a-z0-9]+)*\.trycloudflare\.com')
WRANGLER = 'wrangler@4.137.0'


def validate_origin(origin: str) -> str:
    value = urlsplit(origin)
    if (not TUNNEL_URL.fullmatch(origin) or value.username or value.password
            or value.port or value.query or value.fragment):
        raise ValueError('Expected an exact HTTPS Quick Tunnel origin')
    return origin


def publish_origin(origin: str) -> None:
    origin = validate_origin(origin)
    npx = shutil.which('npx.cmd') or shutil.which('npx')
    if not npx:
        raise RuntimeError('Node.js/npm is required for automatic address updates.')
    deadline = time.monotonic() + 120
    while True:
        try:
            with urlopen(origin + '/api/v1/health', timeout=10) as response:
                if response.status == 200:
                    break
        except (URLError, TimeoutError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError('Public tunnel health did not pass; address was not updated.')
        time.sleep(3)
    command = [npx, '--yes', '--offline', WRANGLER, 'kv', 'key', 'put',
               'backend-origin', origin, '--binding', 'PRAXIS_TUNNEL', '--remote']
    for attempt in range(3):
        result = subprocess.run(command, cwd=DASHBOARD, timeout=90, check=False,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding='utf-8', errors='replace')
        if result.returncode == 0:
            print('Address updated automatically. Cloudflare propagation may take about a minute.', flush=True)
            print('Dashboard/phone server: https://praxisdashboard.debopomrc2602.workers.dev/', flush=True)
            return
        if attempt < 2:
            time.sleep(5)
    # Do not emit CLI output, which can contain authorization links or credentials.
    raise RuntimeError('Cloudflare address update failed. Run npx wrangler@4.137.0 login '
                       'from praxis-dashboard, approve in browser, then retry. '
                       'If offline cache is missing, run npx --yes wrangler@4.137.0 --version once.')


def run_tunnel() -> None:
    import msvcrt

    runtime = ROOT / 'runtime'
    runtime.mkdir(exist_ok=True)
    with (runtime / 'tunnel-launcher.lock').open('a+b') as lock:
        lock.seek(0)
        if not lock.read(1):
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise RuntimeError('An online tunnel launcher is already running.') from error
        connector = runtime / 'cloudflared.exe'
        process = subprocess.Popen(
            [str(connector), 'tunnel', '--no-autoupdate', '--protocol', 'http2',
             '--edge-ip-version', '4', '--url', 'http://127.0.0.1:8787'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding='utf-8', errors='replace', creationflags=subprocess.CREATE_NO_WINDOW,
        )
        lines: queue.Queue[str | None] = queue.Queue()

        def read_output() -> None:
            assert process.stdout is not None
            for line in process.stdout:
                lines.put(line)
            lines.put(None)

        threading.Thread(target=read_output, daemon=True).start()
        published = False
        deadline = time.monotonic() + 180
        try:
            while True:
                try:
                    line = lines.get(timeout=1)
                except queue.Empty:
                    if not published and time.monotonic() > deadline:
                        raise RuntimeError('Tunnel creation timed out; check internet and retry.')
                    continue
                if line is None:
                    raise RuntimeError('Tunnel connector stopped. Rerun the launcher to reconnect.')
                print(line.rstrip(), flush=True)
                found = TUNNEL_URL.search(line)
                if found and not published:
                    publish_origin(found.group())
                    published = True
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            if process.stdout:
                process.stdout.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish-existing', help='Verify/publish an already running tunnel without restarting it')
    args = parser.parse_args()
    os.environ['WRANGLER_SEND_METRICS'] = 'false'
    try:
        if args.publish_existing:
            publish_origin(args.publish_existing)
        else:
            run_tunnel()
    except KeyboardInterrupt:
        print('Tunnel stopped. Praxis data and models remain on this computer.')
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), flush=True)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
