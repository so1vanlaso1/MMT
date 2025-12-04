import argparse
import os
import re
from typing import Dict, Tuple, List, Union

from daemon import create_proxy

PROXY_PORT = 8080
DEFAULT_POLICY = "round-robin"
HOST_BLOCK_PATTERN = r'host\s+"([^"]+)"\s*\{(.*?)\}'
PROXY_PASS_PATTERN = r'proxy_pass\s+http://([^\s;]+);'
DIST_POLICY_PATTERN = r'dist_policy\s+([-\w]+)'


def parse_virtual_hosts(config_file: str) -> Dict[str, Tuple[Union[str, List[str]], str]]:
    """
    Parse virtual-host mapping from `config_file`.

    Returns:
        dict: routes[host] = (proxy_pass | [proxy_pass...], policy)
    """
    config_path = os.path.abspath(config_file)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"[start_proxy] Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as cfg:
        config_text = cfg.read()

    routes: Dict[str, Tuple[Union[str, List[str]], str]] = {}

    for host, block in re.findall(HOST_BLOCK_PATTERN, config_text, re.DOTALL):
        proxy_passes = re.findall(PROXY_PASS_PATTERN, block)
        policy_match = re.search(DIST_POLICY_PATTERN, block)
        policy = (policy_match.group(1).lower() if policy_match else DEFAULT_POLICY).strip()

        if not proxy_passes:
            raise ValueError(f"[start_proxy] Host '{host}' lacks proxy_pass entries")

        if len(proxy_passes) == 1:
            routes[host] = (proxy_passes[0], policy)
        else:
            routes[host] = (proxy_passes, policy)

    if not routes:
        raise ValueError("[start_proxy] No host blocks were parsed from config")

    for host, mapping in routes.items():
        print(f"[start_proxy] {host} -> {mapping}")

    return routes


def main() -> None:
    parser = argparse.ArgumentParser(prog="Proxy", description="Reverse proxy daemon", epilog="Proxy daemon")
    parser.add_argument("--server-ip", default="0.0.0.0")
    parser.add_argument("--server-port", type=int, default=PROXY_PORT)
    parser.add_argument(
        "--config",
        default=os.path.join(os.path.dirname(__file__), "config", "proxy.conf"),
        help="Path to proxy configuration file",
    )

    args = parser.parse_args()
    routes = parse_virtual_hosts(args.config)
    create_proxy(args.server_ip, args.server_port, routes)


if __name__ == "__main__":
    main()