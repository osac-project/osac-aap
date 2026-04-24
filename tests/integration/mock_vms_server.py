"""Mock VAST VMS API server for storage provider integration tests.

Simulates VAST VMS REST endpoints for tenants, vippools, views,
viewpolicies, and quotas. Follows the mock_api_server.py pattern.

Auth: vast-ansible sends either ``Authorization: Api-Token <token>`` header
or HTTP Basic Auth on every request -- no login endpoint required.

Usage:
    python3 mock_vms_server.py <port> [--tls --cert <path> --key <path>]
"""

import argparse
import copy
import json
import ssl
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

CALL_LOG = []

_NEXT_ID = {r: 1 for r in ("tenants", "vippools", "views", "viewpolicies", "quotas")}
_STORE = {r: {} for r in _NEXT_ID}
_LOCK = threading.Lock()

CANNED_DEFAULTS = {
    "tenants": {"name": "", "client_ip_ranges": [], "encryption": False},
    "vippools": {"name": "", "ip_ranges": [], "tenant_id": 1},
    "views": {"name": "", "path": "/", "policy_id": 1, "tenant_id": 1},
    "viewpolicies": {"name": "", "flavor": "NFS", "protocols": ["NFS"], "tenant_id": 1},
    "quotas": {"name": "", "hard_limit": 0, "soft_limit": 0, "tenant_id": 1},
}

_RESOURCES = set(CANNED_DEFAULTS)


def _strip_sensitive(headers):
    """Return header dict with Authorization removed."""
    return {k: v for k, v in headers.items() if k.lower() != "authorization"}


def _log(entry):
    if "body" in entry and isinstance(entry["body"], dict):
        entry = dict(entry)
        body = dict(entry["body"])
        for field in ("password", "secret", "token"):
            body.pop(field, None)
        entry["body"] = body
    with _LOCK:
        CALL_LOG.append(entry)


class MockVmsHandler(BaseHTTPRequestHandler):
    def _parse_path(self):
        """Return (resource, resource_id) or (None, None) for non-resource paths."""
        path = self.path.split("?")[0].rstrip("/")
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api":
            parts = parts[2:]
        if not parts or parts[0] not in _RESOURCES:
            return None, None
        resource = parts[0]
        resource_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        return resource, resource_id

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            return None

    def _respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/_calls":
            with _LOCK:
                snapshot = list(CALL_LOG)
            self._respond(200, snapshot)
            return

        if path == "/_reset":
            with _LOCK:
                CALL_LOG.clear()
                for r in _STORE:
                    _STORE[r].clear()
                for r in _NEXT_ID:
                    _NEXT_ID[r] = 1
            self._respond(200, {"status": "reset"})
            return

        if path.rstrip("/") == "/api":
            _log({"method": "GET", "path": path, "headers": _strip_sensitive(dict(self.headers))})
            self._respond(200, {"status": "ok"})
            return

        resource, resource_id = self._parse_path()
        _log({"method": "GET", "path": path, "headers": _strip_sensitive(dict(self.headers))})

        if resource is None:
            self._respond(404, {"error": "not found"})
            return

        with _LOCK:
            if resource_id is not None:
                obj = _STORE[resource].get(resource_id)
            else:
                obj = list(_STORE[resource].values())
        if resource_id is not None:
            if obj is None:
                self._respond(404, {"error": f"{resource} {resource_id} not found"})
            else:
                self._respond(200, obj)
        else:
            self._respond(200, obj)

    def do_POST(self):
        path = self.path.split("?")[0]
        body = self._read_body()
        if body is None:
            self._respond(400, {"error": "invalid JSON body"})
            return
        _log({"method": "POST", "path": path, "headers": _strip_sensitive(dict(self.headers)), "body": body})

        resource, _ = self._parse_path()
        if resource is None:
            self._respond(404, {"error": "not found"})
            return

        with _LOCK:
            obj_id = _NEXT_ID[resource]
            _NEXT_ID[resource] += 1
            obj = {**copy.deepcopy(CANNED_DEFAULTS[resource]), **body, "id": obj_id}
            _STORE[resource][obj_id] = obj
        self._respond(201, obj)

    def do_PATCH(self):
        path = self.path.split("?")[0]
        body = self._read_body()
        if body is None:
            self._respond(400, {"error": "invalid JSON body"})
            return
        _log({"method": "PATCH", "path": path, "headers": _strip_sensitive(dict(self.headers)), "body": body})

        resource, resource_id = self._parse_path()
        if resource is None or resource_id is None:
            self._respond(404, {"error": "not found"})
            return

        result = None
        with _LOCK:
            obj = _STORE[resource].get(resource_id)
            if obj is not None:
                obj.update(body)
                result = dict(obj)
        if result is None:
            self._respond(404, {"error": f"{resource} {resource_id} not found"})
        else:
            self._respond(200, result)

    def do_DELETE(self):
        path = self.path.split("?")[0]
        _log({"method": "DELETE", "path": path, "headers": _strip_sensitive(dict(self.headers))})

        resource, resource_id = self._parse_path()
        if resource is None or resource_id is None:
            self._respond(404, {"error": "not found"})
            return

        with _LOCK:
            if resource_id not in _STORE[resource]:
                found = False
            else:
                found = True
                del _STORE[resource][resource_id]
        if not found:
            self._respond(404, {"error": f"{resource} {resource_id} not found"})
        else:
            self.send_response(204)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int)
    parser.add_argument("--tls", action="store_true")
    parser.add_argument("--cert", default=None)
    parser.add_argument("--key", default=None)
    args = parser.parse_args()

    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("127.0.0.1", args.port), MockVmsHandler)

    if args.tls:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=args.cert, keyfile=args.key)
        server.socket = ctx.wrap_socket(server.socket, server_side=True)

    print(f"Mock VMS server running on port {args.port} (tls={args.tls})", flush=True)
    server.serve_forever()
