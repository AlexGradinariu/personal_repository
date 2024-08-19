a = "14.19.60.30-SECURED"

function = lambda x: "DRT16" if x.startswith("16") else "DRT15"
print(f"este {function(a)}")

with open("wtc") as f:
    wtc = f.re