"""A reference template plus faulty variants with known fixes."""
REQUEST = {"interface": "eth0", "ip": "10.0.0.1", "mask": "255.255.255.0",
           "vlans": [10, 20]}
EXPECTED = REQUEST

GOOD = """interface {{ interface }}
ip address {{ ip }} {{ mask }}
no shutdown
{% for v in vlans %}
switchport trunk allowed vlan add {{ v }}
{% endfor %}
exit"""

FAULTS = {   # name -> (broken template, stage where it should fail)
    "loop never closed": (GOOD.replace("{% endfor %}\n", ""), "format"),
    "undefined variable": (GOOD.replace("{{ ip }}", "{{ address }}"), "render"),
    "wrong command": (GOOD.replace("ip address", "ip addr"), "execute"),
    "command outside interface": ("ip address {{ ip }} {{ mask }}\n" + GOOD, "execute"),
    "forgot no shutdown": (GOOD.replace("no shutdown\n", ""), "correct"),
    "only one VLAN": (GOOD.replace("{{ v }}", "10"), "correct"),
}
