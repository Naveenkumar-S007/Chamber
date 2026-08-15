"""Minimal frappe stub so Chamber unit tests run without a bench.

When run inside a bench (real frappe importable) the stub is skipped and the
tests exercise the app against the real framework.
"""
import importlib.util
import json
import sys
import types


def _real_frappe_usable():
	"""True when a working frappe is importable (bench)."""
	try:
		spec = importlib.util.find_spec("frappe")
	except (ValueError, ImportError):
		spec = None
	if spec is None:
		return False
	try:
		import frappe as real

		return hasattr(real, "utils") and hasattr(real.utils, "jinja")
	except Exception:
		return False


def install():
	if getattr(sys.modules.get("frappe"), "_chamber_stub", False):
		return
	if _real_frappe_usable():
		return  # real frappe available (bench) — use it
	# purge any broken/partial frappe left in sys.modules
	for name in [k for k in list(sys.modules) if k == "frappe" or k.startswith("frappe.")]:
		del sys.modules[name]

	import calendar
	import datetime as _dt

	frappe = types.ModuleType("frappe")

	# ---- frappe.utils
	utils = types.ModuleType("frappe.utils")
	jinja_mod = types.ModuleType("frappe.utils.jinja")

	from jinja2 import Environment

	def render_template(template, context):
		env = Environment()
		return env.from_string(template).render(context or {})

	jinja_mod.render_template = render_template

	def getdate(d=None):
		if d is None:
			d = _dt.date.today()
		if isinstance(d, _dt.datetime):
			return d.date()
		if isinstance(d, _dt.date):
			return d
		return _dt.datetime.strptime(str(d)[:10], "%Y-%m-%d").date()

	def today():
		return str(_dt.date.today())

	def now_datetime():
		return _dt.datetime.now()

	def get_datetime(d=None):
		if d is None:
			return _dt.datetime.now()
		if isinstance(d, _dt.datetime):
			return d
		return _dt.datetime.strptime(str(d)[:19], "%Y-%m-%d %H:%M:%S")

	def date_diff(a, b):
		return (getdate(a) - getdate(b)).days

	def add_days(d, n):
		return getdate(d) + _dt.timedelta(days=int(n))

	def add_months(d, n):
		d = getdate(d)
		m = d.month - 1 + int(n)
		y = d.year + m // 12
		m = m % 12 + 1
		day = min(d.day, calendar.monthrange(y, m)[1])
		return _dt.date(y, m, day)

	def add_years(d, n):
		d = getdate(d)
		y = d.year + int(n)
		day = min(d.day, calendar.monthrange(y, d.month)[1])
		return _dt.date(y, d.month, day)

	def cstr(v, encoding="utf-8"):
		return str(v or "")

	utils.cstr = cstr
	utils.getdate = getdate
	utils.today = today
	utils.now_datetime = now_datetime
	utils.get_datetime = get_datetime
	utils.date_diff = date_diff
	utils.add_days = add_days
	utils.add_months = add_months
	utils.add_years = add_years
	utils.jinja = jinja_mod

	# ---- frappe top-level helpers
	frappe.utils = utils
	frappe.log_error = lambda *a, **k: None
	frappe.get_traceback = lambda: ""
	frappe._ = lambda s: s

	def whitelist(fn=None, **kwargs):
		if fn is not None:
			return fn
		return lambda f: f

	frappe.whitelist = whitelist
	frappe.AuthenticationError = type("AuthenticationError", (Exception,), {})
	frappe.throw = lambda msg, exc=None: (_ for _ in ()).throw(exc(msg) if exc else Exception(msg))
	frappe.scrub = lambda t: str(t).strip().lower().replace(" ", "_").replace("/", "_")
	frappe.as_json = lambda obj, indent=1: json.dumps(obj, indent=indent, default=str)
	frappe.get_installed_apps = lambda: []
	frappe.db = types.SimpleNamespace(
		get_all=lambda *a, **k: [],
		get_value=lambda *a, **k: None,
		exists=lambda *a, **k: False,
		commit=lambda: None,
		get_single_value=lambda *a, **k: None,
	)
	frappe.get_meta = lambda doctype: types.SimpleNamespace(has_field=lambda f: False)
	frappe.get_doc = lambda *a, **k: None
	frappe.new_doc = lambda *a, **k: None
	frappe.session = types.SimpleNamespace(user="tester@example.com")
	frappe.get_roles = lambda user=None: ["Advocate"]

	# ---- frappe.model.document.Document (minimal) so doctype controllers import
	model_pkg = types.ModuleType("frappe.model")
	model_pkg.__path__ = []
	document_mod = types.ModuleType("frappe.model.document")

	class Document:
		def __init__(self, *args, **kwargs):
			self.flags = types.SimpleNamespace()
			self._previous = None
			for k, v in kwargs.items():
				setattr(self, k, v)

		def get_doc_before_save(self):
			return self._previous

		def save(self, ignore_permissions=False, **kwargs):
			return self

		def get(self, key, default=None):
			return getattr(self, key, default)

		def is_new(self):
			return not hasattr(self, "name") or not self.name

	document_mod.Document = Document
	model_pkg.document = document_mod
	sys.modules["frappe.model"] = model_pkg
	sys.modules["frappe.model.document"] = document_mod

	sys.modules["frappe"] = frappe
	sys.modules["frappe.utils"] = utils
	sys.modules["frappe.utils.jinja"] = jinja_mod

	frappe._chamber_stub = True

	# requests stub when not installed (tests never hit the network)
	try:
		_has_requests = importlib.util.find_spec("requests") is not None
	except (ValueError, ImportError):
		_has_requests = False
	if not _has_requests:
		req = types.ModuleType("requests")

		def _raise(*a, **k):
			raise ConnectionError("no network in unit tests")

		req.get = req.post = _raise
		req.RequestException = ConnectionError
		sys.modules["requests"] = req
