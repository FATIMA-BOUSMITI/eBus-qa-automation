"""Read-only static inspection; reports candidate origins, never app data or tokens."""
import argparse
import hashlib
import json
import re
import zipfile
from urllib.parse import urlsplit


def inspect(path):
    result = {"apk_sha256": "", "dart_artifacts": [], "candidate_origins": [],
              "embedded_source_configuration": []}
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    result["apk_sha256"] = digest.hexdigest()
    origins = set()
    with zipfile.ZipFile(path) as apk:
        for name in apk.namelist():
            if not (name.endswith("/kernel_blob.bin") or name.endswith("/libapp.so")):
                continue
            result["dart_artifacts"].append(name)
            data = apk.read(name)
            # Debug kernels can include Dart source. Ignore commented alternatives.
            source = re.search(rb'class AppConstants\s*\{(.{0,4000}?)\}', data, re.S)
            if source:
                declarations = b'\n'.join(line for line in source.group(1).splitlines()
                                          if not line.lstrip().startswith(b'//'))
                base = re.search(rb'''static\s+const\s+String\s+baseUrl\s*=\s*(['"])(https?://[^'"\s]+)\1\s*;''', declarations)
                if base:
                    result["embedded_source_configuration"].append({
                        "artifact": name, "field": "AppConstants.baseUrl",
                        "active_literal": base.group(2).decode("ascii"),
                        "commented_alternatives_ignored": True,
                    })
                environment = re.search(rb'''static\s+const\s+String\s+baseUrl\s*=\s*String\.fromEnvironment\(\s*(['"])API_BASE_URL\1\s*,\s*defaultValue:\s*(['"])(https?://[^'"\s]+)\2''', declarations)
                if environment:
                    result["embedded_source_configuration"].append({
                        "artifact": name, "field": "AppConstants.baseUrl",
                        "environment_key": "API_BASE_URL",
                        "default_literal": environment.group(3).decode("ascii"),
                        "note": "Compare with the recorded dart-define used for compilation.",
                    })
            dio = re.search(rb'class DioClient\b(.{0,1800})', data, re.S)
            if dio and re.search(rb'baseUrl\s*:\s*AppConstants\.baseUrl', dio.group(1)):
                result["dio_uses_appconstants_baseurl"] = True
            # Dart string tables may concatenate an URL and the next symbol.
            pattern = rb'https?://(?:[A-Za-z0-9.\-]+?\.onrender\.com|[A-Za-z0-9.\-]+?\.firebaseio\.com|localhost|(?:[0-9]{1,3}\.){3}[0-9]{1,3})(?::[0-9]+)?'
            for raw in re.findall(pattern, data):
                origin = raw.decode("ascii")
                host = urlsplit(origin).hostname or ""
                if "ebus" in host.lower() or "onrender.com" in host or host == "localhost" or re.fullmatch(r"\d+\.\d+\.\d+\.\d+", host):
                    origins.add(origin)
    result["candidate_origins"] = sorted(origins)
    result["limitation"] = "Static string presence is configuration evidence, not proof of a successful runtime request."
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("apk")
    args = parser.parse_args()
    print(json.dumps(inspect(args.apk), indent=2))
