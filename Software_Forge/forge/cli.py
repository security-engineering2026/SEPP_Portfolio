import argparse,json,sys
from pathlib import Path
from .engine import ForgeEngine
def main(argv=None):
    ap=argparse.ArgumentParser(prog="forge"); ap.add_argument("--root",default="."); sub=ap.add_subparsers(dest="cmd",required=True); sub.add_parser("inventory"); sub.add_parser("health"); sub.add_parser("self-test")
    args=ap.parse_args(argv); e=ForgeEngine(Path(args.root))
    if args.cmd=="inventory": print(json.dumps(e.inspect(),indent=2)); return 0
    if args.cmd=="health": r=e.health(); print(json.dumps(r,indent=2)); return 0 if r["release_ready"] else 2
    if args.cmd=="self-test": ok,c=e.self_test(); print(json.dumps({"result":"PASS" if ok else "FAIL","checks":c},indent=2)); return 0 if ok else 1
    return 2
if __name__=="__main__": sys.exit(main())
