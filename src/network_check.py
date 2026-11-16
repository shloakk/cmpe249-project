"""Bounded package-server connectivity checks; never downloads packages."""
import concurrent.futures
import json
import platform
import sys
import urllib.error
import urllib.request

# The file host root may return 404; that still proves HTTP/TLS reachability.
ENDPOINTS = {
    'conda-main-linux': ('https://repo.anaconda.com/pkgs/main/linux-64/repodata.json', False),
    'conda-main-noarch': ('https://repo.anaconda.com/pkgs/main/noarch/repodata.json', False),
    'conda-r-linux': ('https://repo.anaconda.com/pkgs/r/linux-64/repodata.json', False),
    'conda-r-noarch': ('https://repo.anaconda.com/pkgs/r/noarch/repodata.json', False),
    'pypi-index': ('https://pypi.org/simple/pip/', False),
    'pypi-files': ('https://files.pythonhosted.org/', True),
    'pytorch-cu118': ('https://download.pytorch.org/whl/cu118/torch/', False),
}


def check(name, url, allow_not_found=False):
    result = {'endpoint': name, 'url': url, 'reachable': False}
    request = urllib.request.Request(url, method='HEAD')
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result.update(status=response.status, reachable=200 <= response.status < 400)
    except urllib.error.HTTPError as error:
        result.update(status=error.code, reachable=allow_not_found and error.code == 404,
                      error=str(error))
    except (OSError, urllib.error.URLError) as error:
        result['error'] = str(error)
    return result


def main():
    print('Network check host:', platform.node(), flush=True)
    print('HEAD requests only; successful reachability does not guarantee installation.', flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(ENDPOINTS)) as pool:
        futures = [pool.submit(check, name, *args) for name, args in ENDPOINTS.items()]
        results = [future.result() for future in futures]
    for result in results:
        print(json.dumps(result, sort_keys=True), flush=True)
    if not all(result['reachable'] for result in results):
        print('PACKAGE_NETWORK_BLOCKED; do not retry installation until a transfer route is prepared.', flush=True)
        return 1
    print('PACKAGE_NETWORK_OK', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
