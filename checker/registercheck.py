import ast
import sys
from collections import defaultdict


class History(object):
    def __init__(self, pid, status, op, register, msg=""):
        self.pid = int(pid)
        self.status = status
        self.op = op
        self.register = ast.literal_eval(
            register.replace(" ", ",").replace("nil", "None"))
        self.msg = msg
        self.actual = None


histories = []
ryw_violations = []
curr_vals = defaultdict(None)  # {pid: None}}
written_vals = defaultdict(lambda: defaultdict(None))  # {key: {pid: None}}

# Read from history file
with open(sys.argv[1], "r") as f:
    line = f.readline().strip()
    while line:
        # Strip nemesis lines
        if not line.startswith(":nemesis"):
            h = History(*line.split("\t"))
            histories.append(h)
        line = f.readline().strip()

for h in histories:
    if h.status == ":ok":
        # Set latest values in curr_vals for curr pid and update latest
        history_key = h.register[0]
        if h.op == ":read":
            # Have we written to this PID before?
            if h.pid in written_vals[history_key]:
                # Does this read return the latest value written to the process
                if written_vals[history_key][h.pid] != h.register[1] and curr_vals[history_key] != h.register[1]:
                    # Violation, note expected and actual values
                    h.actual = [written_vals[history_key][h.pid], curr_vals[history_key]]
                    ryw_violations.append(h)

        elif h.op == ":write":
            written_vals[history_key][h.pid] = h.register[1]
            curr_vals[history_key] = h.register[1]
        elif h.op == ":cas":
            written_vals[history_key][h.pid] = h.register[1][1]
            curr_vals[history_key] = h.register[1][1]
        else:
            print "ERROR, BAD OP " + h.op

print "Final state of CAS register:"
for i in curr_vals:
    print "k:", i, " v:", written_vals[i].get('latest', 'NIL')

print
print "There were", len(ryw_violations), "violation(s):"
for i in ryw_violations:
    print "line:", histories.index(i), "PID:", i.pid, "read", i.register[1], "when it should've read", i.actual
