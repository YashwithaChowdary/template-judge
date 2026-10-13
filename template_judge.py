"""
Staged judge for device configuration templates.

A template turns a high-level request (interface, IP, VLANs ...) into the
exact commands a device needs. This judge checks a candidate template in four
increasingly demanding stages and reports how far it got:

  1 FORMAT    the template syntax is valid (balanced loops, valid tags)
  2 RENDER    it renders against a request without errors
  3 EXECUTE   the rendered commands run on a simulated device
  4 CORRECT   the final device state matches what the request asked for

Template language (small, on purpose):
  {{ name }}                          substitute a request value
  {% for v in list %} ... {% endfor %}  repeat for each item (use {{ v }})
"""
import re
from dataclasses import dataclass, field

STAGES = ["format", "render", "execute", "correct"]
TAG = re.compile(r"\{%\s*(.*?)\s*%\}")
VAR = re.compile(r"\{\{\s*(\w+)\s*\}\}")
FOR = re.compile(r"for\s+(\w+)\s+in\s+(\w+)$")


# ---------- Stage 1: format ----------
def check_format(template):
    depth = 0
    for m in TAG.finditer(template):
        tag = m.group(1)
        if FOR.match(tag):
            depth += 1
        elif tag == "endfor":
            depth -= 1
            if depth < 0:
                raise ValueError("endfor without a matching for")
        else:
            raise ValueError(f"unknown tag: {tag}")
    if depth != 0:
        raise ValueError("for loop is never closed")
    if template.count("{{") != template.count("}}"):
        raise ValueError("unbalanced {{ }}")


# ---------- Stage 2: render ----------
def render(template, request):
    loop = re.compile(r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}", re.S)

    def expand(m):
        var, coll, body = m.groups()
        if coll not in request:
            raise KeyError(f"unknown list: {coll}")
        return "".join(body.replace("{{ %s }}" % var, str(x))
                           .replace("{{%s}}" % var, str(x)) for x in request[coll])

    out = loop.sub(expand, template)

    def sub(m):
        if m.group(1) not in request:
            raise KeyError(f"undefined variable: {m.group(1)}")
        return str(request[m.group(1)])

    out = VAR.sub(sub, out)
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


# ---------- Stage 3: simulated device ----------
@dataclass
class SimDevice:
    """A toy router CLI. Rejects unknown commands and commands out of context."""
    interfaces: dict = field(default_factory=dict)
    current: str = ""

    def run(self, cmd):
        parts = cmd.split()
        if parts[:1] == ["interface"] and len(parts) == 2:
            self.current = parts[1]
            self.interfaces.setdefault(parts[1], {"ip": None, "up": False, "vlans": set()})
        elif parts[:2] == ["ip", "address"] and len(parts) == 4:
            self._need_if(cmd)
            if not all(re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", p) for p in parts[2:]):
                raise ValueError(f"bad address in: {cmd}")
            self.interfaces[self.current]["ip"] = (parts[2], parts[3])
        elif parts == ["no", "shutdown"]:
            self._need_if(cmd)
            self.interfaces[self.current]["up"] = True
        elif parts[:5] == ["switchport", "trunk", "allowed", "vlan", "add"] and len(parts) == 6:
            self._need_if(cmd)
            self.interfaces[self.current]["vlans"].add(int(parts[5]))
        elif parts == ["exit"]:
            self.current = ""
        else:
            raise ValueError(f"unknown command: {cmd}")

    def _need_if(self, cmd):
        if not self.current:
            raise ValueError(f"command outside an interface: {cmd}")


# ---------- Stage 4: correctness ----------
def check_state(device, expected):
    got = device.interfaces.get(expected["interface"])
    if got is None:
        raise AssertionError("interface was never configured")
    if got["ip"] != (expected["ip"], expected["mask"]):
        raise AssertionError(f"wrong address: {got['ip']}")
    if not got["up"]:
        raise AssertionError("interface is still shut down")
    if got["vlans"] != set(expected["vlans"]):
        raise AssertionError(f"wrong VLANs: {sorted(got['vlans'])}")


@dataclass
class Verdict:
    stage_reached: int          # 0-4: how many stages passed
    failed_stage: str           # "" if all passed
    message: str
    commands: list

    @property
    def passed(self):
        return self.stage_reached == len(STAGES)


def judge(template, request, expected):
    commands = []
    try:
        check_format(template)
    except ValueError as e:
        return Verdict(0, "format", str(e), commands)
    try:
        commands = render(template, request)
    except (KeyError, ValueError) as e:
        return Verdict(1, "render", str(e), commands)
    device = SimDevice()
    try:
        for c in commands:
            device.run(c)
    except ValueError as e:
        return Verdict(2, "execute", str(e), commands)
    try:
        check_state(device, expected)
    except AssertionError as e:
        return Verdict(3, "correct", str(e), commands)
    return Verdict(4, "", "all checks passed", commands)
