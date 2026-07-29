#!/usr/bin/env python3
"""Build an interactive access graph HTML from BigID ACI JSON exports.

Required inputs (in --data-dir):
  users.json        array from get_aci_users        -> data.users
  groups.json       array from get_aci_groups       -> data.groups
  objects.json      array from get_aci_data_manager -> data
  permissions.json  dict fullyQualifiedName -> permissions array
                    from get_aci_data_manager_permissions -> data.permissions

Optional inputs (skip the file entirely if the environment doesn't expose the data):
  cases.json        flat array of DSPM cases (flattened get_security_cases
                    -> data.policies[].cases[]) -> clickable risk findings
  enrichment.json   dict fullyQualifiedName -> catalog metadata from
                    get_catalog_objects: {"sensitivity": "Restricted",
                    "last_opened": "...", "lastAccessedBy": "...",
                    "modified_date": "..."} -> tag-based sensitivity +
                    activity/staleness overlay
  memberships.json  dict group name/email -> [member names/emails]
                    -> ground-truth user->group membership edges

Output: self-contained HTML (Cytoscape.js) with nodes/edges, risk flags,
grant-path derivation, optional activity overlay, and optional run-over-run diff.
"""
import argparse, hashlib, json, os, sys
from datetime import datetime, timezone

SENSITIVE_PII_THRESHOLD = 100   # fallback when no sensitivity tag available
SENSITIVE_TAG_VALUES = {"restricted", "confidential", "high"}
STALE_DAYS = 90                 # unused-exposure threshold


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def norm_key(name, email):
    return (email or name or "").strip().lower() or (name or "").strip().lower()


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--template", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="BigID Access Graph")
    ap.add_argument("--bigid-url", default="", help="BigID base URL for DSPM case deep links")
    ap.add_argument("--case-url-template", default="{base}/#/actionable-insights/case/{caseId}")
    ap.add_argument("--rollup", type=int, default=3,
                    help="Collapse >=N files sharing a folder + identical ACL into one folder node (0 disables)")
    ap.add_argument("--snapshot-dir", default="",
                    help="Directory for run snapshots; enables 'changes since last run' diff panel")
    args = ap.parse_args()

    d = args.data_dir
    users = load(os.path.join(d, "users.json"), [])
    groups = load(os.path.join(d, "groups.json"), [])
    objects = load(os.path.join(d, "objects.json"), [])
    perms = load(os.path.join(d, "permissions.json"), {})
    cases = load(os.path.join(d, "cases.json"), [])
    enrichment = load(os.path.join(d, "enrichment.json"), {})
    memberships = load(os.path.join(d, "memberships.json"), {})

    def case_url(c):
        if args.bigid_url and c.get("id"):
            return args.case_url_template.format(base=args.bigid_url.rstrip("/"), caseId=c["id"])
        return ""

    cases_by_source = {}
    for c in cases:
        if (c.get("caseStatus") or "open") != "open":
            continue
        cases_by_source.setdefault(c.get("dataSourceName") or "", []).append(c)
    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    for lst in cases_by_source.values():
        lst.sort(key=lambda c: (sev_rank.get(c.get("severityLevel"), 9),
                                -(c.get("numberOfAffectedObjects") or 0)))

    # directory of known identities (for external flag etc.)
    directory = {}
    for u in users:
        entry = {"external": bool(u.get("external")), "dataSource": u.get("dataSource"),
                 "kind": "user", "email": u.get("email"),
                 "name": u.get("name") or u.get("username")}
        for k in (u.get("email"), u.get("username"), u.get("name")):
            if k:
                directory.setdefault(k.strip().lower(), entry)
    for g in groups:
        entry = {"external": bool(g.get("external")), "dataSource": g.get("dataSource"),
                 "kind": "group", "membersCount": g.get("membersCount"),
                 "email": g.get("email"), "name": g.get("name")}
        for k in (g.get("email"), g.get("name")):
            if k:
                directory.setdefault(k.strip().lower(), entry)

    # normalized membership lookup: member key -> set of group keys
    member_of = {}
    for gname, members in (memberships or {}).items():
        gk = (gname or "").strip().lower()
        for m in members or []:
            member_of.setdefault((m or "").strip().lower(), set()).add(gk)

    nodes, edges = {}, {}

    def add_identity(name, email, kind, external=None):
        key = "id::" + norm_key(name, email)
        info = directory.get((email or "").strip().lower()) or directory.get((name or "").strip().lower())
        if external is None:
            external = bool(info and info.get("external"))
        n = nodes.get(key)
        if not n:
            n = {"id": key, "label": name or email or "unknown", "type": kind,
                 "email": email or (info or {}).get("email") or "",
                 "external": external,
                 "dataSource": (info or {}).get("dataSource") or "",
                 "membersCount": (info or {}).get("membersCount"),
                 "degree": 0}
            nodes[key] = n
        n["external"] = n["external"] or external
        return key

    def add_edge(src, dst, access, deriv="direct", via=None):
        ek = src + "->" + dst
        e = edges.get(ek)
        if not e:
            e = {"id": ek, "source": src, "target": dst, "access": set(),
                 "deriv": deriv, "via": set()}
            edges[ek] = e
        e["access"].update(access or [])
        e["via"].update(via or [])
        if deriv == "direct":
            e["deriv"] = "direct"

    def enrich_for(fqn):
        return enrichment.get(fqn) or {}

    def sens_info(fqn, pii):
        """Returns (sensitive: bool, label: str, basis: 'tag'|'pii')."""
        label = (enrich_for(fqn).get("sensitivity") or "").strip()
        if label:
            return label.lower() in SENSITIVE_TAG_VALUES, label, "tag"
        return pii >= SENSITIVE_PII_THRESHOLD, "", "pii"

    def activity_for(fqn):
        e = enrich_for(fqn)
        last = e.get("last_opened") or e.get("lastAccessed") or ""
        by = e.get("lastAccessedBy") or ""
        dt = parse_dt(last)
        stale = None
        if dt:
            stale = (datetime.now(timezone.utc) - dt).days
        return last, by, stale

    def perm_entries(fqn, ann):
        plist = perms.get(fqn) or []
        if plist:
            return plist, True
        return [{"name": g.split(",")[0], "email": None, "type": "group",
                 "access": ["SHARED"], "grantType": "EFFECTIVE"}
                for g in (ann.get("sharedWithGroup") or [])], False

    def acl_signature(plist):
        return tuple(sorted((p.get("name") or "", p.get("type") or "",
                             tuple(sorted(p.get("access") or []))) for p in plist))

    def ancestor_acl(fqn):
        """Nearest ancestor folder of fqn that has permissions fetched.
        Enables Direct-vs-Inherited per the effective-permission model:
        an entry also present on the parent folder ACL is inherited."""
        parts = (fqn or "").split("/")
        for i in range(len(parts) - 1, 0, -1):
            anc = "/".join(parts[:i])
            if anc != fqn and anc in perms:
                return anc, perms[anc]
        return None, []

    def derive(p, group_grants, parent_map, parent_groups, anc_label):
        """Grant path for a user permission entry, in priority order:
        declared grantType > parent-ACL match (inherited) > membership >
        group access-set inference."""
        gt = (p.get("grantType") or "").upper()
        if gt in ("DIRECT", "EXPLICIT"):
            return "direct", []
        if gt in ("INHERITED",):
            return "inherited", [anc_label] if anc_label else []
        if gt in ("GROUP", "INDIRECT"):
            return "via-group", []
        ukey = norm_key(p.get("name"), p.get("email"))
        acc = set(p.get("access") or [])
        # inherited: same identity appears on the parent folder ACL
        if ukey in parent_map and acc and acc <= parent_map[ukey]:
            return "inherited", [anc_label] if anc_label else []
        # group_grants entries are (name, access_set, inherited_on_object). A group
        # whose own grant is inherited from the parent transmits "inherited" to its
        # members (PM model: inherited = direct-or-group on a parent folder).
        def split(matching):
            direct_g = [gn for gn, _, inh in matching if not inh]
            inh_g = [gn for gn, _, inh in matching if inh]
            if direct_g:
                return "via-group", direct_g
            if inh_g:
                return "inherited", inh_g
            return None
        # known membership: group granted on this object, or on the parent
        known = member_of.get(ukey) or set()
        if known:
            m = [(gn, ga, inh) for gn, ga, inh in group_grants
                 if gn and gn.strip().lower() in known]
            r = split(m)
            if r:
                return r
            via = [gn for gn, ga in parent_groups
                   if gn and gn.strip().lower() in known and acc and acc <= ga]
            if via:
                return "inherited", via
            return "direct", []
        # inference: a group with same-or-broader access on this object, else on parent
        m = [(gn, ga, inh) for gn, ga, inh in group_grants if acc and acc <= ga]
        r = split(m)
        if r:
            return r
        via = [gn for gn, ga in parent_groups if acc and acc <= ga]
        if via:
            return "inherited", via
        return "direct", []

    def connect(rkey, plist, fqn):
        anc, anc_plist = ancestor_acl(fqn)
        anc_label = (anc.split("/")[-1] + "/") if anc else ""
        parent_map = {norm_key(p.get("name"), p.get("email")): set(p.get("access") or [])
                      for p in anc_plist}
        parent_groups = [(p.get("name"), set(p.get("access") or []))
                         for p in anc_plist if p.get("type") == "group"]
        def g_inherited(p):
            gk = norm_key(p.get("name"), p.get("email"))
            ga = set(p.get("access") or [])
            return gk in parent_map and bool(ga) and ga <= parent_map[gk]
        group_grants = [(p.get("name"), set(p.get("access") or []), g_inherited(p))
                        for p in plist if p.get("type") == "group"]
        for p in plist:
            t = p.get("type")
            kind = "group" if t == "group" else ("link" if t == "link" else "user")
            ikey = add_identity(p.get("name"), p.get("email"), kind)
            if kind == "user":
                deriv, via = derive(p, group_grants, parent_map, parent_groups, anc_label)
            elif kind == "link":
                deriv, via = "sharing", []
            else:  # group: inherited when the same group grant exists on the parent
                gkey = norm_key(p.get("name"), p.get("email"))
                acc = set(p.get("access") or [])
                if gkey in parent_map and acc and acc <= parent_map[gkey]:
                    deriv, via = "inherited", [anc_label] if anc_label else []
                else:
                    deriv, via = "group-grant", []
            add_edge(ikey, rkey, p.get("access"), deriv, via)

    risks = []

    def add_resource_risks(n, o_source):
        if n.get("openAccess"):
            risks.append({"level": "high" if n.get("sensitive") else "medium",
                          "nodeId": n["id"], "source": o_source, "kind": "open-access",
                          "text": f"Open access: {n['label']}"
                                  + (f" ({n['pii']} PII findings)" if n.get("pii") else "")})
        if (n.get("openAccess") or n.get("sensitive")) and n.get("staleDays") is not None \
                and n["staleDays"] > STALE_DAYS:
            risks.append({"level": "high" if n.get("sensitive") else "medium",
                          "nodeId": n["id"], "source": o_source, "kind": "unused-exposure",
                          "text": f"Unused exposure: {n['label']} is "
                                  f"{'open access' if n.get('openAccess') else 'sensitive'} "
                                  f"but hasn't been opened in {n['staleDays']} days"})

    # ---- resources: rollup pass then node creation ----
    buckets = {}  # (source, parent, acl_sig) -> [(object, plist, from_perms)]
    for o in objects:
        fqn = o.get("fullyQualifiedName") or o.get("_id")
        ann = o.get("annotations") or {}
        plist, from_perms = perm_entries(fqn, ann)
        parent = fqn.rsplit("/", 1)[0] if "/" in fqn else (o.get("source") or "")
        buckets.setdefault((o.get("source") or "", parent, acl_signature(plist)),
                           []).append((o, plist))

    def resource_node(o, plist, rollup_group=None):
        fqn = o.get("fullyQualifiedName") or o.get("_id")
        od = o.get("objectDetails") or {}
        ann = o.get("annotations") or {}
        if rollup_group:
            members = rollup_group
            parent = fqn.rsplit("/", 1)[0]
            sig = hashlib.sha1(("|".join(sorted(
                m[0].get("fullyQualifiedName") or "" for m in members)) or parent
                ).encode()).hexdigest()[:10]
            rkey = "res::folder::" + parent + "::" + sig
            pii = sum((m[0].get("objectDetails") or {}).get("total_pii_count") or 0 for m in members)
            open_access = any(bool((m[0].get("annotations") or {}).get("openAccess")) for m in members)
            sens_results = [sens_info(m[0].get("fullyQualifiedName") or "",
                                      (m[0].get("objectDetails") or {}).get("total_pii_count") or 0)
                            for m in members]
            sensitive = any(s for s, _, _ in sens_results)
            sens_label = next((l for _, l, _ in sens_results if l), "")
            attrs = []
            for m in members:
                for a in ((m[0].get("objectDetails") or {}).get("attribute") or []):
                    if a not in attrs:
                        attrs.append(a)
            acts = [activity_for(m[0].get("fullyQualifiedName") or "") for m in members]
            dated = [a for a in acts if a[2] is not None]
            last, by, stale = min(dated, key=lambda a: a[2]) if dated else ("", "", None)
            label = (parent.split("/")[-1] or parent) + f"/  ({len(members)} files)"
            n = {"id": rkey, "type": "resource", "isFolder": True,
                 "fileCount": len(members),
                 "files": [(m[0].get("shortenedFQN") or "") for m in members][:10],
                 "label": label, "fqn": parent, "source": o.get("source") or "",
                 "pii": pii, "openAccess": open_access, "sensitive": sensitive,
                 "sensLabel": sens_label, "lastOpened": last, "lastAccessedBy": by,
                 "staleDays": stale, "sizeInBytes": None,
                 "attributes": attrs[:12], "objectType": "folder", "degree": 0}
        else:
            rkey = "res::" + fqn
            pii = od.get("total_pii_count") or 0
            sensitive, sens_label, _ = sens_info(fqn, pii)
            last, by, stale = activity_for(fqn)
            n = {"id": rkey, "type": "resource", "isFolder": False,
                 "label": o.get("shortenedFQN") or od.get("objectName") or fqn,
                 "fqn": fqn, "source": o.get("source") or "",
                 "pii": pii, "openAccess": bool(ann.get("openAccess")),
                 "sensitive": sensitive, "sensLabel": sens_label,
                 "lastOpened": last, "lastAccessedBy": by, "staleDays": stale,
                 "sizeInBytes": od.get("sizeInBytes"),
                 "attributes": (od.get("attribute") or [])[:12],
                 "objectType": o.get("objectType") or od.get("type") or "", "degree": 0}
        nodes[rkey] = n
        # inheritance is judged against the ancestor of the node itself:
        # for a folder rollup that's the folder's parent, for a file its folder
        connect(rkey, plist, n["fqn"])
        add_resource_risks(n, o.get("source") or "")

    for (src, parent, sig), members in buckets.items():
        if args.rollup and len(members) >= args.rollup:
            resource_node(members[0][0], members[0][1], rollup_group=members)
        else:
            for o, plist in members:
                resource_node(o, plist)

    # ---- membership edges (ground truth, only when provided) ----
    membership_edges = 0
    if memberships:
        group_nodes = {n["label"].strip().lower(): n["id"] for n in nodes.values()
                       if n["type"] == "group"}
        group_nodes.update({(n.get("email") or "").strip().lower(): n["id"]
                            for n in nodes.values() if n["type"] == "group" and n.get("email")})
        for gname, members in memberships.items():
            gid = group_nodes.get((gname or "").strip().lower())
            if not gid:
                continue
            for m in members or []:
                ikey = add_identity(m, m if "@" in (m or "") else None, "user")
                add_edge(ikey, gid, ["MEMBER"], "member")
                membership_edges += 1

    # ---- degrees + identity-level risks ----
    for e in edges.values():
        e["access"] = sorted(e["access"])
        e["via"] = sorted(e["via"])
        nodes[e["source"]]["degree"] += 1
        nodes[e["target"]]["degree"] += 1
        if e["deriv"] == "member":
            continue
        tgt, srcn = nodes[e["target"]], nodes[e["source"]]
        writey = any(a in ("WRITE", "DELETE") for a in e["access"])
        if writey and tgt.get("sensitive"):
            risks.append({"level": "high", "nodeId": e["target"], "source": tgt.get("source") or "",
                          "kind": "write-on-sensitive",
                          "text": f"{srcn['label']} has {'/'.join(a for a in e['access'] if a in ('WRITE','DELETE'))} on sensitive {tgt['label']}"})
        if srcn.get("external") and writey:
            risks.append({"level": "high", "nodeId": e["source"], "source": tgt.get("source") or "",
                          "kind": "external-write",
                          "text": f"External identity {srcn['label']} has write access to {tgt['label']}"})

    seen, dedup = set(), []
    for r in sorted(risks, key=lambda r: 0 if r["level"] == "high" else 1):
        if r["text"] not in seen:
            seen.add(r["text"])
            dedup.append(r)
    risks = dedup[:40]

    for r in risks:
        related = cases_by_source.get(r.get("source") or "", [])
        if r.get("kind") in ("open-access", "unused-exposure"):
            pref = [c for c in related if "open access" in (c.get("policyName") or "").lower()]
            related = pref + [c for c in related if c not in pref]
        r["cases"] = [{
            "id": c.get("id"), "label": c.get("caseLabel") or c.get("policyName"),
            "severity": c.get("severityLevel"), "affected": c.get("numberOfAffectedObjects"),
            "assignee": c.get("assignee"), "status": c.get("caseStatus"),
            "policy": c.get("policyName"),
            "description": (c.get("policyDescription") or "")[:300],
            "url": case_url(c), "ticketUrl": c.get("ticketUrl") or "",
            "ticketKey": ((c.get("ticketMetadata") or {}).get("key")) or "",
        } for c in related[:3]]

    node_list = list(nodes.values())
    edge_list = list(edges.values())
    stats = {
        "users": sum(1 for n in node_list if n["type"] == "user"),
        "groups": sum(1 for n in node_list if n["type"] == "group"),
        "links": sum(1 for n in node_list if n["type"] == "link"),
        "resources": sum(1 for n in node_list if n["type"] == "resource"),
        "external": sum(1 for n in node_list if n.get("external")),
        "openAccess": sum(1 for n in node_list if n.get("openAccess")),
        "edges": len(edge_list),
        "directGrants": sum(1 for e in edge_list if e["deriv"] == "direct"
                            and nodes[e["source"]]["type"] == "user"),
        "viaGroup": sum(1 for e in edge_list if e["deriv"] == "via-group"),
        "inherited": sum(1 for e in edge_list if e["deriv"] == "inherited"),
        "sharing": sum(1 for e in edge_list if e["deriv"] == "sharing"),
        "memberEdges": membership_edges,
        "stale": sum(1 for n in node_list if (n.get("staleDays") or 0) > STALE_DAYS),
    }

    # ---- run-over-run diff (optional) ----
    changes = None
    if args.snapshot_dir:
        os.makedirs(args.snapshot_dir, exist_ok=True)
        labels = {n["id"]: n["label"] for n in node_list}
        state = {
            "date": datetime.now(timezone.utc).isoformat(),
            "labels": labels,
            "edges": {e["id"]: e["access"] for e in edge_list},
            "openAccess": sorted(n["id"] for n in node_list if n.get("openAccess")),
            "external": sorted(n["id"] for n in node_list
                               if n.get("external") and n["type"] != "resource"),
        }
        snaps = sorted(f for f in os.listdir(args.snapshot_dir) if f.endswith(".json"))
        if snaps:
            prev = load(os.path.join(args.snapshot_dir, snaps[-1]), {})
            plabels = prev.get("labels") or {}
            pedges = prev.get("edges") or {}

            def edge_desc(eid, acc, lbl):
                s, t = eid.split("->", 1)
                return f"{lbl.get(s, s)} → {lbl.get(t, t)} [{'/'.join(acc)}]"
            new_e = [edge_desc(k, v, labels) for k, v in state["edges"].items() if k not in pedges]
            rem_e = [edge_desc(k, v, plabels) for k, v in pedges.items() if k not in state["edges"]]
            new_oa = [labels[i] for i in state["openAccess"] if i not in set(prev.get("openAccess") or [])]
            new_ext = [labels[i] for i in state["external"] if i not in set(prev.get("external") or [])]
            changes = {"prevDate": (prev.get("date") or "")[:10],
                       "newEdges": new_e[:15], "removedEdges": rem_e[:15],
                       "newOpenAccess": new_oa[:15], "newExternal": new_ext[:15],
                       "counts": {"newEdges": len(new_e), "removedEdges": len(rem_e),
                                  "newOpenAccess": len(new_oa), "newExternal": len(new_ext)}}
        fname = "snapshot-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + ".json"
        with open(os.path.join(args.snapshot_dir, fname), "w") as f:
            json.dump(state, f)

    payload = {"title": args.title, "nodes": node_list, "edges": edge_list,
               "risks": risks, "stats": stats, "changes": changes,
               "hasActivity": bool(enrichment) and any(n.get("lastOpened") for n in node_list),
               "hasMembership": membership_edges > 0}

    with open(args.template) as f:
        html = f.read()
    html = html.replace("__TITLE__", args.title)
    html = html.replace("__GRAPH_DATA__", json.dumps(payload))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        f.write(html)

    folders = sum(1 for n in node_list if n.get("isFolder"))
    print(f"Wrote {args.out}")
    print(f"Nodes: {stats['users']} users, {stats['groups']} groups, {stats['links']} links, "
          f"{stats['resources']} resources ({folders} folder rollups) | Edges: {stats['edges']} "
          f"({stats['directGrants']} direct, {stats['viaGroup']} via group, "
          f"{stats['inherited']} inherited, {stats['sharing']} sharing, "
          f"{stats['memberEdges']} membership) | External: {stats['external']} | "
          f"Open access: {stats['openAccess']} | Stale(>90d): {stats['stale']}")
    if not any(("/" in k) and (k not in {o.get("fullyQualifiedName") for o in objects}) for k in perms):
        print("Note: no parent-folder ACLs in permissions.json — inherited-vs-direct uses "
              "declared grantType / membership / group inference only.")
    if not enrichment:
        print("Note: no enrichment.json — sensitivity falls back to PII counts; activity overlay skipped.")
    if not memberships:
        print("Note: no memberships.json — via-group derivation uses access-set inference.")
    if changes:
        c = changes["counts"]
        print(f"Changes since {changes['prevDate']}: +{c['newEdges']} grants, "
              f"-{c['removedEdges']} removed, {c['newOpenAccess']} newly open, "
              f"{c['newExternal']} new external identities")
    if risks:
        print("Top risks:")
        for r in risks[:8]:
            print(f"  [{r['level'].upper()}] {r['text']}")


if __name__ == "__main__":
    main()
