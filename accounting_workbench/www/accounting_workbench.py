import os
import re

import frappe

no_cache = 1


def _ordered_head_asset_tags(head_inner: str) -> list[str]:
	tags = []
	pos = 0
	s = head_inner
	while pos < len(s):
		rest = s[pos:]
		low = rest.lower()
		li = low.find("<link")
		si = low.find("<script")
		next_positions = [(li, "link"), (si, "script")]
		next_positions = [(i, k) for i, k in next_positions if i >= 0]
		if not next_positions:
			break
		idx_rel, kind = min(next_positions, key=lambda x: x[0])
		idx = pos + idx_rel
		if kind == "link":
			close = s.find(">", idx)
			if close == -1:
				break
			tags.append(s[idx : close + 1].strip())
			pos = close + 1
		else:
			m = re.match(r"<script\b[^>]*>\s*</script>", s[idx:], re.I | re.DOTALL)
			if m:
				tags.append(s[idx : idx + m.end()].strip())
				pos = idx + m.end()
			else:
				pos = idx + 1
	return tags


def get_context(context):
	context.no_cache = 1
	context.title = "Accounting Workbench"

	idx_path = os.path.join(
		frappe.get_app_path("accounting_workbench"),
		"public",
		"workbench",
		"index.html",
	)
	if not os.path.isfile(idx_path):
		context.workbench_head_tags = []
		context.workbench_missing_build = True
		return context

	context.workbench_missing_build = False
	with open(idx_path, encoding="utf-8") as f:
		html = f.read()

	hm = re.search(r"<head[^>]*>([\s\S]*?)</head>", html, flags=re.I)
	head_inner = hm.group(1) if hm else ""

	context.workbench_head_tags = _ordered_head_asset_tags(head_inner)
	return context
