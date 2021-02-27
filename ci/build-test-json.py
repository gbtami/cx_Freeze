import json
import os
import subprocess
import sys
import sysconfig

FILENAME = os.path.join(os.path.dirname(sys.argv[0]), "build-test.json")
IS_MINGW = sysconfig.get_platform() == "mingw"
IS_LINUX = sys.platform == "linux"
HOSTTYPE = (
    os.environ.get("HOSTTYPE")
    or (sysconfig.get_config_var("HOST_GNU_TYPE") or "-").split("-")[0]
)

if len(sys.argv) != 3:
    sys.exit(1)

with open(FILENAME) as fp:
    data = json.load(fp)

name = sys.argv[1]
func = sys.argv[2]
test_data = data.get(name, {})

# verify if platform to run is in use
platform = test_data.get("platform", [])
if isinstance(platform, str):
    platform = [platform]
if platform and sys.platform not in platform:
    sys.exit()

# process requirements
if func == "req":
    requires = test_data.get("requirements", [])
    if isinstance(requires, str):
        requires = [requires]
    requires = "pip,setuptools,wheel,importlib-metadata".split(",") + requires
    out = []
    for req in requires:
        if ";" in req:
            require = req.replace(" ", "")
        else:
            require = req
        if IS_LINUX and require.startswith("wxPython"):
            output = subprocess.check_output(
                [
                    "pip",
                    "install",
                    "-f",
                    "https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-18.04",
                    "wxPython",
                ]
            )
        elif IS_MINGW and ";sys_platform!='mingw'" in require:
            continue
        else:
            if IS_MINGW:
                package = require.split(";")[0]
                try:
                    output = subprocess.check_output(
                        [
                            "pacman",
                            "--noconfirm",
                            "-S",
                            "--needed",
                            f"mingw-w64-{HOSTTYPE}-python-{package}",
                        ]
                    )
                except subprocess.CalledProcessError:
                    pass
                else:
                    continue
            output = subprocess.check_output(
                ["pip", "install", "--upgrade", require]
            )
        out.append(output)
    print(b"\n".join(out))

else:  # app number
    test_app = test_data.get("test_app", [f"test_{name}"])
    if isinstance(test_app, str):
        test_app = [test_app]
    line = int(func or 0)
    for app in test_app[:]:
        if IS_MINGW and app.startswith("gui:"):
            test_app.remove(app)
    if line < len(test_app):
        print(test_app[line])
