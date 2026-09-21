import argparse,json,sys
from pathlib import Path
from .engine import ForgeEngine
from .dashboard import serve
def main(argv=None):
    ap=argparse.ArgumentParser(prog="forge"); ap.add_argument("--root",default="."); sub=ap.add_subparsers(dest="cmd",required=True)
    for n in ("inventory","health","self-test","build"): sub.add_parser(n)
    mp=sub.add_parser("manifest-propose"); mp.add_argument("instruction"); mp.add_argument("changes_json"); mp.add_argument("--reason",default="")
    im=sub.add_parser("impact"); im.add_argument("changed_paths",nargs="+"); im.add_argument("--manifest-paths",nargs="*",default=[])
    ma=sub.add_parser("manifest-apply"); ma.add_argument("proposal_id"); ma.add_argument("approval_token"); ma.add_argument("--approver",default="local_user")
    x=sub.add_parser("execute"); x.add_argument("--timeout",type=float,default=30.0); x.add_argument("command",nargs=argparse.REMAINDER)
    s=sub.add_parser("serve"); s.add_argument("--host",default="127.0.0.1"); s.add_argument("--port",type=int,default=8765)
    args=ap.parse_args(argv); e=ForgeEngine(Path(args.root))
    if args.cmd=="impact":
        r=e.impact(args.changed_paths,args.manifest_paths); print(json.dumps(r,indent=2)); return 0
    if args.cmd=="manifest-propose":
        changes=json.loads(args.changes_json); r=e.manifest_evolution().propose(args.instruction,changes,reason=args.reason); print(json.dumps(r,indent=2)); return 0
    if args.cmd=="manifest-apply":
        r=e.manifest_evolution().approve_and_apply(args.proposal_id,args.approval_token,args.approver); print(json.dumps(r,indent=2)); return 0
    if args.cmd=="inventory": print(json.dumps(e.inspect(),indent=2)); return 0
    if args.cmd=="build":
        r=e.build(); print(json.dumps(r,indent=2)); return 0 if r["state"]=="PASSED" else 1
    if args.cmd=="execute":
        r=e.execute(args.command,args.timeout); print(json.dumps(r,indent=2)); return 0 if r["state"]=="PASSED" else 1
    if args.cmd=="health": r=e.health(); print(json.dumps(r,indent=2)); return 0 if r["release_ready"] else 2
    if args.cmd=="self-test": ok,c=e.self_test(); print(json.dumps({"result":"PASS" if ok else "FAIL","checks":c},indent=2)); return 0 if ok else 1
    if args.cmd=="serve": serve(args.host,args.port); return 0
if __name__=="__main__": sys.exit(main())
