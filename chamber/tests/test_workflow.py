import unittest

from chamber.tests.stubs import install

install()

from chamber.chamber.doctype.generated_document.generated_document import (
	WORKFLOW_STATES,
	WORKFLOW_TRANSITIONS,
	GeneratedDocument,
)


class TestWorkflowShape(unittest.TestCase):
	def test_full_chain_reaches_executed(self):
		# The state machine must allow forward progress all the way to Executed
		state = "Draft"
		seen = {state}
		while True:
			allowed = WORKFLOW_TRANSITIONS.get(state, [])
			# forward moves are the ones that come later in the canonical list
			forward = [s for s in allowed if WORKFLOW_STATES.index(s) > WORKFLOW_STATES.index(state)]
			if not forward:
				break
			state = forward[0]
			seen.add(state)
		self.assertIn("Finalized", seen)
		self.assertIn("Executed", seen)

	def test_no_jumps(self):
		# Every transition may move at most one canonical step forward
		for state, allowed in WORKFLOW_TRANSITIONS.items():
			idx = WORKFLOW_STATES.index(state)
			for target in allowed:
				if WORKFLOW_STATES.index(target) > idx:
					self.assertLessEqual(WORKFLOW_STATES.index(target), idx + 1)


class TestWorkflowTransitions(unittest.TestCase):
	def make_doc(self, workflow_state="Draft", **kwargs):
		doc = GeneratedDocument()
		doc.workflow_state = workflow_state
		doc.status = "Draft"
		doc.requires_lawyer_review = 0
		doc.reviewed_by = ""
		doc.legal_matter = None
		doc.document_template = None
		doc.title = "Test"
		doc.notes = ""
		for k, v in kwargs.items():
			setattr(doc, k, v)
		return doc

	def test_advance_to_next(self):
		doc = self.make_doc("Draft")
		result = doc.advance_workflow()
		self.assertEqual(result["workflow_state"], "Internal Review")

	def test_advance_to_explicit_target(self):
		doc = self.make_doc("Internal Review")
		result = doc.advance_workflow(target="Client Review")
		self.assertEqual(result["workflow_state"], "Client Review")

	def test_invalid_target_raises(self):
		doc = self.make_doc("Draft")
		with self.assertRaises(Exception):
			doc.advance_workflow(target="Executed")  # jump is not allowed

	def test_sensitive_doc_requires_review_before_client_review(self):
		doc = self.make_doc("Internal Review", requires_lawyer_review=1, reviewed_by="")
		doc.workflow_state = "Client Review"
		with self.assertRaises(Exception):
			doc.validate()

	def test_reviewed_sensitive_doc_passes(self):
		doc = self.make_doc("Internal Review", requires_lawyer_review=1, reviewed_by="Adv. A")
		doc.workflow_state = "Client Review"
		doc.validate()  # must not raise

	def test_suggest_clauses_returns_list(self):
		doc = self.make_doc("Draft", legal_matter="MATTER-TEST", document_template="TPL-TEST")
		result = doc.suggest_clauses(query="indemnity")
		self.assertIsInstance(result, list)
		self.assertLessEqual(len(result), 8)


if __name__ == "__main__":
	unittest.main()
