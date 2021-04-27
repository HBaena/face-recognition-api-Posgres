# from arlp import ALPR
# from pprint import pprint

# response = ALPR().get_license_plate(open("../placa-00.jpeg", "rb").read())
# for item in response:
#     print(f"Plate, {item['plate']}")
#     print(f"Score, {item['score']}")

import sys
import tqdm
import time
import pandas as pd

B = []
t = pd.DataFrame({'a': range(0, 10000), 'b': range(10000, 20000)})
for _ in tqdm.tqdm(range(10)):
    C = []
    A = time.time()
    for i,r in t.iterrows():
        C.append((r['a'], r['b']))
    B.append({"method": "iterrows", "time": time.time()-A})

    C = []
    A = time.time()
    for ir in t.itertuples():
        C.append((ir[1], ir[2]))
    B.append({"method": "itertuples", "time": time.time()-A})

    C = []
    A = time.time()
    for r in zip(t['a'], t['b']):
        C.append((r[0], r[1]))
    B.append({"method": "zip", "time": time.time()-A})

    C = []
    A = time.time()
    for r in zip(*t.to_dict("list").values()):
        C.append((r[0], r[1]))
    B.append({"method": "zip + to_dict('list')", "time": time.time()-A})

    C = []
    A = time.time()
    for r in t.to_dict("records"):
        C.append((r["a"], r["b"]))
    B.append({"method": "to_dict('records')", "time": time.time()-A})

    A = time.time()
    t.agg(tuple, axis=1).tolist()
    B.append({"method": "agg", "time": time.time()-A})

    A = time.time()
    t.apply(tuple, axis=1).tolist()
    B.append({"method": "apply", "time": time.time()-A})

print(f'Python {sys.version} on {sys.platform}')
print(f"Pandas version {pd.__version__}")
print(
    pd.DataFrame(B).groupby("method").agg(["mean", "std"]).xs("time", axis=1).sort_values("mean")
)